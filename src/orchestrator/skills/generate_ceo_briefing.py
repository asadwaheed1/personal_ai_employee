#!/usr/bin/env python3
"""
Agent Skill: Generate CEO Weekly Briefing
Reads vault state for the past 7 days and writes Briefings/YYYY-MM-DD_Monday_Briefing.md
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


class GenerateCEOBriefingSkill(BaseSkill):
    """Generates a weekly executive briefing from vault activity"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target_date = params.get("date")
        if target_date:
            briefing_date = datetime.strptime(target_date, "%Y-%m-%d")
        else:
            briefing_date = datetime.now()

        cutoff = briefing_date - timedelta(days=7)

        done_stats = self._scan_done(cutoff)
        audit_stats = self._scan_audit_logs(cutoff)
        calendar_stats = self._scan_content_calendar()
        pending_stats = self._count_pending()
        anomalies = self._detect_anomalies(done_stats, audit_stats, pending_stats)

        briefing = self._render_briefing(
            briefing_date, cutoff, done_stats, audit_stats,
            calendar_stats, pending_stats, anomalies
        )

        briefings_dir = self.vault_path / "Briefings"
        briefings_dir.mkdir(exist_ok=True)
        filename = briefing_date.strftime("%Y-%m-%d_Monday_Briefing.md")
        output_path = briefings_dir / filename
        self.write_file(output_path, briefing)

        self.logger.info(f"CEO briefing written to {output_path}")
        return {
            "briefing_path": str(output_path),
            "period_start": cutoff.strftime("%Y-%m-%d"),
            "period_end": briefing_date.strftime("%Y-%m-%d"),
            "done_tasks": done_stats["total"],
            "pending_items": pending_stats["total"],
        }

    # -------------------------------------------------------------------------
    # Data collection
    # -------------------------------------------------------------------------

    def _scan_done(self, cutoff: datetime) -> Dict[str, Any]:
        done_dir = self.vault_path / "Done"
        stats: Dict[str, Any] = {
            "total": 0,
            "auto_email": 0,
            "approved_email": 0,
            "linkedin_post": 0,
            "mcp_action": 0,
            "other": 0,
            "files": [],
        }
        if not done_dir.exists():
            return stats

        for f in done_dir.rglob("*.md"):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
            except OSError:
                continue
            if mtime < cutoff:
                continue

            stats["total"] += 1
            name = f.name
            if name.startswith("AUTO_PROCESSED_EMAIL_"):
                stats["auto_email"] += 1
            elif name.startswith("PROCESSED_EMAIL_") or name.startswith("EMAIL_"):
                stats["approved_email"] += 1
            elif name.startswith("LINKEDIN_") or name.startswith("POST_"):
                stats["linkedin_post"] += 1
            elif name.startswith("MCP_"):
                stats["mcp_action"] += 1
            else:
                stats["other"] += 1
            stats["files"].append(name)

        return stats

    def _scan_audit_logs(self, cutoff: datetime) -> Dict[str, Any]:
        logs_dir = self.vault_path / "Logs"
        stats: Dict[str, Any] = {
            "total_actions": 0,
            "email_actions": 0,
            "linkedin_actions": 0,
            "mcp_actions": 0,
            "errors": 0,
        }
        if not logs_dir.exists():
            return stats

        for f in logs_dir.glob("audit_*.json"):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if mtime < cutoff:
                    continue
                entries = json.loads(f.read_text(encoding="utf-8"))
                if not isinstance(entries, list):
                    entries = [entries]
                for entry in entries:
                    stats["total_actions"] += 1
                    action_type = str(entry.get("type", "")).lower()
                    platform = str(entry.get("platform", "")).lower()
                    if "email" in action_type or "email" in platform:
                        stats["email_actions"] += 1
                    elif "linkedin" in action_type or "linkedin" in platform:
                        stats["linkedin_actions"] += 1
                    elif "mcp" in action_type:
                        stats["mcp_actions"] += 1
                    result = entry.get("result", {})
                    if isinstance(result, dict) and result.get("status") == "error":
                        stats["errors"] += 1
            except Exception as e:
                self.logger.warning(f"Could not parse audit log {f.name}: {e}")

        return stats

    def _scan_content_calendar(self) -> Dict[str, Any]:
        cal_dir = self.vault_path / "Content_Calendar"
        stats: Dict[str, Any] = {
            "total_posts": 0,
            "published": 0,
            "scheduled": 0,
            "pending_approval": 0,
            "weeks": [],
        }
        if not cal_dir.exists():
            return stats

        for f in cal_dir.glob("CALENDAR_*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                posts = data.get("posts", [])
                stats["weeks"].append(data.get("week_start", f.stem))
                for post in posts:
                    stats["total_posts"] += 1
                    status = post.get("status", "").lower()
                    if status == "published":
                        stats["published"] += 1
                    elif status == "scheduled":
                        stats["scheduled"] += 1
                    elif "pending" in status or "approval" in status:
                        stats["pending_approval"] += 1
            except Exception as e:
                self.logger.warning(f"Could not parse calendar {f.name}: {e}")

        return stats

    def _count_pending(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {"total": 0, "needs_action": 0, "pending_approval": 0}

        na = self.vault_path / "Needs_Action"
        if na.exists():
            count = sum(1 for f in na.iterdir() if f.suffix in (".md", ".json"))
            stats["needs_action"] = count
            stats["total"] += count

        pa = self.vault_path / "Pending_Approval"
        if pa.exists():
            count = sum(1 for f in pa.iterdir() if f.suffix in (".md", ".json"))
            stats["pending_approval"] = count
            stats["total"] += count

        return stats

    def _detect_anomalies(
        self,
        done: Dict[str, Any],
        audit: Dict[str, Any],
        pending: Dict[str, Any],
    ) -> List[str]:
        anomalies = []
        if pending["needs_action"] > 20:
            anomalies.append(
                f"High backlog: {pending['needs_action']} items in Needs_Action (threshold: 20)"
            )
        if pending["pending_approval"] > 5:
            anomalies.append(
                f"Approval queue backed up: {pending['pending_approval']} items awaiting human review"
            )
        if audit["errors"] > 0:
            anomalies.append(f"{audit['errors']} action error(s) recorded in audit logs this week")
        if done["total"] == 0:
            anomalies.append("No tasks completed this week — system may be stalled or idle")
        return anomalies

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def _render_briefing(
        self,
        briefing_date: datetime,
        cutoff: datetime,
        done: Dict[str, Any],
        audit: Dict[str, Any],
        calendar: Dict[str, Any],
        pending: Dict[str, Any],
        anomalies: List[str],
    ) -> str:
        period = f"{cutoff.strftime('%Y-%m-%d')} → {briefing_date.strftime('%Y-%m-%d')}"
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

        anomaly_section = (
            "\n".join(f"- ⚠️ {a}" for a in anomalies)
            if anomalies
            else "- ✅ No anomalies detected"
        )

        calendar_weeks = ", ".join(calendar["weeks"]) if calendar["weeks"] else "none"

        return f"""# CEO Weekly Briefing — {briefing_date.strftime('%B %d, %Y')}

**Generated:** {generated_at}
**Period:** {period}
**Prepared by:** AI Employee (automated)

---

## Executive Summary

| Metric | Value |
|---|---|
| Tasks completed (7 days) | {done['total']} |
| Items pending review | {pending['total']} |
| Audit log actions | {audit['total_actions']} |
| Content posts scheduled | {calendar['scheduled']} |
| Content posts published | {calendar['published']} |
| Anomalies detected | {len(anomalies)} |

---

## Email Activity

| Category | Count |
|---|---|
| Auto-processed (low priority) | {done['auto_email']} |
| Human-approved + executed | {done['approved_email']} |
| MCP email actions executed | {audit['email_actions']} |
| Currently in Needs_Action | {pending['needs_action']} |
| Awaiting human approval | {pending['pending_approval']} |

---

## LinkedIn Activity

| Category | Count |
|---|---|
| Posts published this week | {done['linkedin_post']} |
| Audit-logged LinkedIn actions | {audit['linkedin_actions']} |
| Posts scheduled (all calendars) | {calendar['scheduled']} |
| Posts published (all calendars) | {calendar['published']} |
| Posts pending approval | {calendar['pending_approval']} |
| Calendar weeks loaded | {calendar_weeks} |

---

## Completed Tasks (7 days)

| Category | Count |
|---|---|
| Auto-processed emails | {done['auto_email']} |
| Approved emails | {done['approved_email']} |
| LinkedIn posts | {done['linkedin_post']} |
| MCP actions | {done['mcp_action']} |
| Other | {done['other']} |
| **Total** | **{done['total']}** |

---

## Pending Items

| Queue | Count |
|---|---|
| Needs_Action | {pending['needs_action']} |
| Pending_Approval | {pending['pending_approval']} |
| **Total** | **{pending['total']}** |

---

## Anomalies & Alerts

{anomaly_section}

---

## Next Week Preparation

- [ ] Review {pending['pending_approval']} item(s) in Pending_Approval
- [ ] Clear {pending['needs_action']} item(s) in Needs_Action backlog
- [ ] Verify content calendar covers next 7 days across all platforms
- [ ] Check LinkedIn OAuth token expiry (refresh if needed)
- [ ] Review Gmail MCP authentication health

---

*Briefing auto-generated by `generate_ceo_briefing.py`. Edit Company_Handbook.md to adjust thresholds.*
"""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: generate_ceo_briefing.py '<json_params>'"}, indent=2))
        sys.exit(1)
    run_skill(GenerateCEOBriefingSkill, sys.argv[1])
