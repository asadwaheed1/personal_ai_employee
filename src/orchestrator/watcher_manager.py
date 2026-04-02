"""
Watcher Manager - Manages multiple watcher processes

This module manages the lifecycle of multiple watcher processes:
- File System Watcher
- Gmail Watcher
- LinkedIn Watcher

Features:
- Process lifecycle management (start/stop/restart)
- Health monitoring
- Auto-restart on failure
- Process coordination
"""

import subprocess
import time
import signal
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import psutil
import json
import logging


class WatcherProcess:
    """Represents a managed watcher process"""

    def __init__(self, name: str, command: List[str], env: Optional[Dict] = None):
        self.name = name
        self.command = command
        self.env = env or {}
        self.process: Optional[subprocess.Popen] = None
        self.started_at: Optional[datetime] = None
        self.restart_count = 0
        self.max_restarts = 10  # Prevent infinite restart loops
        self.last_error: Optional[str] = None
        self.status = 'stopped'

    def start(self) -> bool:
        """Start the watcher process"""
        try:
            if self.is_running():
                logging.info(f"{self.name} is already running")
                return True

            # Merge environment
            env = {**dict(os.environ), **self.env}

            # Start process
            self.process = subprocess.Popen(
                self.command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent.parent)
            )

            self.started_at = datetime.now()
            self.status = 'running'

            # Wait a moment to check if it started successfully
            time.sleep(1)
            if self.process.poll() is not None:
                # Process exited immediately
                stdout, stderr = self.process.communicate()
                self.last_error = stderr.decode() if stderr else "Process exited immediately"
                self.status = 'failed'
                return False

            logging.info(f"Started {self.name} (PID: {self.process.pid})")
            return True

        except Exception as e:
            self.last_error = str(e)
            self.status = 'failed'
            logging.error(f"Failed to start {self.name}: {e}")
            return False

    def stop(self, timeout: int = 5) -> bool:
        """Stop the watcher process gracefully"""
        if not self.process or self.process.poll() is not None:
            self.status = 'stopped'
            return True

        try:
            # Try graceful termination first
            self.process.terminate()
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                self.process.kill()
                self.process.wait()

            self.status = 'stopped'
            logging.info(f"Stopped {self.name}")
            return True

        except Exception as e:
            logging.error(f"Error stopping {self.name}: {e}")
            return False

    def restart(self) -> bool:
        """Restart the watcher process"""
        # Check if we've exceeded max restarts
        if self.restart_count >= self.max_restarts:
            self.logger.error(f"{self.name} has exceeded max restarts ({self.max_restarts}), not restarting")
            self.status = 'failed_max_restarts'
            return False

        self.stop()
        time.sleep(2)  # Cooldown period between restarts
        self.restart_count += 1
        return self.start()

    def is_running(self) -> bool:
        """Check if the process is running"""
        if not self.process:
            return False
        return self.process.poll() is None

    def get_info(self) -> Dict:
        """Get process information"""
        return {
            'name': self.name,
            'status': 'running' if self.is_running() else self.status,
            'pid': self.process.pid if self.process else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'uptime_seconds': (datetime.now() - self.started_at).total_seconds() if self.started_at else None,
            'restart_count': self.restart_count,
            'last_error': self.last_error
        }


class WatcherManager:
    """Manages all watcher processes"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.watchers: Dict[str, WatcherProcess] = {}
        self.logger = self._setup_logging()
        self.running = False

    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f'watcher_manager_{datetime.now().strftime("%Y-%m-%d")}.log'

        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        logger = logging.getLogger('WatcherManager')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        return logger

    def register_watcher(self, name: str, command: List[str], env: Optional[Dict] = None):
        """Register a watcher to be managed"""
        self.watchers[name] = WatcherProcess(name, command, env)
        self.logger.info(f"Registered watcher: {name}")

    def start_all(self) -> Dict[str, bool]:
        """Start all registered watchers"""
        results = {}
        for name, watcher in self.watchers.items():
            self.logger.info(f"Starting {name}...")
            results[name] = watcher.start()
        return results

    def stop_all(self) -> Dict[str, bool]:
        """Stop all watchers"""
        results = {}
        for name, watcher in self.watchers.items():
            self.logger.info(f"Stopping {name}...")
            results[name] = watcher.stop()
        return results

    def restart_watcher(self, name: str) -> bool:
        """Restart a specific watcher"""
        if name not in self.watchers:
            self.logger.error(f"Unknown watcher: {name}")
            return False
        return self.watchers[name].restart()

    def get_status(self) -> Dict[str, Dict]:
        """Get status of all watchers"""
        return {name: watcher.get_info() for name, watcher in self.watchers.items()}

    def health_check(self) -> List[str]:
        """Check health of all watchers, return list of failed watchers"""
        failed = []
        for name, watcher in self.watchers.items():
            if not watcher.is_running() and watcher.status != 'stopped':
                self.logger.warning(f"{name} is not running (status: {watcher.status})")
                failed.append(name)
        return failed

    def auto_restart_failed(self) -> Dict[str, bool]:
        """Automatically restart failed watchers"""
        failed = self.health_check()
        results = {}
        for name in failed:
            self.logger.info(f"Auto-restarting failed watcher: {name}")
            results[name] = self.watchers[name].restart()
        return results

    def save_state(self):
        """Save manager state to file"""
        state_path = self.vault_path / '.state' / 'watcher_manager_state.json'
        state_path.parent.mkdir(exist_ok=True)

        state = {
            'timestamp': datetime.now().isoformat(),
            'watchers': self.get_status()
        }

        state_path.write_text(json.dumps(state, indent=2))

    def run_monitoring_loop(self, check_interval: int = 30):
        """Main monitoring loop"""
        self.running = True
        self.logger.info("Watcher Manager monitoring loop started")

        def signal_handler(signum, frame):
            self.logger.info("Received shutdown signal")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while self.running:
                # Health check and auto-restart
                failed = self.health_check()
                if failed:
                    self.logger.info(f"Found {len(failed)} failed watchers, auto-restarting...")
                    self.auto_restart_failed()

                # Save state
                self.save_state()

                # Update Dashboard
                self._update_dashboard()

                time.sleep(check_interval)

        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}", exc_info=True)
        finally:
            self.logger.info("Stopping all watchers...")
            self.stop_all()
            self.save_state()

    def _update_dashboard(self):
        """Update Dashboard with watcher status"""
        try:
            dashboard_path = self.vault_path / 'Dashboard.md'
            if not dashboard_path.exists():
                return

            content = dashboard_path.read_text()
            status = self.get_status()

            # Create watcher status section
            watcher_section = "\n## Watcher Status\n\n"
            watcher_section += "| Watcher | Status | PID | Uptime | Restarts |\n"
            watcher_section += "|---------|--------|-----|--------|----------|\n"

            for name, info in status.items():
                status_icon = "🟢" if info['status'] == 'running' else "🔴"
                uptime = f"{int(info['uptime_seconds'] // 60)}m" if info['uptime_seconds'] else "N/A"
                watcher_section += f"| {name} | {status_icon} {info['status']} | {info['pid'] or 'N/A'} | {uptime} | {info['restart_count']}|\n"

            # Replace or add watcher status section
            if "## Watcher Status" in content:
                import re
                content = re.sub(
                    r'## Watcher Status.*?(?=## |$)',
                    watcher_section,
                    content,
                    flags=re.DOTALL
                )
            else:
                content += watcher_section

            dashboard_path.write_text(content)

        except Exception as e:
            self.logger.warning(f"Failed to update dashboard: {e}")


def create_default_manager(vault_path: str) -> WatcherManager:
    """Create a WatcherManager with default watchers"""
    manager = WatcherManager(vault_path)

    # Get Python executable
    python = sys.executable

    # File System Watcher (always enabled)
    manager.register_watcher(
        'filesystem_watcher',
        [python, '-m', 'src.watchers.run_filesystem_watcher', vault_path]
    )

    # Gmail Watcher (if credentials exist)
    gmail_creds = Path(vault_path).parent / 'credentials' / 'gmail_credentials.json'
    if gmail_creds.exists():
        manager.register_watcher(
            'gmail_watcher',
            [python, '-m', 'src.watchers.run_gmail_watcher', vault_path]
        )
    else:
        logging.warning(f"Gmail credentials not found at {gmail_creds}, skipping Gmail watcher")

    # LinkedIn Watcher (if credentials configured)
    import os
    if os.getenv('LINKEDIN_USERNAME') and os.getenv('LINKEDIN_PASSWORD'):
        manager.register_watcher(
            'linkedin_watcher',
            [python, '-m', 'src.watchers.run_linkedin_watcher', vault_path]
        )
    else:
        logging.warning("LinkedIn credentials not configured, skipping LinkedIn watcher")

    return manager


if __name__ == '__main__':
    import os

    if len(sys.argv) < 2:
        print('Usage: python watcher_manager.py <vault_path> [command]')
        print('Commands: start, stop, status, restart <watcher_name>')
        sys.exit(1)

    vault_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'start'

    manager = create_default_manager(vault_path)

    if command == 'start':
        print("Starting all watchers...")
        results = manager.start_all()
        for name, success in results.items():
            print(f"  {name}: {'✓' if success else '✗'}")

        # Start monitoring loop
        manager.run_monitoring_loop()

    elif command == 'stop':
        print("Stopping all watchers...")
        results = manager.stop_all()
        for name, success in results.items():
            print(f"  {name}: {'✓' if success else '✗'}")

    elif command == 'status':
        status = manager.get_status()
        print("\nWatcher Status:")
        print("-" * 60)
        for name, info in status.items():
            print(f"\n{name}:")
            print(f"  Status: {info['status']}")
            print(f"  PID: {info['pid']}")
            if info['uptime_seconds']:
                print(f"  Uptime: {int(info['uptime_seconds'] // 60)} minutes")
            print(f"  Restarts: {info['restart_count']}")
            if info['last_error']:
                print(f"  Last Error: {info['last_error'][:100]}")

    elif command == 'restart' and len(sys.argv) > 3:
        watcher_name = sys.argv[3]
        success = manager.restart_watcher(watcher_name)
        print(f"Restart {watcher_name}: {'✓' if success else '✗'}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
