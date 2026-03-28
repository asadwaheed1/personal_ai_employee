#!/usr/bin/env python3
"""
Agent Skill: Parse Watcher File
Extracts information from watcher-generated files
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from base_skill import BaseSkill, run_skill


class ParseWatcherFileSkill(BaseSkill):
    """Skill to parse watcher-generated files and extract information"""

    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a watcher file and extract information"""
        file_path = Path(params.get('file_path'))
        file_type = params.get('file_type', 'auto')

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        content = self.read_file(file_path)

        # Auto-detect file type if not specified
        if file_type == 'auto':
            file_type = self._detect_file_type(file_path, content)

        # Parse based on file type
        if file_type == 'email':
            parsed_data = self._parse_email_file(content)
        elif file_type == 'file_drop':
            parsed_data = self._parse_file_drop(content)
        elif file_type == 'system_event':
            parsed_data = self._parse_system_event(content)
        elif file_type == 'manual':
            parsed_data = self._parse_manual_file(content)
        else:
            parsed_data = self._parse_generic_file(content)

        # Add common metadata
        parsed_data.update({
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_type": file_type,
            "parsed_at": datetime.now().isoformat(),
            "file_size": file_path.stat().st_size
        })

        self.logger.info(f"Parsed {file_type} file: {file_path.name}")

        return parsed_data

    def _detect_file_type(self, file_path: Path, content: str) -> str:
        """Auto-detect file type based on name and content"""
        name_lower = file_path.name.lower()

        # Check filename patterns
        if 'email' in name_lower or 'gmail' in name_lower:
            return 'email'
        elif 'file_drop' in name_lower or 'drop' in name_lower:
            return 'file_drop'
        elif 'system' in name_lower or 'event' in name_lower:
            return 'system_event'

        # Check content patterns
        if 'type: email' in content:
            return 'email'
        elif 'type: file_drop' in content:
            return 'file_drop'
        elif 'type: system_event' in content:
            return 'system_event'
        elif 'type: manual' in content:
            return 'manual'

        # Default to manual for user-created files
        return 'manual'

    def _parse_email_file(self, content: str) -> Dict[str, Any]:
        """Parse email watcher file"""
        data = {
            "source_type": "email",
            "parsed_fields": {}
        }

        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        data["parsed_fields"].update(frontmatter)

        # Extract email-specific fields
        patterns = {
            "from": r"from:\s*(.+?)(?:\n|$)",
            "subject": r"subject:\s*(.+?)(?:\n|$)",
            "to": r"to:\s*(.+?)(?:\n|$)",
            "date": r"received:\s*(.+?)(?:\n|$)",
            "priority": r"priority:\s*(\w+)(?:\n|$)",
            "message_id": r"message_id:\s*(.+?)(?:\n|$)"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data["parsed_fields"][field] = match.group(1).strip()

        # Extract email content
        content_match = re.search(r'## Email Content\s*\n(.*)', content, re.DOTALL)
        if content_match:
            data["email_content"] = content_match.group(1).strip()

        # Extract suggested actions
        actions_match = re.search(r'## Suggested Actions\s*\n(.*)', content, re.DOTALL)
        if actions_match:
            actions_text = actions_match.group(1).strip()
            data["suggested_actions"] = [
                line.strip().replace('- [ ] ', '').replace('- [x] ', '')
                for line in actions_text.split('\n')
                if line.strip().startswith('-')
            ]

        return data

    def _parse_file_drop(self, content: str) -> Dict[str, Any]:
        """Parse file drop watcher file"""
        data = {
            "source_type": "file_drop",
            "parsed_fields": {}
        }

        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        data["parsed_fields"].update(frontmatter)

        # Extract file-specific fields
        patterns = {
            "original_name": r"original_name:\s*(.+?)(?:\n|$)",
            "size": r"size:\s*(\d+)(?:\n|$)",
            "type": r"type:\s*(\w+)(?:\n|$)"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if field == "size":
                    value = int(value)
                data["parsed_fields"][field] = value

        # Extract description
        desc_match = re.search(r'New file dropped for processing\.\s*\n(.*)', content, re.DOTALL)
        if desc_match:
            data["description"] = desc_match.group(1).strip()

        return data

    def _parse_system_event(self, content: str) -> Dict[str, Any]:
        """Parse system event watcher file"""
        data = {
            "source_type": "system_event",
            "parsed_fields": {}
        }

        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)
        data["parsed_fields"].update(frontmatter)

        # Extract system-specific fields
        patterns = {
            "event_type": r"event_type:\s*(\w+)(?:\n|$)",
            "severity": r"severity:\s*(\w+)(?:\n|$)",
            "component": r"component:\s*(.+?)(?:\n|$)",
            "timestamp": r"timestamp:\s*(.+?)(?:\n|$)"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data["parsed_fields"][field] = match.group(1).strip()

        # Extract event description
        event_match = re.search(r'# System Event\s*\n\n## Description\s*\n(.*)', content, re.DOTALL)
        if event_match:
            data["event_description"] = event_match.group(1).strip()

        return data

    def _parse_manual_file(self, content: str) -> Dict[str, Any]:
        """Parse manually created file"""
        data = {
            "source_type": "manual",
            "parsed_fields": {}
        }

        # Extract frontmatter if present
        frontmatter = self._extract_frontmatter(content)
        data["parsed_fields"].update(frontmatter)

        # Extract any headers as sections
        sections = re.findall(r'^#+\s+(.+?)\s*$', content, re.MULTILINE)
        if sections:
            data["sections"] = sections

        # Get first few lines as summary
        lines = content.split('\n')
        summary_lines = []
        for line in lines:
            if line.strip() and not line.startswith('#') and not line.startswith('---'):
                summary_lines.append(line.strip())
            if len(summary_lines) >= 3:
                break

        data["summary"] = ' '.join(summary_lines)

        return data

    def _parse_generic_file(self, content: str) -> Dict[str, Any]:
        """Parse generic file with basic extraction"""
        data = {
            "source_type": "unknown",
            "parsed_fields": {}
        }

        # Try to extract any YAML frontmatter
        frontmatter = self._extract_frontmatter(content)
        if frontmatter:
            data["parsed_fields"].update(frontmatter)

        # Get basic stats
        data["line_count"] = len(content.split('\n'))
        data["word_count"] = len(content.split())
        data["has_frontmatter"] = bool(frontmatter)

        return data

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract YAML frontmatter from content"""
        frontmatter = {}

        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    import yaml
                    yaml_content = parts[1].strip()
                    if yaml_content:
                        parsed = yaml.safe_load(yaml_content)
                        if isinstance(parsed, dict):
                            frontmatter = parsed
            except Exception as e:
                self.logger.warning(f"Failed to parse frontmatter: {e}")

        return frontmatter


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python parse_watcher_file.py '<json_params>'")
        sys.exit(1)

    run_skill(ParseWatcherFileSkill, sys.argv[1])