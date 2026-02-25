"""
File System Watcher - Monitors a drop folder for new files

This watcher monitors a designated folder for new files and creates
action items in the vault when files are detected.
"""

import time
import shutil
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from base_watcher import BaseWatcher


class DropFolderHandler(FileSystemEventHandler):
    """Handler for file system events"""

    def __init__(self, watcher_instance):
        self.watcher = watcher_instance
        self.logger = watcher_instance.logger

    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Ignore temporary files
        if self._is_temp_file(source):
            self.logger.debug(f'Ignoring temporary file: {source.name}')
            return

        # Wait for file to be completely written
        self.logger.info(f'Detected new file: {source.name}')
        time.sleep(0.5)  # Initial wait

        if not self.watcher._wait_for_file_complete(source):
            self.logger.warning(f'File may be incomplete: {source.name}')

        try:
            # Create action file
            item = {
                'id': self.watcher._generate_unique_id(str(source.absolute())),
                'source_path': str(source.absolute()),
                'filename': source.name,
                'size': source.stat().st_size,
                'detected_at': datetime.now().isoformat()
            }

            self.watcher.create_action_file(item)

        except Exception as e:
            self.logger.error(f'Failed to process file {source.name}: {e}', exc_info=True)

    def _is_temp_file(self, filepath: Path) -> bool:
        """Check if file is temporary"""
        temp_patterns = ['.tmp', '.swp', '.lock', '~', '.crdownload', '.part']
        name = filepath.name.lower()
        return any(name.endswith(pattern) or name.startswith('.') for pattern in temp_patterns)


class FileSystemWatcher(BaseWatcher):
    """Watcher for monitoring a drop folder"""

    def __init__(self, vault_path: str, monitored_folder: str, check_interval: int = 5):
        super().__init__(vault_path, check_interval)
        self.monitored_folder = Path(monitored_folder)
        self.monitored_folder.mkdir(parents=True, exist_ok=True)

        self.observer = Observer()
        self.handler = DropFolderHandler(self)

        self.logger.info(f'Monitoring folder: {self.monitored_folder}')

    def check_for_updates(self):
        """Not used in watchdog pattern - events are handled by observer"""
        return []

    def create_action_file(self, item: dict) -> Path:
        """Create action file for dropped file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sanitized_name = self._sanitize_filename(item['filename'])

        # Create unique filename
        action_filename = f'FILE_{timestamp}_{sanitized_name}'

        # If it's a markdown file, use it directly
        source_path = Path(item['source_path'])
        if source_path.suffix.lower() == '.md':
            action_filepath = self.needs_action / f'{action_filename}.md'
        else:
            action_filepath = self.needs_action / f'{action_filename}.md'

        # Create metadata markdown file
        content = self._create_metadata_content(item)

        # Write with file locking
        action_filepath.write_text(content)

        # Copy the original file if it's not markdown
        if source_path.suffix.lower() != '.md':
            copied_file = self.needs_action / sanitized_name
            shutil.copy2(source_path, copied_file)
            self.logger.info(f'Copied file to: {copied_file}')

        return action_filepath

    def _create_metadata_content(self, item: dict) -> str:
        """Create markdown content with file metadata"""
        source_path = Path(item['source_path'])
        mime_type = self._get_mime_type(source_path)

        content = f"""---
type: file_drop
original_name: {item['filename']}
source_path: {item['source_path']}
size: {item['size']}
mime_type: {mime_type}
detected_at: {item['detected_at']}
status: pending
---

# File Drop Notification

A new file has been dropped for processing.

## File Details
- **Original Name**: `{item['filename']}`
- **Size**: {self._format_size(item['size'])}
- **Type**: {mime_type}
- **Location**: `{item['source_path']}`
- **Detected at**: {item['detected_at']}

## Recommended Actions
- [ ] Review the file content
- [ ] Determine appropriate processing steps
- [ ] Update Dashboard.md with status
- [ ] Move to /Done/ when complete

## Processing Notes
Add your processing notes here...
"""
        return content

    def _get_mime_type(self, file_path: Path) -> str:
        """Simple MIME type detection based on extension"""
        suffix = file_path.suffix.lower()
        mime_types = {
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.zip': 'application/zip',
        }
        return mime_types.get(suffix, 'application/octet-stream')

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def run(self):
        """Start the file system watcher using watchdog"""
        self.observer.schedule(self.handler, str(self.monitored_folder), recursive=False)
        self.observer.start()
        self.logger.info(f'File system watcher started for {self.monitored_folder}')

        try:
            while True:
                time.sleep(1)  # Keep the thread alive
        except KeyboardInterrupt:
            self.observer.stop()
            self.logger.info('File system watcher stopped by user')
        except Exception as e:
            self.logger.error(f'Watcher error: {e}', exc_info=True)
            self.observer.stop()
        finally:
            self.observer.join()
            self._save_state()
