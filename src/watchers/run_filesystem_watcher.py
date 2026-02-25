"""
Main entry point for running the File System Watcher
"""

import sys
from pathlib import Path

# Add parent directory to path to import base_watcher
sys.path.insert(0, str(Path(__file__).parent))

from filesystem_watcher import FileSystemWatcher


def main():
    if len(sys.argv) < 3:
        print('Usage: python run_filesystem_watcher.py <vault_path> <monitored_folder> [check_interval]')
        print('Example: python run_filesystem_watcher.py /path/to/vault /path/to/drop_folder 5')
        sys.exit(1)

    vault_path = sys.argv[1]
    monitored_folder = sys.argv[2]
    check_interval = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    print(f'Starting File System Watcher...')
    print(f'Vault: {vault_path}')
    print(f'Monitoring: {monitored_folder}')
    print(f'Check interval: {check_interval}s')

    watcher = FileSystemWatcher(vault_path, monitored_folder, check_interval)
    watcher.run()


if __name__ == '__main__':
    main()
