# Personal AI Employee - Agent Architecture

## Bronze Tier Implementation Plan

This document outlines the agent architecture for the Bronze Tier of the Personal AI Employee project, focusing on the foundational components needed to create a minimum viable autonomous system.

## Overview

The Personal AI Employee is designed as a digital full-time equivalent (FTE) that operates using Claude Code as the reasoning engine, Obsidian as the memory/dashboard, Python watcher scripts as sensors, and Model Context Protocol (MCP) servers as actuators.

## Bronze Tier Requirements

The Bronze Tier represents the minimum viable deliverable with these core components:

### 1. Obsidian Vault Structure
- **Dashboard.md**: Real-time summary of activities, pending messages, and active projects
- **Company_Handbook.md**: Rules of engagement and operational guidelines
- **Folder Structure**:
  - `/Inbox/`: Incoming items requiring processing
  - `/Needs_Action/`: Items flagged for action by the AI
  - `/Done/`: Completed tasks archive

### 2. Watcher Implementation
- **Single Watcher Script**: Either Gmail or File System monitoring
- **Functionality**: Continuously monitors external sources and creates actionable files in the vault

### 3. Claude Code Integration
- **Watcher-Triggered**: Claude Code is directly triggered by watcher scripts when events occur
- **Direct File Processing**: When `.md` files are dropped in `/Inbox/`, Claude is triggered to process and move them to `/Done/`
- **Human-in-the-Loop Support**: For sensitive actions such as payments and financial transactions, Claude moves files to `/Needs_Action/` for human review, then processes when moved to `/Approved/`
- **Reading/Writing**: Claude Code must successfully read from and write to the Obsidian vault
- **Agent Skills**: All AI functionality implemented as Agent Skills for modularity and reusability

## Technical Architecture

### Core Components

1. **The Brain**: Claude Code acts as the reasoning engine
2. **The Memory/GUI**: Obsidian vault stores state and provides interface
3. **The Senses**: Python watcher scripts monitor external sources
4. **The Hands**: MCP servers perform external actions

### File-Based State Management

The system uses a file-based approach for state management and communication:
- Items move through `/Inbox/` → `/Needs_Action/` → `/Done/` as they're processed
- Approval workflows use `/Pending_Approval/`, `/Approved/`, and `/Rejected/` folders
- Logs stored in `/Logs/` for audit trail

## Agent Skills Framework

All AI functionality will be implemented as Agent Skills following Claude's skill framework:

### Core Skills Required

1. **File Management Skills**:
   - Read/write files in the vault
   - Move files between folders
   - Parse and extract information from files

2. **Watcher Integration Skills**:
   - Process incoming watcher-generated files
   - Create structured action items
   - Update dashboard status

3. **Decision Making Skills**:
   - Apply rules from Company_Handbook.md
   - Determine appropriate actions based on context
   - Create approval requests when needed

## File System Watcher Implementation

### Architecture Overview

The file system watcher serves as one of the "senses" for the AI Employee, monitoring specific directories for changes and creating actionable items in the Obsidian vault when events occur.

### Core Components

#### 1. Base Watcher Class
The base watcher follows the pattern outlined in the requirements document:

```python
import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod

class BaseWatcher(ABC):
    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def check_for_updates(self) -> list:
        '''Return list of new items to process'''
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        '''Create .md file in Needs_Action folder'''
        pass

    def run(self):
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
            except Exception as e:
                self.logger.error(f'Error: {e}')
            time.sleep(self.check_interval)
```

#### 2. File System Watcher Implementation
The file system watcher monitors a designated drop folder and creates action files when new files are detected:

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
from base_watcher import BaseWatcher

class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str, monitored_folder: str):
        self.needs_action = Path(vault_path) / 'Needs_Action'
        self.monitored_folder = Path(monitored_folder)

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        # Create a uniquely named file in Needs_Action
        dest = self.needs_action / f'FILE_{source.name}_{int(time.time())}'
        if source.suffix.lower() != '.md':
            # Copy the original file
            shutil.copy2(source, dest)
            # Create a metadata file describing the dropped file
            self.create_metadata(source, dest.with_suffix('.md'))
        else:
            # If it's already a markdown file, just copy it
            shutil.copy2(source, dest)

    def on_moved(self, event):
        # Handle file moves as well
        if not event.is_directory:
            self.on_created(type('Event', (), {'src_path': event.dest_path, 'is_directory': False})())

    def create_metadata(self, source: Path, dest: Path):
        """Create a markdown file with metadata about the dropped file"""
        meta_content = f"""---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
mime_type: {self._get_mime_type(source)}
timestamp: {time.time()}
---

# File Drop Notification

A new file has been dropped for processing:

- **Original Name**: `{source.name}`
- **Size**: {source.stat().st_size} bytes
- **Location**: {str(source.absolute())}
- **Detected at**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Recommended Actions
- [ ] Review the file content
- [ ] Determine appropriate processing steps
- [ ] Update Dashboard.md with status

"""
        dest.write_text(meta_content)

    def _get_mime_type(self, file_path: Path):
        """Simple MIME type detection based on extension"""
        suffix = file_path.suffix.lower()
        mime_types = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv',
        }
        return mime_types.get(suffix, 'application/octet-stream')

class FileSystemWatcher(BaseWatcher):
    def __init__(self, vault_path: str, monitored_folder: str, check_interval: int = 5):
        super().__init__(vault_path, check_interval)
        self.monitored_folder = Path(monitored_folder)
        self.observer = Observer()
        self.handler = DropFolderHandler(vault_path, monitored_folder)

    def check_for_updates(self) -> list:
        # This method is overridden to work with the observer pattern
        # The actual file monitoring happens in the observer
        return []

    def create_action_file(self, item) -> Path:
        # This is handled by the DropFolderHandler
        pass

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
            self.logger.info('File system watcher stopped')
        finally:
            self.observer.join()
```

### 3. Orchestrator Integration

The orchestrator component ties the watcher and Claude Code together. **UPDATED**: Now includes proper file locking, multi-folder monitoring, and state persistence.

See the complete implementation in `/src/orchestrator/orchestrator.py`.

Key improvements:
- **Global processing lock** prevents concurrent Claude runs
- **Multi-folder monitoring**: Inbox, Needs_Action, Approved
- **Priority-based processing**: Approved > Needs_Action > Inbox
- **Persistent state** survives crashes
- **Instruction file pattern** for Claude Code integration
- **Comprehensive error handling and logging**

```python
# Simplified example - see full implementation in src/orchestrator/orchestrator.py
import subprocess
import time
from pathlib import Path
import fcntl

class Orchestrator:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.approved = self.vault_path / 'Approved'
        self.inbox = self.vault_path / 'Inbox'
        self.processing_lock = self.vault_path / '.state' / 'processing.lock'

    def _acquire_processing_lock(self) -> bool:
        """Acquire global lock to prevent concurrent processing"""
        try:
            self.lock_fd = open(self.processing_lock, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False

    def _trigger_claude_processing(self, context: str) -> bool:
        """Trigger Claude Code with instruction file"""
        instruction_file = self.vault_path / '.claude_instruction.md'
        instruction_file.write_text(f"# Task\n{context}\n\n[Full instructions...]")

        result = subprocess.run([
            'claude', '--cwd', str(self.vault_path),
            f'Please read and execute the instructions in .claude_instruction.md'
        ], capture_output=True, text=True, timeout=300)

        instruction_file.unlink()
        return result.returncode == 0

    def check_and_trigger(self):
        """Check for files and trigger Claude if needed"""
        if not self._acquire_processing_lock():
            return  # Another instance is running

        try:
            # Get files from all monitored folders
            approved_files = list(self.approved.glob('*.md'))
            needs_action_files = list(self.needs_action.glob('*.md'))
            inbox_files = list(self.inbox.glob('*.md'))

            # Process in priority order
            if approved_files:
                self._trigger_claude_processing(f'Execute {len(approved_files)} approved actions')
            if needs_action_files:
                self._trigger_claude_processing(f'Process {len(needs_action_files)} items')
            if inbox_files:
                self._trigger_claude_processing(f'Process {len(inbox_files)} inbox items')
        finally:
            self._release_processing_lock()
```

### 4. Watchdog Process for Reliability

**UPDATED**: Production-ready watchdog with restart limiting, alerting, and graceful shutdown.

See the complete implementation in `/src/orchestrator/watchdog.py`.

Key features:
- **Process monitoring** using PID files and psutil
- **Auto-restart** with restart count limiting (max 5/hour)
- **Human alerting** via ALERTS.md file
- **Graceful shutdown** of all processes
- **Comprehensive logging**

```python
# Simplified example - see full implementation in src/orchestrator/watchdog.py
import subprocess
import psutil
from pathlib import Path

class ProcessWatchdog:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.pid_dir = Path('/tmp/ai_employee_pids')
        self.restart_counts = {}
        self.max_restarts = 5  # Per hour

    def _is_process_running(self, process_name: str) -> bool:
        """Check if process is running via PID file"""
        pid_file = self.pid_dir / f'{process_name}.pid'
        if not pid_file.exists():
            return False

        try:
            pid = int(pid_file.read_text().strip())
            return psutil.pid_exists(pid)
        except:
            return False

    def _start_process(self, process_name: str) -> int:
        """Start a process and save its PID"""
        proc = subprocess.Popen(
            self.processes[process_name]['command'],
            start_new_session=True  # Detach from parent
        )
        pid_file = self.pid_dir / f'{process_name}.pid'
        pid_file.write_text(str(proc.pid))
        return proc.pid

    def check_and_restart(self):
        """Check all processes and restart if needed"""
        for name in self.processes:
            if not self._is_process_running(name):
                if self.restart_counts[name] < self.max_restarts:
                    self._start_process(name)
                    self.restart_counts[name] += 1
                    self._notify_human(f'{name} restarted')
                else:
                    self._notify_human(f'{name} failed {self.max_restarts} times')
```

### 5. Process Management

For deployment, consider using process managers like PM2:

```bash
# Install PM2
npm install -g pm2

# Start the file system watcher
pm2 start filesystem_watcher.py --name fs-watcher --interpreter python3

# Start the orchestrator
pm2 start orchestrator.py --name orchestrator --interpreter python3

# Save the process list to start on boot
pm2 save
pm2 startup
```

### 6. Security Considerations

- Monitor only designated safe directories to prevent unauthorized file access
- Validate file types before processing
- Implement rate limiting to prevent overwhelming Claude Code
- Use secure file permissions for the vault directory

## Implementation Phases

### Phase 1: Infrastructure Setup
- Configure Obsidian vault with required files and folders
- Set up Claude Code workspace
- Create basic file structure

### Phase 2: Watcher Implementation
- Implement chosen watcher (Gmail or File System)
- Configure monitoring and file creation
- Test external source integration

### Phase 3: Agent Skills Development
- Create core file management skills
- Develop decision-making skills
- Implement approval workflow

### Phase 4: Integration and Testing
- Connect all components
- Test end-to-end workflows
- Validate Bronze Tier requirements are met

## Security Considerations

- Credentials stored securely using environment variables
- Human-in-the-loop for sensitive actions
- Audit logging for all AI actions
- Development mode with dry-run capabilities

## Success Criteria

The Bronze Tier implementation will be successful when:
- Claude Code can read from and write to the Obsidian vault
- At least one watcher is monitoring and creating action files
- Basic file movement workflow (Inbox → Needs_Action → Done) functions correctly
- All functionality is implemented as modular Agent Skills
- Dashboard.md updates reflect system activity
- **Multiple files can be processed concurrently without corruption**
- **System recovers automatically from process crashes**
- **No duplicate processing occurs after restart**
- **File locking prevents race conditions**
- **Comprehensive logging enables debugging**
- **Human-in-the-loop approval workflow is complete (Pending_Approval → Approved → Done)**

## Implementation Status

### ✅ Completed Components

1. **Vault Structure** - All required folders created with proper permissions
2. **Base Watcher** - Abstract class with state persistence, file locking, and sanitization
3. **File System Watcher** - Production-ready with watchdog library integration
4. **Orchestrator** - Multi-folder monitoring with global locking and priority processing
5. **Watchdog** - Process monitoring with auto-restart and alerting
6. **Setup Scripts** - Automated setup, start, and stop scripts
7. **Documentation** - Complete architecture documentation and testing scenarios

### 🔄 Next Steps

1. **Test the complete workflow** with real files
2. **Verify Claude Code integration** - May need adjustment based on actual CLI behavior
3. **Create Agent Skills** for common tasks (email drafting, file categorization, etc.)
4. **Add Business_Goals.md** template for weekly audits
5. **Implement basic MCP server** for email sending (Silver tier preparation)

## Quick Start

```bash
# 1. Setup
./setup.sh

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Start the system
./start.sh

# 4. Test by dropping a file
echo "Test task" > ai_employee_vault/Inbox/test_task.md

# 5. Monitor logs
tail -f ai_employee_vault/Logs/*.log

# 6. Stop the system
./stop.sh
```

## Troubleshooting

### Issue: Claude Code not found
**Solution**: Ensure Claude Code CLI is installed and in PATH
```bash
which claude
# If not found, install Claude Code
```

### Issue: Processes not starting
**Solution**: Check logs and permissions
```bash
cat ai_employee_vault/Logs/watchdog_*.log
ls -la /tmp/ai_employee_pids/
```

### Issue: Files not being processed
**Solution**: Check orchestrator logs and processing lock
```bash
cat ai_employee_vault/Logs/orchestrator_*.log
ls -la ai_employee_vault/.state/processing.lock
```

### Issue: Duplicate processing
**Solution**: Check state files
```bash
cat ai_employee_vault/.state/filesystem_watcher_state.json
cat ai_employee_vault/.state/orchestrator_state.json
```