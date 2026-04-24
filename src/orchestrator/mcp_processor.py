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
import signal


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
                
                success = execution_result.get('success', False)
                action_data['status'] = 'completed' if success else 'failed'

                if not success and action_data.get('mcp_server') == 'gmail':
                    # Gold Tier: Queue failed Gmail actions for retry if error is likely transient
                    error_msg = str(execution_result.get('error', '')).lower()
                    transient_errors = ['timeout', 'token failed', 'oauth', 'connection', 'network', 'could not connect']
                    is_transient = any(err in error_msg for err in transient_errors)
                    
                    if is_transient:
                        self.logger.warning(f"Transient Gmail error detected, queuing for retry: {file_path.name}")
                        action_data['status'] = 'queued'
                        queued_filename = file_path.name.replace('MCP_', 'QUEUED_MCP_GMAIL_')
                        if 'QUEUED_MCP_GMAIL_' not in queued_filename:
                            queued_filename = f"QUEUED_MCP_GMAIL_{file_path.name}"
                        
                        queued_path = self.needs_action / queued_filename
                        with open(queued_path, 'w', encoding='utf-8') as f:
                            json.dump(action_data, f, indent=2)
                        
                        if file_path.exists():
                            file_path.unlink()
                        
                        results['failed'] += 1
                        continue

                # Write updated action file to Done folder
                done_path = self.done / f"EXECUTED_{file_path.name}"
                with open(done_path, 'w', encoding='utf-8') as f:
                    json.dump(action_data, f, indent=2)

                # Remove original file from Needs_Action (ignore if already moved/removed)
                if file_path.exists():
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
        Execute filesystem MCP actions via Claude Code's filesystem MCP server.
        Post-processes result for data-returning tools (read/list/search/info)
        where Claude outputs the data directly rather than a success confirmation.
        """
        # Tools that return data rather than a confirmation string
        DATA_TOOLS = {'read_file', 'list_directory', 'search_files', 'get_file_info', 'read_multiple_files', 'list_allowed_directories'}

        try:
            instruction = self._create_filesystem_instruction(tool, params)
            result = self._execute_claude_with_mcp(instruction, 'filesystem')

            # For data-returning tools: if we got output with returncode 0, treat as success
            # even when the output doesn't match generic success signal patterns
            if not result.get('success') and tool in DATA_TOOLS:
                output = result.get('output', result.get('error', ''))
                if output and result.get('returncode', -1) == 0:
                    self.logger.info(f"Filesystem {tool} returned data — treating as success")
                    return {'success': True, 'output': output, 'returncode': 0}

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
            message_id = params.get('messageId', params.get('message_id', 'Not specified'))
            remove_labels = params.get('removeLabelIds', params.get('removeLabels', []))
            add_labels = params.get('addLabelIds', params.get('addLabels', []))
            return f"""
Please execute Gmail label modification using the gmail_modify_labels MCP tool.

Required parameters:
- messageId: {message_id}
- removeLabels: {remove_labels}
- addLabels: {add_labels}

Use the gmail_modify_labels tool from the Gmail MCP server to modify message labels.
Return the operation result.
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
- messageId: {params.get('messageId', params.get('message_id', 'Not specified'))}
- threadId: {params.get('threadId', params.get('thread_id', 'Not specified'))}
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
        Create Claude instruction for filesystem MCP actions.
        Maps to @modelcontextprotocol/server-filesystem tool names exactly.
        """
        if tool == 'read_file':
            return f"""Use the filesystem MCP tool `read_file` to read the file at path: {params.get('path', 'Not specified')}
Return the file contents. If the file does not exist, say so explicitly."""

        elif tool == 'write_file':
            return f"""Use the filesystem MCP tool `write_file` to write a file.
- path: {params.get('path', 'Not specified')}
- content: {params.get('content', '')}
Confirm the file was written successfully."""

        elif tool == 'list_directory':
            return f"""Use the filesystem MCP tool `list_directory` to list contents of: {params.get('path', 'Not specified')}
Return the directory listing."""

        elif tool == 'create_directory':
            return f"""Use the filesystem MCP tool `create_directory` to create directory at: {params.get('path', 'Not specified')}
Confirm the directory was created."""

        elif tool == 'move_file':
            return f"""Use the filesystem MCP tool `move_file` to move/rename a file.
- source: {params.get('source', 'Not specified')}
- destination: {params.get('destination', 'Not specified')}
Confirm the file was moved successfully."""

        elif tool == 'search_files':
            return f"""Use the filesystem MCP tool `search_files` to search for files.
- path: {params.get('path', 'Not specified')}
- pattern: {params.get('pattern', 'Not specified')}
Return the list of matching files."""

        elif tool == 'delete_file':
            return f"""Use the filesystem MCP tool `delete_file` to delete the file at: {params.get('path', 'Not specified')}
Confirm the file was deleted."""

        elif tool == 'get_file_info':
            return f"""Use the filesystem MCP tool `get_file_info` to get metadata for: {params.get('path', 'Not specified')}
Return file size, modification time, and type."""

        else:
            return f"""Use the filesystem MCP tool `{tool}` with these parameters: {json.dumps(params)}
Confirm the operation completed successfully."""

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
                # Run from project root (not vault) so .claude/config.json and .mcp.json are accessible
                project_root = self.vault_path.parent
                process = subprocess.Popen(
                    ['claude', '--dangerously-skip-permissions', f'Please execute the instruction in {temp_file_path}'],
                    cwd=str(project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True
                )

                try:
                    stdout, stderr = process.communicate(timeout=300)
                except subprocess.TimeoutExpired:
                    # Kill entire process group (includes gmail-mcp-server children)
                    try:
                        pgid = os.getpgid(process.pid)
                        os.killpg(pgid, signal.SIGTERM)
                    except OSError:
                        process.terminate()
                    # Drain pipes — required to reap zombie and unblock parent
                    try:
                        stdout, stderr = process.communicate(timeout=10)
                    except subprocess.TimeoutExpired:
                        try:
                            pgid = os.getpgid(process.pid)
                            os.killpg(pgid, signal.SIGKILL)
                        except OSError:
                            process.kill()
                        stdout, stderr = process.communicate()
                    self.logger.error(f"MCP action timed out via {mcp_server}")
                    return {'success': False, 'error': 'Timeout executing MCP action'}

                if process.returncode == 0:
                    output = stdout.strip()
                    try:
                        # Strict: attempt JSON parse for robust success/failure
                        result_json = json.loads(output)
                        if not isinstance(result_json, dict):
                            raise ValueError('MCP tool did not return a JSON object')
                        if not result_json.get('success', False):
                            self.logger.error(f"MCP JSON failure response: {result_json}")
                            return {**result_json, 'returncode': process.returncode}
                        self.logger.info(f"MCP action executed successfully via {mcp_server} [structured response]")
                        return {**result_json, 'returncode': process.returncode}
                    except Exception:
                        output_lower = output.lower()

                        # Check for explicit success indicators in plain text
                        success_signals = [
                            'successfully',
                            'successful',
                            'success',
                            'sent successfully',
                            'executed successfully',
                            'message id:',
                            'completed successfully',
                            'auth verified',
                            'authentication healthy',
                            'token refresh work',
                            # Gmail plain-text responses
                            'marked as read',
                            'label removed',
                            'reply sent',
                            'draft created',
                            'mcp action marked complete',
                            'has been marked',
                            'been archived',
                            # Filesystem plain-text responses
                            'file written',
                            'file created',
                            'file moved',
                            'file deleted',
                            'directory created',
                            'directory listing',
                            'directory contents',
                            'file contents',
                            'file size',
                            'written to',
                            'moved to',
                            'deleted successfully',
                            'created successfully',
                            '[file]',
                            '[directory]',
                            'size:',
                            'modified:',
                        ]
                        has_success_signal = any(signal in output_lower for signal in success_signals)

                        failure_signals = [
                            'action failed',
                            'could not',
                            'token failed',
                            'oauth',
                            'not executed',
                            'gmail mcp tool',
                            'gmail mcp server',
                            "isn't available",
                            'not available',
                            'request to https://oauth2.googleapis.com/token failed',
                            'error:'
                        ]
                        has_failure_signal = any(signal in output_lower for signal in failure_signals)

                        # Explicit: fail if missing JSON AND mentioned missing MCP tool/server
                        if has_failure_signal or 'no gmail mcp' in output_lower:
                            self.logger.error(f"MCP action reported explicit failure via {mcp_server}")
                            return {
                                'success': False,
                                'error': output[:500],
                                'output': output[:500],
                                'returncode': process.returncode
                            }

                        # Accept plain-text success if clear success indicators present
                        if has_success_signal:
                            self.logger.info(f"MCP action executed successfully via {mcp_server} [plain-text success]")
                            return {
                                'success': True,
                                'output': output[:500],
                                'returncode': process.returncode
                            }

                        self.logger.error(f"MCP action did not return recognizable JSON or success signal, treated as failure")
                        return {
                            'success': False,
                            'error': output[:500],
                            'output': output[:500],
                            'returncode': process.returncode
                        }

                self.logger.error(f"MCP action failed via {mcp_server}: {stderr}")
                return {
                    'success': False,
                    'error': stderr[:500],  # Limit error length
                    'output': stdout[:500],
                    'returncode': process.returncode
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

    def validate_gmail_mcp_auth(self) -> Dict[str, Any]:
        """Run non-destructive Gmail MCP auth preflight check."""
        try:
            instruction = """
Please verify Gmail MCP authentication by performing a non-destructive profile check.
Use Gmail MCP tool to read mailbox profile only (no write actions).
Return success only if MCP auth and token refresh work.
"""
            result = self._execute_claude_with_mcp(instruction, 'gmail')

            if result.get('success'):
                self.logger.info('Gmail MCP preflight check passed')
            else:
                self.logger.error(f"Gmail MCP preflight check failed: {result.get('error', result.get('output', 'Unknown error'))}")

            return result
        except Exception as e:
            self.logger.error(f'Gmail MCP preflight check exception: {e}', exc_info=True)
            return {'success': False, 'error': str(e)}

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