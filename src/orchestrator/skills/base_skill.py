"""
Base skill class for Bronze tier agent skills
"""

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class BaseSkill:
    """Base class for all Bronze tier skills"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the skill"""
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f'skills_{datetime.now().strftime("%Y-%m-%d")}.log'

        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill with given parameters"""
        try:
            self.logger.info(f"Executing {self.__class__.__name__} with params: {params}")
            result = self._execute_impl(params)
            self.logger.info(f"Skill execution completed successfully")
            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Skill execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _execute_impl(self, params: Dict[str, Any]) -> Any:
        """Implementation of the skill logic - to be overridden by subclasses"""
        raise NotImplementedError

    def read_file(self, file_path: Path) -> str:
        """Safely read a file"""
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            raise

    def write_file(self, file_path: Path, content: str):
        """Safely write a file"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            raise

    def move_file(self, source: Path, destination: Path):
        """Safely move a file"""
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
        except Exception as e:
            self.logger.error(f"Failed to move file from {source} to {destination}: {e}")
            raise

    def _log_audit(self, action_type: str, target: str, result: str = 'success', platform: str = 'system', details: Dict = None, error: str = None):
        """Log structured audit entry using AuditLoggerSkill pattern"""
        try:
            from .audit_logger import AuditLoggerSkill
        except ImportError:
            try:
                from audit_logger import AuditLoggerSkill
            except ImportError:
                self.logger.warning("AuditLoggerSkill not found, logging locally only")
                return

        try:
            logger_skill = AuditLoggerSkill(str(self.vault_path))
            params = {
                "action_type": action_type,
                "actor": self.__class__.__name__,
                "platform": platform,
                "target": target,
                "result": result,
                "details": details or {},
                "error": error,
                "approval_status": "manual" # Base assumption for skills triggered via process_approved
            }
            logger_skill.execute(params)
        except Exception as e:
            self.logger.error(f"Failed to log audit entry: {e}")


def run_skill(skill_class, params_json: str):
    """Run a skill from command line"""
    try:
        params = json.loads(params_json)
        vault_path = params.get('vault_path')

        if not vault_path:
            raise ValueError("vault_path is required")

        skill = skill_class(vault_path)
        result = skill.execute(params)

        print(json.dumps(result, indent=2))
        sys.exit(0 if result['success'] else 1)

    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)