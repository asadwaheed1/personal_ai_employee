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
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
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
        platforms = params.get('platforms', ['linkedin', 'facebook', 'instagram'])

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

            # Generate platform-specific content via Claude API
            platform_content = self._generate_post_content_ai(
                theme, context, platforms, post_time.strftime('%Y-%m-%d')
            )

            for platform in platforms:
                pc = platform_content.get(platform, {})
                content = pc.get('content', '')
                post = {
                    'id': f"POST_{platform.upper()}_{post_time.strftime('%Y%m%d_%H%M')}",
                    'scheduled_for': post_time.isoformat(),
                    'platform': platform,
                    'type': theme['type'],
                    'title': theme['title'],
                    'content': content,
                    'hashtags': self._generate_hashtags(context, platform),
                    'status': 'scheduled',
                    'created_at': datetime.now().isoformat(),
                    'optimal_engagement_time': f"{hour}:00 - {hour + 2}:00"
                }

                if platform in ('facebook', 'instagram', 'linkedin'):
                    post['image_prompt'] = pc.get('image_prompt', '')

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

    def _generate_post_content_ai(
        self,
        theme: Dict,
        context: Dict,
        platforms: List[str],
        week_date: str,
    ) -> Dict[str, Any]:
        """Call Claude API to generate unique platform-specific content for a theme."""
        platform_tone = {
            'linkedin': (
                'Write as an individual software developer sharing personal insights — first person singular (I, my, I\'ve). '
                'Do NOT mention any company name or use "we/our". '
                'Professional, thought-leadership tone. Structured points or numbered lists. '
                'End with a question to spark discussion. No excessive emojis. 150-300 words.'
            ),
            'twitter': (
                'Punchy, direct, conversational. Max 270 characters including hashtags. '
                '1-2 hashtags only. No fluff.'
            ),
            'facebook': (
                'Warm, friendly, casual tone. Use 2-3 emojis naturally. '
                'Relatable story or hook. Encourage comments and shares. 80-150 words.'
            ),
            'instagram': (
                'Visual storytelling, lifestyle-oriented, casual and upbeat. '
                'Strong hook in first line. Emojis. 60-120 words for caption. '
                'Suggest a compelling image to accompany this post.'
            ),
        }

        platform_blocks = '\n'.join(
            f'- {p}: {platform_tone.get(p, "Professional tone.")}'
            for p in platforms
        )

        prompt = f"""You are a social media content writer for a {context.get('industry', 'Technology')} brand.

Week of: {week_date}
Post theme: {theme['title']} ({theme['type']})
Theme focus: {theme['focus']}

Generate UNIQUE, FRESH content for each platform below. Content must be different each week — do not use generic filler.

Platform tone requirements:
{platform_blocks}

For LinkedIn, Facebook, and Instagram posts, add an image_prompt field (1 sentence describing a compelling visual to pair with the post).

Return ONLY valid JSON in this exact format:
{{
  "linkedin": {{"content": "...", "image_prompt": "..."}},
  "facebook": {{"content": "...", "image_prompt": "..."}},
  "instagram": {{"content": "...", "image_prompt": "..."}}
}}

Include only the platforms listed. No markdown fences around JSON."""

        try:
            from google import genai
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not set")
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=prompt,
            )
            raw = response.text.strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            result = json.loads(raw)
            self.logger.info(f"Gemini generated content for theme '{theme['type']}'")
            return result
        except Exception as e:
            self.logger.warning(f"Gemini content generation failed ({e}), using fallback templates")
            return self._fallback_content(theme, context, platforms)

    def _fallback_content(self, theme: Dict, context: Dict, platforms: List[str]) -> Dict[str, Any]:
        """Static fallback content when Claude API unavailable."""
        biz = context.get('business_name', 'our company')
        ind = context.get('industry', 'Technology')
        base = {
            'thought_leadership': f"This week in {ind}: three things that stood out to us.\n\n1. Speed of change is accelerating\n2. Collaboration unlocks better outcomes\n3. Simplicity wins every time\n\nWhat trends are you watching? #ThoughtLeadership #{ind.replace(' ', '')}",
            'case_study': f"A challenge became a win this week at {biz}.\n\nThe lesson: clear scope + fast feedback loops = results that exceed expectations. #ClientSuccess",
            'engagement': f"Quick question: what's the hardest part of working in {ind} right now?\n\nDrop your answer below 👇 #Community",
            'behind_scenes': f"Behind the scenes at {biz}: great ideas come from diverse perspectives. We carve out time each week for creative thinking. #BehindTheScenes",
            'value_proposition': f"Consistency over brilliance. At {biz} we show up every day committed to delivering real value. #Values #{ind.replace(' ', '')}",
        }
        text = base.get(theme['type'], base['thought_leadership'])
        result = {}
        for p in platforms:
            entry: Dict[str, Any] = {'content': text[:270] if p == 'twitter' else text}
            if p in ('facebook', 'instagram', 'linkedin'):
                entry['image_prompt'] = f"Professional {ind} team working collaboratively in a modern office."
            result[p] = entry
        return result

    def _generate_hashtags(self, context: Dict, platform: str = 'linkedin') -> List[str]:
        """Generate platform-appropriate hashtags."""
        industry = context.get('industry', 'Business')
        industry_tags = {
            'Technology': ['#Tech', '#Innovation', '#Digital'],
            'Marketing': ['#Marketing', '#Growth', '#Strategy'],
            'Finance': ['#Finance', '#Investment', '#Money'],
            'Healthcare': ['#Healthcare', '#Wellness', '#Medical'],
            'Education': ['#Education', '#Learning', '#Training'],
            'Consulting': ['#Consulting', '#Advisory', '#Expertise'],
        }
        specific = industry_tags.get(industry, ['#Industry', '#Leadership'])
        if platform == 'linkedin':
            return ['#LinkedIn', '#Professional', '#Business'] + specific
        elif platform == 'twitter':
            return specific[:2]
        elif platform == 'instagram':
            return ['#instagood', '#business'] + specific + ['#lifestyle', '#motivation']
        else:  # facebook
            return ['#Business'] + specific

    def _save_calendar(self, calendar: Dict, start_date: datetime) -> Path:
        """Save calendar and individual post files to Content_Calendar"""
        calendar_dir = self.vault_path / 'Content_Calendar'
        calendar_dir.mkdir(exist_ok=True)

        # 1. Save individual post files for watchers
        for post in calendar['posts']:
            platform = post['platform']
            dt = datetime.fromisoformat(post['scheduled_for'])
            filename = f"{platform.upper()}_POST_{dt.strftime('%Y%m%d_%H%M%S')}.json"
            
            # Map simplified post data for specific skills
            post_file_data = {
                'type': f"{platform}_post",
                'content': post['content'],
                'scheduled_for': post['scheduled_for'],
                'created_at': post['created_at'],
                'status': 'scheduled',
                'hashtags': post['hashtags']
            }

            if platform in ('facebook', 'instagram', 'linkedin') and post.get('image_prompt'):
                post_file_data['image_prompt'] = post['image_prompt']
            
            (calendar_dir / filename).write_text(json.dumps(post_file_data, indent=2), encoding='utf-8')

        # 2. Save weekly calendar as JSON
        week_str = start_date.strftime('%Y-W%U')
        calendar_file = calendar_dir / f"CALENDAR_{week_str}.json"
        calendar_file.write_text(json.dumps(calendar, indent=2), encoding='utf-8')

        # 3. Also save as markdown for easy viewing
        md_file = calendar_dir / f"CALENDAR_{week_str}.md"
        md_content = self._calendar_to_markdown(calendar)
        md_file.write_text(md_content, encoding='utf-8')

        self.logger.info(f"Saved content calendar and {len(calendar['posts'])} post files to {calendar_dir}")

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
