"""
Orchestrator - Coordinates watchers and Claude Code processing

This orchestrator monitors the vault for new files and triggers Claude Code
to process them. It handles multiple folders and implements proper file locking.
"""

import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging
import fcntl
import sys


class Orchestrator:
    """Main orchestrator for the AI Employee system"""

    def __init__(self, vault_path: str, check_interval: int = 30):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval

        # Folders to monitor
        self.needs_action = self.vault_path / 'Needs_Action'
        self.approved = self.vault_path / 'Approved'
        self.inbox = self.vault_path / 'Inbox'

        # State management
        self.state_dir = self.vault_path / '.state'
        self.state_file = self.state_dir / 'orchestrator_state.json'
        self.processing_lock = self.state_dir / 'processing.lock'

        # Setup logging
        self._setup_logging()

        # Load state
        self.last_processed = self._load_state()

    def _setup_logging(self):
        """Configure logging"""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f'orchestrator_{datetime.now().strftime("%Y-%m-%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('Orchestrator')

    def _load_state(self) -> Dict:
        """Load orchestrator state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f'Failed to load state: {e}')
        return {'last_check': None, 'processed_count': 0}

    def _save_state(self):
        """Save orchestrator state"""
        try:
            self.state_dir.mkdir(exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    'last_check': datetime.now().isoformat(),
                    'processed_count': self.last_processed.get('processed_count', 0)
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f'Failed to save state: {e}')

    def _acquire_processing_lock(self) -> bool:
        """Acquire global processing lock to prevent concurrent Claude runs"""
        try:
            self.lock_fd = open(self.processing_lock, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(datetime.now().isoformat()))
            self.lock_fd.flush()
            return True
        except (IOError, OSError):
            return False

    def _release_processing_lock(self):
        """Release processing lock"""
        try:
            if hasattr(self, 'lock_fd'):
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
            if self.processing_lock.exists():
                self.processing_lock.unlink()
        except Exception as e:
            self.logger.warning(f'Failed to release lock: {e}')

    def _get_files_to_process(self) -> Dict[str, List[Path]]:
        """Get all files that need processing from monitored folders"""
        files = {
            'needs_action': [],
            'approved': [],
            'inbox': []
        }

        # Check Needs_Action folder
        if self.needs_action.exists():
            files['needs_action'] = sorted(
                [f for f in self.needs_action.glob('*.md') if not f.name.startswith('.')],
                key=lambda x: x.stat().st_mtime
            )

        # Check Approved folder
        if self.approved.exists():
            files['approved'] = sorted(
                [f for f in self.approved.glob('*.md') if not f.name.startswith('.')],
                key=lambda x: x.stat().st_mtime
            )

        # Check Inbox folder
        if self.inbox.exists():
            files['inbox'] = sorted(
                [f for f in self.inbox.glob('*.md') if not f.name.startswith('.')],
                key=lambda x: x.stat().st_mtime
            )

        return files

    def _trigger_claude_processing(self, context: str) -> bool:
        """
        Trigger Claude Code to process the vault

        Args:
            context: Context string describing what to process

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f'Triggering Claude Code: {context}')

            # Create a processing instruction file
            instruction_file = self.vault_path / '.claude_instruction.md'
            instruction_content = f"""# Processing Instruction

**Generated**: {datetime.now().isoformat()}
**Context**: {context}

## Task
{context}

## Guidelines
1. Read all files in the specified folders
2. Process according to Company_Handbook.md rules
3. Create plans in /Plans/ if needed
4. Create approval requests in /Pending_Approval/ for sensitive actions
5. Update Dashboard.md with current status
6. Move processed files to /Done/ with timestamp
7. Log all actions

## Completion Criteria
All files have been processed and moved to appropriate folders.
"""
            instruction_file.write_text(instruction_content)

            # Run Claude Code with the instruction
            # Note: This assumes Claude Code can be invoked this way
            # You may need to adjust based on actual Claude Code CLI behavior
            result = subprocess.run(
                ['claude', '--cwd', str(self.vault_path), f'Please read and execute the instructions in .claude_instruction.md'],
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Clean up instruction file
            if instruction_file.exists():
                instruction_file.unlink()

            if result.returncode == 0:
                self.logger.info('Claude processing completed successfully')
                self.logger.debug(f'Output: {result.stdout[:500]}')
                return True
            else:
                self.logger.error(f'Claude processing failed: {result.stderr}')
                return False

        except subprocess.TimeoutExpired:
            self.logger.error('Claude processing timed out')
            return False
        except FileNotFoundError:
            self.logger.error('Claude Code CLI not found. Please ensure it is installed and in PATH.')
            return False
        except Exception as e:
            self.logger.error(f'Error triggering Claude: {e}', exc_info=True)
            return False

    def _process_needs_action(self, files: List[Path]) -> bool:
        """Process files in Needs_Action folder"""
        if not files:
            return True

        self.logger.info(f'Processing {len(files)} files in Needs_Action')
        context = f'Process {len(files)} new items in /Needs_Action/ folder and update Dashboard.md'
        return self._trigger_claude_processing(context)

    def _process_approved(self, files: List[Path]) -> bool:
        """Process approved actions"""
        if not files:
            return True

        self.logger.info(f'Executing {len(files)} approved actions')
        context = f'Execute {len(files)} approved actions from /Approved/ folder'
        return self._trigger_claude_processing(context)

    def _process_inbox(self, files: List[Path]) -> bool:
        """Process files in Inbox folder"""
        if not files:
            return True

        self.logger.info(f'Processing {len(files)} files in Inbox')
        context = f'Process {len(files)} items from /Inbox/ folder'
        return self._trigger_claude_processing(context)

    def check_and_trigger(self):
        """Check for new files and trigger Claude if any exist"""
        # Try to acquire processing lock
        if not self._acquire_processing_lock():
            self.logger.debug('Another processing instance is running, skipping...')
            return

        try:
            files = self._get_files_to_process()

            total_files = sum(len(f) for f in files.values())

            if total_files == 0:
                self.logger.debug('No files to process')
                return

            self.logger.info(f'Found {total_files} total files to process')

            # Process in priority order: Approved > Needs_Action > Inbox
            success = True

            if files['approved']:
                success = self._process_approved(files['approved']) and success

            if files['needs_action']:
                success = self._process_needs_action(files['needs_action']) and success

            if files['inbox']:
                success = self._process_inbox(files['inbox']) and success

            if success:
                self.last_processed['processed_count'] = self.last_processed.get('processed_count', 0) + total_files
                self._save_state()

        finally:
            self._release_processing_lock()

    def run_monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info('Orchestrator started')
        self.logger.info(f'Monitoring: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval} seconds')

        try:
            while True:
                self.check_and_trigger()
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped by user')
        except Exception as e:
            self.logger.error(f'Orchestrator error: {e}', exc_info=True)
        finally:
            self._release_processing_lock()
            self._save_state()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('Usage: python orchestrator.py <vault_path> [check_interval]')
        sys.exit(1)

    vault_path = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    orchestrator = Orchestrator(vault_path, check_interval)
    orchestrator.run_monitoring_loop()
