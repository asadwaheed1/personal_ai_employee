#!/usr/bin/env python3
"""
MCP Processor - Executes MCP action files via Claude Code's MCP servers

This module processes MCP action files created by agent skills and executes
them through Claude Code's MCP servers, fulfilling the Silver Tier requirement
of using MCP for external actions.
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import subprocess
import sys
import os
import tempfile


class MCPProcessor:
    """
    Processes MCP action files by executing them through Claude Code's MCP servers.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'

        # Setup logging
        self.logger = self._setup_logging()

        # MCP server mappings
        self.mcp_servers = {
            'gmail': self._execute_gmail_action,
            'linkedin': self._execute_linkedin_action,
            'filesystem': self._execute_filesystem_action,
            # Add more MCP servers as needed
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for MCP processor"""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f'mcp_processor_{datetime.now().strftime("%Y-%m-%d")}.log'

        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        logger = logging.getLogger('MCPProcessor')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        return logger

    def process_pending_actions(self) -> Dict[str, Any]:
        """
        Process all pending MCP action files in Needs_Action folder

        Returns:
            Dictionary with processing results
        """
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }

        # Find all MCP action files (JSON files with mcp_server field)
        mcp_files = []
        for file_path in self.needs_action.glob('MCP_*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    if isinstance(content, dict) and 'mcp_server' in content:
                        mcp_files.append((file_path, content))
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Failed to parse MCP action file {file_path}: {e}")
                results['errors'].append(f"Failed to parse {file_path}: {e}")

        self.logger.info(f"Found {len(mcp_files)} MCP action files to process")

        for file_path, action_data in mcp_files:
            try:
                self.logger.info(f"Processing MCP action: {file_path.name}")

                # Execute the action via the appropriate MCP server
                execution_result = self._execute_action(action_data)

                # Update the action file with results
                action_data['result'] = execution_result
                action_data['executed_at'] = datetime.now().isoformat()
                action_data['status'] = 'completed' if execution_result.get('success', False) else 'failed'

                # Write updated action file to Done folder
                done_path = self.done / f"EXECUTED_{file_path.name}"
                with open(done_path, 'w', encoding='utf-8') as f:
                    json.dump(action_data, f, indent=2)

                # Remove original file from Needs_Action
                file_path.unlink()

                results['processed'] += 1
                if execution_result.get('success', False):
                    results['successful'] += 1
                    self.logger.info(f"Successfully executed action: {file_path.name}")
                else:
                    results['failed'] += 1
                    self.logger.error(f"Failed to execute action: {file_path.name}, error: {execution_result.get('error', 'Unknown error')}")

            except Exception as e:
                results['failed'] += 1
                error_msg = f"Error processing {file_path.name}: {str(e)}"
                results['errors'].append(error_msg)
                self.logger.error(error_msg, exc_info=True)

                # Move to Done with error status
                action_data['result'] = {'success': False, 'error': str(e)}
                action_data['executed_at'] = datetime.now().isoformat()
                action_data['status'] = 'failed'

                done_path = self.done / f"FAILED_{file_path.name}"
                try:
                    with open(done_path, 'w', encoding='utf-8') as f:
                        json.dump(action_data, f, indent=2)
                    file_path.unlink()
                except Exception as cleanup_error:
                    self.logger.error(f"Failed to cleanup failed action file {file_path.name}: {cleanup_error}")

        return results

    def _execute_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an MCP action by calling the appropriate MCP server

        Args:
            action_data: Dictionary containing MCP action details

        Returns:
            Dictionary with execution result
        """
        mcp_server = action_data.get('mcp_server')
        tool = action_data.get('tool')
        params = action_data.get('params', {})

        if not mcp_server:
            return {'success': False, 'error': 'Missing MCP server'}

        if not tool:
            return {'success': False, 'error': 'Missing tool'}

        # Check if MCP server is supported
        if mcp_server not in self.mcp_servers:
            return {'success': False, 'error': f'Unsupported MCP server: {mcp_server}'}

        try:
            # Call the appropriate MCP server method
            executor = self.mcp_servers[mcp_server]
            result = executor(tool, params)
            return result
        except Exception as e:
            self.logger.error(f"Error executing {mcp_server}.{tool}: {e}", exc_info=True)
            return {'success': False, 'error': f'Execution error: {str(e)}'}

    def _execute_gmail_action(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Gmail MCP actions via Claude Code's Gmail MCP server

        Args:
            tool: The Gmail tool to execute (send_email, modify_email, trash_email, etc.)
            params: Parameters for the tool

        Returns:
            Dictionary with execution result
        """
        try:
            # Create a temporary Claude instruction file to execute the Gmail action
            instruction = self._create_gmail_instruction(tool, params)

            # Execute via Claude Code with MCP server
            result = self._execute_claude_with_mcp(instruction, 'gmail')

            return result

        except Exception as e:
            self.logger.error(f"Gmail action execution failed: {e}", exc_info=True)
            return {'success': False, 'error': f'Gmail execution error: {str(e)}'}

    def _execute_linkedin_action(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LinkedIn MCP actions via Claude Code's LinkedIn MCP server
        """
        try:
            instruction = self._create_linkedin_instruction(tool, params)
            result = self._execute_claude_with_mcp(instruction, 'linkedin')
            return result
        except Exception as e:
            self.logger.error(f"LinkedIn action execution failed: {e}", exc_info=True)
            return {'success': False, 'error': f'LinkedIn execution error: {str(e)}'}

    def _execute_filesystem_action(self, tool: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute filesystem MCP actions via Claude Code's filesystem MCP server
        """
        try:
            instruction = self._create_filesystem_instruction(tool, params)
            result = self._execute_claude_with_mcp(instruction, 'filesystem')
            return result
        except Exception as e:
            self.logger.error(f"Filesystem action execution failed: {e}", exc_info=True)
            return {'success': False, 'error': f'Filesystem execution error: {str(e)}'}

    def _create_gmail_instruction(self, tool: str, params: Dict[str, Any]) -> str:
        """
        Create Claude instruction for Gmail MCP actions
        """
        if tool == 'send_email':
            return f"""
Please execute a Gmail send_email action using the MCP server.

Parameters:
- to: {params.get('to', 'Not specified')}
- subject: {params.get('subject', 'Not specified')}
- body: {params.get('body', 'Not specified')[:200]}...  # Truncated for brevity

Use Claude's Gmail MCP server to send this email.
Return the result of the operation.
"""
        elif tool == 'modify_email':
            return f"""
Please execute a Gmail modify_email action using the MCP server.

Parameters:
- message_id: {params.get('message_id', 'Not specified')}
- removeLabelIds: {params.get('removeLabelIds', [])}
- addLabelIds: {params.get('addLabelIds', [])}

Use Claude's Gmail MCP server to modify the email labels.
Return the result of the operation.
"""
        elif tool == 'trash_email':
            return f"""
Please execute a Gmail trash_email action using the MCP server.

Parameters:
- message_id: {params.get('message_id', 'Not specified')}

Use Claude's Gmail MCP server to move the email to trash.
Return the result of the operation.
"""
        elif tool == 'send_reply':
            return f"""
Please execute a Gmail send_reply action using the MCP server.

Parameters:
- message_id: {params.get('message_id', 'Not specified')}
- thread_id: {params.get('thread_id', 'Not specified')}
- to: {params.get('to', 'Not specified')}
- subject: {params.get('subject', 'Not specified')}
- body: {params.get('body', 'Not specified')[:200]}...  # Truncated for brevity

Use Claude's Gmail MCP server to send this reply.
Return the result of the operation.
"""
        else:
            return f"""
Please execute a Gmail {tool} action using the MCP server.

Parameters: {json.dumps(params)}

Use Claude's Gmail MCP server to perform this action.
Return the result of the operation.
"""

    def _create_linkedin_instruction(self, tool: str, params: Dict[str, Any]) -> str:
        """
        Create Claude instruction for LinkedIn MCP actions
        """
        return f"""
Please execute a LinkedIn {tool} action using the MCP server.

Parameters: {json.dumps(params)}

Use Claude's LinkedIn MCP server to perform this action.
Return the result of the operation.
"""

    def _create_filesystem_instruction(self, tool: str, params: Dict[str, Any]) -> str:
        """
        Create Claude instruction for filesystem MCP actions
        """
        return f"""
Please execute a filesystem {tool} action using the MCP server.

Parameters: {json.dumps(params)}

Use Claude's filesystem MCP server to perform this action.
Return the result of the operation.
"""

    def _execute_claude_with_mcp(self, instruction: str, mcp_server: str) -> Dict[str, Any]:
        """
        Execute Claude instruction that uses MCP server

        Args:
            instruction: Claude instruction that uses MCP
            mcp_server: Name of the MCP server to use

        Returns:
            Dictionary with execution result
        """
        try:
            # Create a temporary instruction file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(f"""# MCP Action Execution

**Generated**: {datetime.now().isoformat()}
**MCP Server**: {mcp_server}
**Action**: {instruction}

## Task
{instruction}

## Expected Result
Execute the specified MCP action and return the result.
""")
                temp_file_path = temp_file.name

            try:
                # Execute Claude Code with the instruction
                # Using --dangerously-skip-permissions to allow MCP server access
                result = subprocess.run(
                    ['claude', '--dangerously-skip-permissions', f'Please execute the instruction in {temp_file_path}'],
                    cwd=str(self.vault_path),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )

                if result.returncode == 0:
                    self.logger.info(f"MCP action executed successfully via {mcp_server}")
                    # Parse the result to extract success/failure info
                    output = result.stdout
                    success = "error" not in output.lower() and "failed" not in output.lower()
                    return {
                        'success': success,
                        'output': output[:500],  # Limit output length
                        'returncode': result.returncode
                    }
                else:
                    self.logger.error(f"MCP action failed via {mcp_server}: {result.stderr}")
                    return {
                        'success': False,
                        'error': result.stderr[:500],  # Limit error length
                        'output': result.stdout[:500],
                        'returncode': result.returncode
                    }

            finally:
                # Clean up temporary file
                if Path(temp_file_path).exists():
                    Path(temp_file_path).unlink()

        except subprocess.TimeoutExpired:
            self.logger.error(f"MCP action timed out via {mcp_server}")
            return {'success': False, 'error': 'Timeout executing MCP action'}
        except FileNotFoundError:
            self.logger.error("Claude Code CLI not found")
            return {'success': False, 'error': 'Claude Code CLI not found. Please ensure it is installed and in PATH.'}
        except Exception as e:
            self.logger.error(f"Error executing MCP action via {mcp_server}: {e}", exc_info=True)
            return {'success': False, 'error': f'Exception executing MCP action: {str(e)}'}

    def process_single_action_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Process a single MCP action file

        Args:
            file_path: Path to the MCP action file

        Returns:
            Dictionary with execution result
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                action_data = json.load(f)

            if not isinstance(action_data, dict) or 'mcp_server' not in action_data:
                return {'success': False, 'error': 'Invalid MCP action file format'}

            # Execute the action
            execution_result = self._execute_action(action_data)

            # Update the action file with results
            action_data['result'] = execution_result
            action_data['executed_at'] = datetime.now().isoformat()
            action_data['status'] = 'completed' if execution_result.get('success', False) else 'failed'

            # Move to Done folder
            done_path = self.done / f"PROCESSED_{file_path.name}"
            with open(done_path, 'w', encoding='utf-8') as f:
                json.dump(action_data, f, indent=2)

            # Remove original
            file_path.unlink()

            return execution_result

        except Exception as e:
            error_result = {'success': False, 'error': str(e)}
            # Log error and move to failed
            try:
                action_data = {'error': str(e), 'original_file': str(file_path)}
                action_data['result'] = error_result
                action_data['executed_at'] = datetime.now().isoformat()
                action_data['status'] = 'failed'

                failed_path = self.done / f"FAILED_{file_path.name}"
                with open(failed_path, 'w', encoding='utf-8') as f:
                    json.dump(action_data, f, indent=2)

                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors

            return error_result


def main():
    """Command line interface for MCP processor"""
    if len(sys.argv) < 2:
        print("Usage: python mcp_processor.py <vault_path> [single_file]")
        print("  vault_path: Path to the vault directory")
        print("  single_file: Optional path to process a single MCP action file")
        sys.exit(1)

    vault_path = sys.argv[1]

    if len(sys.argv) > 2:
        # Process a single file
        file_path = Path(sys.argv[2])
        if not file_path.exists():
            print(f"File not found: {file_path}")
            sys.exit(1)

        processor = MCPProcessor(vault_path)
        result = processor.process_single_action_file(file_path)
        print(f"Result: {json.dumps(result, indent=2)}")
    else:
        # Process all pending actions
        processor = MCPProcessor(vault_path)
        results = processor.process_pending_actions()
        print(f"Processing results: {json.dumps(results, indent=2)}")


if __name__ == '__main__':
    main()