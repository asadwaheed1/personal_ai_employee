"""
Watchdog Process - Monitors and restarts critical processes

This watchdog ensures that watchers and orchestrator stay running.
It automatically restarts failed processes and alerts on critical failures.
"""

import subprocess
import time
import psutil
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class ProcessWatchdog:
    """Monitors and restarts critical processes"""

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.pid_dir = Path('/tmp/ai_employee_pids')
        self.pid_dir.mkdir(exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Define processes to monitor
        self.processes = self._get_process_definitions()

        # Track restart counts
        self.restart_counts = {name: 0 for name in self.processes.keys()}
        self.max_restarts = 5  # Max restarts per hour

    def _setup_logging(self):
        """Configure logging"""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f'watchdog_{datetime.now().strftime("%Y-%m-%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('Watchdog')

    def _get_process_definitions(self) -> Dict[str, Dict]:
        """Define processes to monitor"""
        project_root = self.vault_path.parent
        src_dir = project_root / 'src'

        return {
            'orchestrator': {
                'command': [
                    sys.executable,
                    str(src_dir / 'orchestrator' / 'orchestrator.py'),
                    str(self.vault_path),
                    '30'
                ],
                'cwd': str(src_dir / 'orchestrator'),
                'critical': True
            },
            'filesystem_watcher': {
                'command': [
                    sys.executable,
                    str(src_dir / 'watchers' / 'filesystem_watcher.py'),
                    str(self.vault_path),
                    str(self.vault_path / 'Inbox')
                ],
                'cwd': str(src_dir / 'watchers'),
                'critical': True
            }
        }

    def _get_pid_file(self, process_name: str) -> Path:
        """Get PID file path for a process"""
        return self.pid_dir / f'{process_name}.pid'

    def _is_process_running(self, process_name: str) -> bool:
        """Check if a process is running based on PID file"""
        pid_file = self._get_pid_file(process_name)

        if not pid_file.exists():
            return False

        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process exists
            return psutil.pid_exists(pid)

        except (ValueError, FileNotFoundError):
            return False
        except Exception as e:
            self.logger.warning(f'Error checking process {process_name}: {e}')
            return False

    def _start_process(self, process_name: str) -> Optional[int]:
        """Start a process and return its PID"""
        process_def = self.processes[process_name]

        try:
            self.logger.info(f'Starting {process_name}...')

            proc = subprocess.Popen(
                process_def['command'],
                cwd=process_def.get('cwd'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Detach from parent
            )

            # Save PID
            pid_file = self._get_pid_file(process_name)
            pid_file.write_text(str(proc.pid))

            self.logger.info(f'{process_name} started with PID {proc.pid}')
            return proc.pid

        except Exception as e:
            self.logger.error(f'Failed to start {process_name}: {e}', exc_info=True)
            return None

    def _stop_process(self, process_name: str):
        """Stop a process gracefully"""
        pid_file = self._get_pid_file(process_name)

        if not pid_file.exists():
            return

        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=10)
                self.logger.info(f'Stopped {process_name} (PID {pid})')

            pid_file.unlink()

        except Exception as e:
            self.logger.warning(f'Error stopping {process_name}: {e}')

    def _notify_human(self, message: str):
        """Notify human of critical issues"""
        # For Bronze tier, just log to a special file
        alert_file = self.vault_path / 'Logs' / 'ALERTS.md'

        alert_content = f"""
## Alert: {datetime.now().isoformat()}

{message}

---
"""
        try:
            with open(alert_file, 'a') as f:
                f.write(alert_content)
            self.logger.warning(f'ALERT: {message}')
        except Exception as e:
            self.logger.error(f'Failed to write alert: {e}')

    def check_and_restart(self):
        """Check all processes and restart if needed"""
        for name, process_def in self.processes.items():
            if not self._is_process_running(name):
                self.logger.warning(f'{name} is not running')

                # Check restart count
                if self.restart_counts[name] >= self.max_restarts:
                    self._notify_human(
                        f'{name} has failed {self.max_restarts} times. '
                        f'Manual intervention required.'
                    )
                    continue

                # Restart the process
                pid = self._start_process(name)

                if pid:
                    self.restart_counts[name] += 1
                    self._notify_human(f'{name} was restarted (restart #{self.restart_counts[name]})')
                else:
                    self._notify_human(f'Failed to restart {name}')

    def reset_restart_counts(self):
        """Reset restart counts (called hourly)"""
        self.restart_counts = {name: 0 for name in self.processes.keys()}
        self.logger.info('Restart counts reset')

    def run(self):
        """Main watchdog loop"""
        self.logger.info('Watchdog started')
        self.logger.info(f'Monitoring {len(self.processes)} processes')

        # Start all processes initially
        for name in self.processes.keys():
            if not self._is_process_running(name):
                self._start_process(name)

        last_reset = time.time()

        try:
            while True:
                self.check_and_restart()

                # Reset restart counts every hour
                if time.time() - last_reset > 3600:
                    self.reset_restart_counts()
                    last_reset = time.time()

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Watchdog stopped by user')

            # Stop all processes
            for name in self.processes.keys():
                self._stop_process(name)

        except Exception as e:
            self.logger.error(f'Watchdog error: {e}', exc_info=True)

    def stop_all(self):
        """Stop all monitored processes"""
        self.logger.info('Stopping all processes...')
        for name in self.processes.keys():
            self._stop_process(name)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python watchdog.py <vault_path> [check_interval]')
        sys.exit(1)

    vault_path = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    watchdog = ProcessWatchdog(vault_path, check_interval)
    watchdog.run()
