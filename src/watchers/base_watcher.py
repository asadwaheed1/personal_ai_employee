"""
Base Watcher Class - Foundation for all watchers

This module provides the abstract base class that all watchers must inherit from.
It includes persistent state management, file locking, and error handling.
"""

import time
import logging
import json
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import fcntl
import hashlib


class BaseWatcher(ABC):
    """Abstract base class for all watcher implementations"""

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # State management
        self.state_dir = self.vault_path / '.state'
        self.state_file = self.state_dir / f'{self.__class__.__name__.lower()}_state.json'
        self.state_dir.mkdir(exist_ok=True)

        # Load persistent state
        self.processed_ids = self._load_state()

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for the watcher"""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f'{self.__class__.__name__.lower()}_{datetime.now().strftime("%Y-%m-%d")}.log'

        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _load_state(self) -> set:
        """Load processed IDs from persistent state file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
            except Exception as e:
                self.logger.error(f'Failed to load state: {e}')
                return set()
        return set()

    def _save_state(self):
        """Save processed IDs to persistent state file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'processed_ids': list(self.processed_ids),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f'Failed to save state: {e}')

    def _acquire_file_lock(self, filepath: Path, timeout: int = 5) -> bool:
        """Acquire an exclusive lock on a file"""
        lock_file = filepath.with_suffix('.lock')
        try:
            lock_fd = open(lock_file, 'w')
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False

    def _release_file_lock(self, filepath: Path):
        """Release file lock"""
        lock_file = filepath.with_suffix('.lock')
        if lock_file.exists():
            try:
                lock_file.unlink()
            except Exception as e:
                self.logger.warning(f'Failed to release lock: {e}')

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename to prevent path traversal and special characters"""
        import re
        # Remove path separators and special characters
        sanitized = re.sub(r'[^\w\-. ]', '_', name)
        # Limit length
        sanitized = sanitized[:100]
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        return sanitized or 'unnamed'

    def _generate_unique_id(self, content: str) -> str:
        """Generate a unique ID for content to prevent duplicates"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _wait_for_file_complete(self, filepath: Path, timeout: int = 5):
        """Wait for a file to be completely written"""
        start_time = time.time()
        last_size = -1

        while time.time() - start_time < timeout:
            try:
                current_size = filepath.stat().st_size
                if current_size == last_size and current_size > 0:
                    # File size hasn't changed, likely complete
                    time.sleep(0.1)  # One more small wait
                    return True
                last_size = current_size
                time.sleep(0.2)
            except FileNotFoundError:
                return False

        return True

    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check external source for new items

        Returns:
            List of items to process, each as a dictionary
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create a markdown file in Needs_Action folder

        Args:
            item: Dictionary containing item data

        Returns:
            Path to the created file
        """
        pass

    def run(self):
        """Main watcher loop"""
        self.logger.info(f'Starting {self.__class__.__name__}')

        while True:
            try:
                items = self.check_for_updates()

                if items:
                    self.logger.info(f'Found {len(items)} new items')

                for item in items:
                    try:
                        filepath = self.create_action_file(item)
                        self.logger.info(f'Created action file: {filepath.name}')

                        # Mark as processed
                        item_id = item.get('id')
                        if item_id:
                            self.processed_ids.add(item_id)

                    except Exception as e:
                        self.logger.error(f'Failed to create action file: {e}', exc_info=True)

                # Save state after processing batch
                if items:
                    self._save_state()

            except Exception as e:
                self.logger.error(f'Error in watcher loop: {e}', exc_info=True)

            time.sleep(self.check_interval)
