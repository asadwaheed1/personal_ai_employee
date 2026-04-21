"""
Orchestrator - Coordinates watchers and Claude Code processing

This orchestrator monitors the vault for new files and triggers Claude Code
to process them. It handles multiple folders and implements proper file locking.

Silver Tier Enhancement: Includes MCP action processing for external actions.
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

# Import MCP processor for Silver Tier
from .mcp_processor import MCPProcessor
from .skills.update_dashboard import UpdateDashboardSkill


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

        # Initialize MCP processor for Silver Tier
        self.mcp_processor = MCPProcessor(str(vault_path))

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

    def _log_dashboard_event(self, activity_log: str = '', summary: str = ''):
        """Append event activity to dashboard and refresh pending counts"""
        try:
            dashboard_skill = UpdateDashboardSkill(str(self.vault_path))
            params = {'status': 'operational'}
            if activity_log:
                params['activity_log'] = activity_log
            if summary:
                params['summary'] = summary
            dashboard_skill.execute(params)
        except Exception as e:
            self.logger.warning(f'Failed to update dashboard event: {e}')

    def _acquire_processing_lock(self) -> bool:
        """Acquire global processing lock to prevent concurrent Claude runs"""
        try:
            self.state_dir.mkdir(exist_ok=True)
            self.lock_fd = open(self.processing_lock, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(datetime.now().isoformat()))
            self.lock_fd.flush()
            return True
        except (IOError, OSError) as e:
            # Check if lock file is stale (older than 10 minutes)
            if self.processing_lock.exists():
                try:
                    lock_age = time.time() - self.processing_lock.stat().st_mtime
                    if lock_age > 600:  # 10 minutes
                        self.logger.warning(f"Stale lock file detected (age: {lock_age:.0f}s), removing")
                        self.processing_lock.unlink()
                        # Try to acquire again
                        return self._acquire_processing_lock()
                except Exception:
                    pass
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
            'needs_action_mcp': [],  # MCP action files
            'approved': [],
            'inbox': []
        }

        # Check Needs_Action folder for markdown files
        if self.needs_action.exists():
            files['needs_action'] = sorted(
                [f for f in self.needs_action.glob('*.md') if not f.name.startswith('.')],
                key=lambda x: x.stat().st_mtime
            )

            # Check for MCP action files (JSON files with MCP_ prefix)
            files['needs_action_mcp'] = sorted(
                [f for f in self.needs_action.glob('MCP_*.json') if not f.name.startswith('.')],
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
        instruction_file = None
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
            # Using --dangerously-skip-permissions to allow file operations in automated mode
            result = subprocess.run(
                ['claude', '--dangerously-skip-permissions', 'Please read and execute the instructions in .claude_instruction.md'],
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

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
        finally:
            # Clean up instruction file
            if instruction_file and instruction_file.exists():
                try:
                    instruction_file.unlink()
                except Exception as e:
                    self.logger.warning(f'Failed to cleanup instruction file: {e}')

    def _process_needs_action(self, files: List[Path]) -> bool:
        """Process files in Needs_Action folder"""
        if not files:
            return True

        self.logger.info(f'Processing {len(files)} files in Needs_Action')
        self._log_dashboard_event(
            activity_log=f"Needs_Action intake: {len(files)} file(s) detected",
            summary=f"Processing {len(files)} item(s) from Needs_Action"
        )

        # Auto-process newsletter/promotional emails first
        email_files = [f for f in files if f.name.startswith('EMAIL_') and f.suffix == '.md']
        if email_files:
            self.logger.info(f'Auto-processing {len(email_files)} email files')
            self._auto_process_emails()

        # Only trigger Claude for non-email markdown tasks.
        # Important emails stay in Needs_Action for human review.
        remaining_non_email = [
            f for f in self.needs_action.glob('*.md')
            if not f.name.startswith('EMAIL_') and not f.name.startswith('.')
        ]

        if not remaining_non_email:
            self.logger.info('No non-email Needs_Action files to process')
            return True

        context = f'Process {len(remaining_non_email)} non-email items in /Needs_Action/ folder and update Dashboard.md'
        return self._trigger_claude_processing(context)

    def _auto_process_emails(self) -> bool:
        """Auto-process newsletter/promotional emails"""
        try:
            import subprocess
            import sys

            skill_path = Path(__file__).parent / 'skills' / 'auto_process_emails.py'

            result = subprocess.run(
                [sys.executable, str(skill_path), json.dumps({'vault_path': str(self.vault_path)})],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.vault_path.parent)
            )

            if result.returncode == 0:
                summary_logged = False
                try:
                    payload = json.loads(result.stdout)
                    skill_result = payload.get('result', {}) if isinstance(payload, dict) else {}
                    processed = skill_result.get('processed', 0)
                    kept_for_review = skill_result.get('kept_for_review', 0)
                    moved_to_pending = skill_result.get('moved_to_pending_approval', 0)
                    self.logger.info(
                        'Auto-processing completed: '
                        f'processed={processed}, '
                        f'kept_for_review={kept_for_review}, '
                        f'moved_to_pending_approval={moved_to_pending}'
                    )
                    self._log_dashboard_event(
                        activity_log=(
                            f"Email auto-processing: processed={processed}, "
                            f"kept_for_review={kept_for_review}, "
                            f"moved_to_pending_approval={moved_to_pending}"
                        ),
                        summary=(
                            f"Needs_Action email cycle complete: {processed} auto-processed, "
                            f"{kept_for_review} kept for review, "
                            f"{moved_to_pending} moved to Pending_Approval"
                        )
                    )
                    summary_logged = True
                except Exception:
                    pass

                if not summary_logged:
                    self.logger.info('Auto-processing completed successfully')
                return True
            else:
                self.logger.error(f'Auto-processing failed: {result.stderr}')
                return False

        except Exception as e:
            self.logger.error(f'Error in auto-processing: {e}', exc_info=True)
            return False

    def _process_mcp_actions(self, files: List[Path]) -> bool:
        """
        Process MCP action files via MCP processor (Silver Tier)

        Args:
            files: List of MCP action JSON files

        Returns:
            True if all actions processed successfully, False otherwise
        """
        if not files:
            return True

        self.logger.info(f'Processing {len(files)} MCP action files')

        try:
            # Process all pending MCP actions
            results = self.mcp_processor.process_pending_actions()

            self.logger.info(f"MCP processing complete: {results['successful']} successful, {results['failed']} failed")
            self._log_dashboard_event(
                activity_log=(
                    f"MCP actions executed: {results['successful']} success, "
                    f"{results['failed']} failed"
                ),
                summary=(
                    f"Done updates from MCP: {results['successful']} executed, "
                    f"{results['failed']} failed"
                )
            )

            # Return True if at least some succeeded, or if there were no failures
            return results['failed'] == 0 or results['successful'] > 0

        except Exception as e:
            self.logger.error(f'Error processing MCP actions: {e}', exc_info=True)
            return False

    def _process_approved(self, files: List[Path]) -> bool:
        """Process approved actions by executing email actions directly"""
        if not files:
            return True

        self.logger.info(f'Executing {len(files)} approved actions')
        self._log_dashboard_event(
            activity_log=f"Approved intake: {len(files)} file(s) ready for execution",
            summary=f"Executing {len(files)} approved action(s)"
        )

        success_count = 0
        for file_path in files:
            try:
                # Check if it's an email file
                content = file_path.read_text()
                if 'type: email' in content and 'message_id:' in content:
                    # Execute email actions directly via skill
                    self.logger.info(f'Processing approved email: {file_path.name}')
                    result = self._execute_email_actions(file_path)
                    if result:
                        success_count += 1
                else:
                    # For non-email files, use generic Claude processing
                    self.logger.info(f'Processing approved file (non-email): {file_path.name}')
                    context = f'Execute approved action from {file_path.name}'
                    if self._trigger_claude_processing(context):
                        success_count += 1

            except Exception as e:
                self.logger.error(f'Failed to process approved file {file_path.name}: {e}', exc_info=True)

        self.logger.info(f'Approved actions: {success_count}/{len(files)} successful')
        self._log_dashboard_event(
            activity_log=f"Approved execution complete: {success_count}/{len(files)} succeeded",
            summary=f"Approved actions executed: {success_count} success, {len(files) - success_count} failed"
        )
        return success_count > 0

    def _execute_email_actions(self, email_file: Path) -> bool:
        """Execute email actions from approved email file"""
        try:
            import subprocess
            import sys

            # Call process_email_actions skill directly
            skill_path = Path(__file__).parent / 'skills' / 'process_email_actions.py'

            params = {
                'email_file': str(email_file),
                'vault_path': str(self.vault_path)
            }

            result = subprocess.run(
                [sys.executable, str(skill_path), json.dumps(params)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.vault_path.parent)
            )

            if result.returncode == 0:
                self.logger.info(f'Email actions executed successfully for {email_file.name}')
                # process_email_actions skill archives file to Done itself.
                return True
            else:
                self.logger.error(f'Email action execution failed: {result.stderr}')
                return False

        except Exception as e:
            self.logger.error(f'Error executing email actions: {e}', exc_info=True)
            return False

    def _process_inbox(self, files: List[Path]) -> bool:
        """Process files in Inbox folder"""
        if not files:
            return True

        self.logger.info(f'Processing {len(files)} files in Inbox')
        self._log_dashboard_event(
            activity_log=f"Inbox intake: {len(files)} new file(s)",
            summary=f"Processing {len(files)} new Inbox item(s)"
        )
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

            # Process in priority order: MCP Actions > Approved > Needs_Action > Inbox
            success = True

            # Silver Tier: Process MCP action files first
            if files['needs_action_mcp']:
                success = self._process_mcp_actions(files['needs_action_mcp']) and success

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
