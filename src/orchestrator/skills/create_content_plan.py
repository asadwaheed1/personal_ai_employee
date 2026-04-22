#!/usr/bin/env python3
"""
Agent Skill: Create Content Plan
Generates a weekly content calendar for LinkedIn posting

This skill creates a structured content plan based on:
- Business goals from Company_Handbook.md or Business_Goals.md
- Previous successful posts
- Industry best practices
- Optimal posting times
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
try:
    from .base_skill import BaseSkill, run_skill
except ImportError:
    from base_skill import BaseSkill, run_skill


class CreateContentPlanSkill(BaseSkill):
    """Skill to create weekly content calendar for social media"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create content plan"""
        week_start = params.get('week_start')
        num_posts = params.get('num_posts', 5)
        platforms = params.get('platforms', ['linkedin'])

        # Determine week start
        if week_start:
            start_date = datetime.fromisoformat(week_start)
        else:
            # Next Monday
            today = datetime.now()
            start_date = today + timedelta(days=(7 - today.weekday()) % 7)
            start_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0)

        # Load business context
        business_context = self._load_business_context()

        # Generate content calendar
        calendar = self._generate_calendar(start_date, num_posts, platforms, business_context)

        # Save calendar
        calendar_path = self._save_calendar(calendar, start_date)

        # Update dashboard
        self._update_dashboard(calendar, start_date)

        return {
            "success": True,
            "calendar_file": str(calendar_path),
            "week_start": start_date.strftime("%Y-%m-%d"),
            "num_posts": len(calendar['posts']),
            "platforms": platforms,
            "message": f"Created content calendar with {len(calendar['posts'])} posts for week of {start_date.strftime('%B %d')}"
        }

    def _load_business_context(self) -> Dict[str, Any]:
        """Load business context from vault files"""
        context = {
            'business_name': 'Your Business',
            'industry': 'Technology',
            'target_audience': 'Professionals',
            'key_messages': [],
            'recent_activities': []
        }

        # Try to load from Business_Goals.md
        goals_path = self.vault_path / 'Business_Goals.md'
        if goals_path.exists():
            try:
                content = self.read_file(goals_path)
                # Extract objectives
                if 'Objectives' in content:
                    objectives = self._extract_section(content, 'Objectives')
                    context['key_messages'] = [line.strip('- ') for line in objectives.split('\n') if line.strip().startswith('-')][:5]

                # Extract industry info
                if 'Industry' in content:
                    industry_line = [l for l in content.split('\n') if 'Industry' in l]
                    if industry_line:
                        context['industry'] = industry_line[0].split(':')[-1].strip()
            except Exception as e:
                self.logger.warning(f"Could not parse Business_Goals.md: {e}")

        # Load from Company_Handbook.md
        handbook_path = self.vault_path / 'Company_Handbook.md'
        if handbook_path.exists():
            try:
                content = self.read_file(handbook_path)
                # Extract tone/voice guidelines
                if 'Tone' in content or 'Voice' in content:
                    tone_section = self._extract_section(content, 'Tone')
                    context['tone'] = tone_section[:500] if tone_section else 'Professional'
            except:
                pass

        # Load recent completed tasks from Done folder
        done_path = self.vault_path / 'Done'
        if done_path.exists():
            recent_files = sorted(done_path.glob('*.md'), key=lambda x: x.stat().st_mtime, reverse=True)[:10]
            for f in recent_files:
                try:
                    content = self.read_file(f)
                    if len(context['recent_activities']) < 5:
                        context['recent_activities'].append({
                            'title': f.stem,
                            'preview': content[:200] + '...' if len(content) > 200 else content
                        })
                except:
                    pass

        return context

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from markdown content"""
        lines = content.split('\n')
        in_section = False
        section_lines = []

        for line in lines:
            if line.startswith(f'## {section_name}') or line.startswith(f'### {section_name}'):
                in_section = True
                continue
            if in_section:
                if line.startswith('#'):
                    break
                section_lines.append(line)

        return '\n'.join(section_lines).strip()

    def _generate_calendar(self, start_date: datetime, num_posts: int,
                            platforms: List[str], context: Dict) -> Dict[str, Any]:
        """Generate content calendar"""
        posts = []

        # Content themes for the week
        themes = [
            {
                'type': 'thought_leadership',
                'title': 'Industry Insights',
                'focus': f'Share insights about {context.get("industry", "your industry")} trends'
            },
            {
                'type': 'case_study',
                'title': 'Success Story',
                'focus': 'Highlight a recent win or client success'
            },
            {
                'type': 'engagement',
                'title': 'Community Question',
                'focus': 'Ask your network for their opinions'
            },
            {
                'type': 'behind_scenes',
                'title': 'Behind the Scenes',
                'focus': 'Share how your business operates'
            },
            {
                'type': 'value_proposition',
                'title': 'Value Spotlight',
                'focus': 'Showcase your unique value proposition'
            }
        ]

        # Optimal posting times (based on LinkedIn best practices)
        optimal_times = [
            (12, 0),  # 12 PM - Lunch break
            (12, 0),  # 12 PM - Lunch break
            (17, 0),  # 5 PM - End of workday
            (19, 0),  # 7 PM - Evening browsing
        ]

        # Generate posts for each weekday
        weekdays = [0, 1, 2, 3, 4]  # Monday to Friday

        for i in range(min(num_posts, 5)):
            day_offset = weekdays[i]
            post_date = start_date + timedelta(days=day_offset)

            # Pick optimal time
            hour, minute = optimal_times[i % len(optimal_times)]
            post_time = post_date.replace(hour=hour, minute=minute)

            # Select theme
            theme = themes[i % len(themes)]

            # Generate post content
            content = self._generate_post_content(theme, context)

            post = {
                'id': f"POST_{post_time.strftime('%Y%m%d_%H%M')}",
                'scheduled_for': post_time.isoformat(),
                'platform': 'linkedin',
                'type': theme['type'],
                'title': theme['title'],
                'content': content,
                'hashtags': self._generate_hashtags(context),
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'optimal_engagement_time': f"{hour}:00 - {hour + 2}:00"
            }

            posts.append(post)

        return {
            'week_start': start_date.strftime('%Y-%m-%d'),
            'week_end': (start_date + timedelta(days=6)).strftime('%Y-%m-%d'),
            'num_posts': len(posts),
            'platforms': platforms,
            'business_context': {
                'industry': context.get('industry'),
                'tone': context.get('tone', 'Professional')
            },
            'posts': posts
        }

    def _generate_post_content(self, theme: Dict, context: Dict) -> str:
        """Generate post content based on theme and context"""
        content_templates = {
            'thought_leadership': f"""What I've learned about {context.get('industry', 'our industry')} this week:

The landscape is shifting faster than ever. Here are 3 observations that stood out:

1. Innovation is happening at the intersection of disciplines
2. Collaboration beats competition in the long run
3. Adaptability is the new stability

What's your take on these trends? I'd love to hear your perspective in the comments.

#ThoughtLeadership #Innovation #{context.get('industry', 'Business').replace(' ', '')}""",

            'case_study': f"""Success story from this week 🎉

A client came to us with a challenge that seemed impossible at first. Through collaboration and persistence, we delivered results that exceeded expectations.

The key lessons:
✅ Clear communication from day one
✅ Iterative approach beats big bang
✅ Celebrate small wins along the way

Every project teaches us something new.

#ClientSuccess #Results #Partnership""",

            'engagement': f"""Quick question for my network:

What's the biggest challenge you're facing in {context.get('industry', 'your work')} right now?

I'm curious to hear your thoughts and maybe we can crowdsource some solutions together.

Drop your answer below 👇

#Question #Community #Discussion""",

            'behind_scenes': f"""Behind the scenes at {context.get('business_name', 'our company')} 👀

Here's something you might not know about how we work:

We believe the best ideas come from diverse perspectives. That's why we make time for creative exploration every week.

The result? Better solutions for our clients and a team that genuinely loves what they do.

What does your creative process look like?

#BehindTheScenes #Culture #Innovation""",

            'value_proposition': f"""The difference between good and great isn't talent—it's consistency.

At {context.get('business_name', 'our company')}, we show up every day committed to:

🎯 Delivering exceptional results
🤝 Building genuine relationships
📈 Creating long-term value

It's not always easy, but it's always worth it.

What's your philosophy on consistency?

#Values #Excellence #{context.get('industry', 'Business').replace(' ', '')}"""
        }

        return content_templates.get(theme['type'], content_templates['thought_leadership'])

    def _generate_hashtags(self, context: Dict) -> List[str]:
        """Generate relevant hashtags"""
        industry = context.get('industry', 'Business')
        base_tags = ['#LinkedIn', '#Professional', '#Business']

        industry_tags = {
            'Technology': ['#Tech', '#Innovation', '#Digital'],
            'Marketing': ['#Marketing', '#Growth', '#Strategy'],
            'Finance': ['#Finance', '#Investment', '#Money'],
            'Healthcare': ['#Healthcare', '#Wellness', '#Medical'],
            'Education': ['#Education', '#Learning', '#Training'],
            'Consulting': ['#Consulting', '#Advisory', '#Expertise']
        }

        specific_tags = industry_tags.get(industry, ['#Industry', '#Leadership'])
        return base_tags + specific_tags

    def _save_calendar(self, calendar: Dict, start_date: datetime) -> Path:
        """Save calendar to file"""
        calendar_dir = self.vault_path / 'Content_Calendar'
        calendar_dir.mkdir(exist_ok=True)

        # Save weekly calendar as JSON
        week_str = start_date.strftime('%Y-W%U')
        calendar_file = calendar_dir / f"CALENDAR_{week_str}.json"
        calendar_file.write_text(json.dumps(calendar, indent=2), encoding='utf-8')

        # Also save as markdown for easy viewing
        md_file = calendar_dir / f"CALENDAR_{week_str}.md"
        md_content = self._calendar_to_markdown(calendar)
        md_file.write_text(md_content, encoding='utf-8')

        self.logger.info(f"Saved content calendar to {calendar_file}")

        return calendar_file

    def _calendar_to_markdown(self, calendar: Dict) -> str:
        """Convert calendar to markdown format"""
        content = f"""---
type: content_calendar
week_start: {calendar['week_start']}
week_end: {calendar['week_end']}
num_posts: {calendar['num_posts']}
created: {datetime.now().isoformat()}
---

# Content Calendar: Week of {calendar['week_start']}

## Overview
- **Posts Scheduled**: {calendar['num_posts']}
- **Platforms**: {', '.join(calendar['platforms'])}
- **Industry Focus**: {calendar['business_context']['industry']}
- **Tone**: {calendar['business_context']['tone']}

## Posts Schedule

"""

        for i, post in enumerate(calendar['posts'], 1):
            content += f"""### Post {i}: {post['title']}
**Scheduled**: {post['scheduled_for']}
**Type**: {post['type']}
**Best Engagement Window**: {post['optimal_engagement_time']}

**Content**:
```
{post['content']}
```

**Hashtags**: {' '.join(post['hashtags'])}

**Status**: {post['status']}

---

"""

        content += f"""## Content Strategy Notes

### Posting Guidelines
- Post consistently during optimal engagement hours
- Respond to comments within 2 hours
- Use 3-5 relevant hashtags per post
- Include a clear call-to-action
- Share genuine insights, not just promotions

### This Week's Themes
1. **Thought Leadership** - Establish expertise
2. **Case Studies** - Showcase results
3. **Engagement** - Build community
4. **Behind the Scenes** - Humanize the brand
5. **Values** - Reinforce brand message

### Approval Process
Each post will be automatically submitted for approval 24 hours before the scheduled time.
Review the post in /Pending_Approval/ and move to /Approved/ to confirm.

---
*Generated by CreateContentPlan skill*
*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

        return content

    def _update_dashboard(self, calendar: Dict, start_date: datetime):
        """Update dashboard with calendar creation"""
        dashboard_path = self.vault_path / 'Dashboard.md'
        if not dashboard_path.exists():
            return

        content = self.read_file(dashboard_path)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Add activity
        activity = f"Created content calendar with {calendar['num_posts']} posts for week of {start_date.strftime('%b %d')}"

        if "## Recent Activity" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("## Recent Activity"):
                    lines.insert(i + 1, f"- [{timestamp}] {activity}")
                    break
            content = '\n'.join(lines)
        else:
            content += f"\n## Recent Activity\n- [{timestamp}] {activity}\n"

        # Update content calendar section
        calendar_info = f"""
## Content Schedule
**Week of {start_date.strftime('%B %d')}: {calendar['num_posts']} posts scheduled**
Next post: {calendar['posts'][0]['scheduled_for'] if calendar['posts'] else 'None'}
"""

        if "## Content Schedule" in content:
            # Replace existing section
            import re
            content = re.sub(
                r'## Content Schedule.*?\n(?=## |$)',
                calendar_info + '\n',
                content,
                flags=re.DOTALL
            )
        else:
            content += calendar_info

        self.write_file(dashboard_path, content)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_content_plan.py '<json_params>'")
        print("\nExamples:")
        print('  Weekly plan: python create_content_plan.py \'{"num_posts": 5}\'')
        print('  Specific week: python create_content_plan.py \'{"week_start": "2026-04-07", "num_posts": 7}\'')
        sys.exit(1)

    run_skill(CreateContentPlanSkill, sys.argv[1])
