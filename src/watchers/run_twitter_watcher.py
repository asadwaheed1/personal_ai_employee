#!/usr/bin/env python3
"""
Run Twitter Watcher - Entry point for monitoring Twitter/X mentions
Used for Gold Tier 2.1: Twitter/X Integration
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.watchers.twitter_watcher import TwitterWatcher

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_twitter_watcher.py <vault_path> [check_interval]")
        sys.exit(1)

    vault_path = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 900  # Default 15 min

    print(f"Starting Twitter Watcher for vault: {vault_path}")
    print(f"Check interval: {check_interval}s")

    watcher = TwitterWatcher(vault_path, check_interval)
    
    try:
        watcher.run()
    except KeyboardInterrupt:
        print("\nTwitter Watcher stopped by user")
    except Exception as e:
        print(f"\nTwitter Watcher error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
