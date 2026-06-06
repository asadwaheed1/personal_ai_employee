#!/usr/bin/env python3
"""
Run Meta Watcher - Entry point for monitoring Facebook and Instagram
Used for Gold Tier 2.2: Facebook + Instagram Integration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.watchers.meta_watcher import MetaWatcher

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_meta_watcher.py <vault_path> [check_interval]")
        sys.exit(1)
        
    vault_path = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 900
    
    print(f"Starting Meta Watcher for vault: {vault_path}")
    print(f"Check interval: {check_interval}s")
    
    watcher = MetaWatcher(vault_path, check_interval)
    
    try:
        watcher.run()
    except KeyboardInterrupt:
        print("\nMeta Watcher stopped by user")
    except Exception as e:
        print(f"\nMeta Watcher error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
