"""
GOD-TIER AUTOBUY STACK - OpenInterpreter Shell Controller
Production-ready shell automation and system integration
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from interpreter import interpreter
import psutil
import sqlite3

class SecurityManager:
    """Security manager for shell operations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.safe_mode = config.get('interpreter', {}).get('safe_mode', True)
        self.allowed_commands = config.get('interpreter', {}).get('shell', {}).get('allowed_commands', [])
        self.restricted_paths = config.get('interpreter', {}).get('shell', {}).get('restricted_paths', [])
        self.logger = logging.getLogger(__name__)

    def is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed"""
        if not self.safe_mode:
            return True

        command_parts = command.strip().split()
        if not command_parts:
            return False

        base_command = command_parts[0]

        # Check if base command is in allowed list
        if base_command in self.allowed_commands:
            return True

        # Check for dangerous commands
        dangerous_commands = [
            'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs',
            'sudo', 'su', 'chmod', 'chown', 'passwd',
            'iptables', 'netsh', 'reg', 'regedit'
        ]

        if base_command in dangerous_commands:
            self.logger.warning(f"Blocked dangerous command: {base_command}")
            return False

        return True

    def is_path_allowed(self, path: str) -> bool:
        """Check if path access is allowed"""
        if not self.safe_mode:
            return True

        path_obj = Path(path).resolve()

        # Check against restricted paths
        for restricted in self.restricted_paths:
            restricted_path = Path(restricted).resolve()
            try:
                path_obj.relative_to(restricted_path)
                self.logger.warning(f"Blocked access to restricted path: {path}")
                return False
            except ValueError:
                continue

        return True

class PythonExecutor:
    """Python code executor with safety checks"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.security = SecurityManager(config)
        self.logger = logging.getLogger(__name__)

        # Python environment settings
        self.python_version = config.get('interpreter', {}).get('python', {}).get('version', '3.11')
        self.virtual_env = config.get('interpreter', {}).get('python', {}).get('virtual_env', 'autobuy_env')

        # Execution limits
        self.max_output = config.get('interpreter', {}).get('max_output', 5000)
        self.timeout = config.get('interpreter', {}).get('timeout', 300)

    async def execute_python_code(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Python code safely"""
        try:
            # Create temporary file for code execution
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            try:
                # Prepare execution environment
                env = os.environ.copy()
                if context:
                    env.update({k: str(v) for k, v in context.items()})

                # Execute Python code
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    env=env
                )

                # Process output
                output = result.stdout
                error = result.stderr

                # Limit output size
                if len(output) > self.max_output:
                    output = output[:self.max_output] + "\n... (output truncated)"

                if len(error) > self.max_output:
                    error = error[:self.max_output] + "\n... (error truncated)"

                return {
                    "success": result.returncode == 0,
                    "output": output,
                    "error": error,
                    "return_code": result.returncode,
                    "execution_time": datetime.now().isoformat()
                }

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Execution timed out after {self.timeout} seconds",
                "execution_time": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "execution_time": datetime.now().isoformat()
            }

    async def install_package(self, package_name: str) -> Dict[str, Any]:
        """Install Python package"""
        try:
            if not self.security.is_command_allowed(f"pip install {package_name}"):
                return {
                    "success": False,
                    "error": "Package installation not allowed in safe mode"
                }

            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name],
                capture_output=True,
                text=True,
                timeout=120
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Package installation failed: {str(e)}"
            }

class SystemMonitor:
    """System monitoring and resource management"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            # CPU information
            cpu_info = {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }

            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            }

            # Disk information
            disk = psutil.disk_usage('/')
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }

            # Network information
            network = psutil.net_io_counters()
            network_info = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }

            return {
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"System info collection failed: {e}")
            return {"error": str(e)}

    async def get_running_processes(self) -> List[Dict[str, Any]]:
        """Get running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)

            return processes[:20]  # Return top 20 processes

        except Exception as e:
            self.logger.error(f"Process listing failed: {e}")
            return []

class DatabaseManager:
    """Database operations for result storage"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db_path = config.get('database', {}).get('storage', {}).get('path', 'data/autobuy.db')

        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def store_execution_result(self, session_id: str, result: Dict[str, Any]) -> bool:
        """Store execution result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Insert result
            cursor.execute(
                'INSERT INTO execution_results (session_id, result_data) VALUES (?, ?)',
                (session_id, json.dumps(result))
            )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            self.logger.error(f"Database storage failed: {e}")
            return False

    async def get_execution_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get execution history for session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                'SELECT result_data, created_at FROM execution_results WHERE session_id = ? ORDER BY created_at DESC',
                (session_id,)
            )

            results = []
            for row in cursor.fetchall():
                result_data = json.loads(row[0])
                result_data['created_at'] = row[1]
                results.append(result_data)

            conn.close()
            return results

        except Exception as e:
            self.logger.error(f"Database retrieval failed: {e}")
            return []

class OpenInterpreterController:
    """
    Production-ready OpenInterpreter Shell Controller
    Handles shell operations, Python execution, and system integration
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.security = SecurityManager(config)
        self.python_executor = PythonExecutor(config)
        self.system_monitor = SystemMonitor(config)
        self.database = DatabaseManager(config)

        # Initialize OpenInterpreter
        self.interpreter = interpreter
        self.interpreter.auto_run = config.get('interpreter', {}).get('auto_run', False)

        # Active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        self.logger.info("OpenInterpreter Controller initialized")

    async def initialize(self):
        """Initialize the shell controller"""
        try:
            # Configure OpenInterpreter
            self.interpreter.offline = True  # Use local models if available
            self.interpreter.safe_mode = self.config.get('interpreter', {}).get('safe_mode', True)

            # Test system access
            system_info = await self.system_monitor.get_system_info()
            if 'error' not in system_info:
                self.logger.info("System monitoring initialized successfully")

            # Test database connection
            test_result = await self.database.store_execution_result(
                "test_session",
                {"message": "Initialization test", "success": True}
            )
            if test_result:
                self.logger.info("Database connection established successfully")

            self.logger.info("OpenInterpreter Controller initialized successfully")

        except Exception as e:
            self.logger.error(f"OpenInterpreter initialization failed: {e}")
            raise

    async def process_result(self, gui_result: Dict[str, Any], task_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process GUI automation result"""
        session_id = f"process_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Initialize session
            self.active_sessions[session_id] = {
                "gui_result": gui_result,
                "task_parameters": task_parameters,
                "started_at": datetime.now(),
                "status": "processing",
                "operations": []
            }

            session = self.active_sessions[session_id]

            # Analyze GUI result
            analysis = await self._analyze_gui_result(gui_result)
            session['operations'].append({
                "type": "analysis",
                "result": analysis,
                "timestamp": datetime.now().isoformat()
            })

            # Generate system operations
            if analysis.get('success', False):
                # Save screenshots with metadata
                screenshot_result = await self._save_screenshots(gui_result, task_parameters)
                session['operations'].append({
                    "type": "screenshot_processing",
                    "result": screenshot_result,
                    "timestamp": datetime.now().isoformat()
                })

                # Generate receipt/report
                report_result = await self._generate_report(gui_result, task_parameters)
                session['operations'].append({
                    "type": "report_generation",
                    "result": report_result,
                    "timestamp": datetime.now().isoformat()
                })

                # Send notifications
                notification_result = await self._send_notifications(gui_result, task_parameters)
                session['operations'].append({
                    "type": "notifications",
                    "result": notification_result,
                    "timestamp": datetime.now().isoformat()
                })

            # Update session status
            session['status'] = 'completed'
            session['completed_at'] = datetime.now()

            # Store in database
            await self.database.store_execution_result(session_id, session)

            return {
                "session_id": session_id,
                "status": session['status'],
                "operations": session['operations'],
                "execution_time": (session['completed_at'] - session['started_at']).total_seconds()
            }

        except Exception as e:
            self.logger.error(f"Result processing failed: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['status'] = 'failed'
                self.active_sessions[session_id]['error'] = str(e)

            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e)
            }

    async def _analyze_gui_result(self, gui_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze GUI automation result"""
        try:
            # Extract key information
            status = gui_result.get('status', 'unknown')
            steps_completed = gui_result.get('steps_completed', 0)
            total_steps = gui_result.get('total_steps', 0)
            screenshots = gui_result.get('screenshots', [])

            # Calculate success metrics
            success_rate = steps_completed / total_steps if total_steps > 0 else 0

            # Analyze screenshots
            screenshot_analysis = []
            for screenshot in screenshots:
                if os.path.exists(screenshot):
                    screenshot_analysis.append({
                        "path": screenshot,
                        "size": os.path.getsize(screenshot),
                        "exists": True
                    })

            return {
                "success": status == "completed",
                "status": status,
                "success_rate": success_rate,
                "steps_completed": steps_completed,
                "total_steps": total_steps,
                "screenshots": screenshot_analysis,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"GUI result analysis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _save_screenshots(self, gui_result: Dict[str, Any], task_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Save and organize screenshots"""
        try:
            screenshots = gui_result.get('screenshots', [])
            if not screenshots:
                return {"success": True, "message": "No screenshots to process"}

            # Create organized directory structure
            task_id = task_parameters.get('task_id', 'unknown')
            product_name = task_parameters.get('product_name', 'unknown')
            website = task_parameters.get('website', 'unknown')

            organized_dir = Path(f"data/results/{task_id}/{website}/{product_name}")
            organized_dir.mkdir(parents=True, exist_ok=True)

            # Copy and organize screenshots
            organized_screenshots = []
            for i, screenshot in enumerate(screenshots):
                if os.path.exists(screenshot):
                    filename = f"step_{i+1}_{datetime.now().strftime('%H%M%S')}.png"
                    dest_path = organized_dir / filename
                    shutil.copy2(screenshot, dest_path)
                    organized_screenshots.append(str(dest_path))

            # Generate metadata
            metadata = {
                "task_id": task_id,
                "product_name": product_name,
                "website": website,
                "screenshots": organized_screenshots,
                "created_at": datetime.now().isoformat(),
                "original_count": len(screenshots),
                "processed_count": len(organized_screenshots)
            }

            # Save metadata
            metadata_path = organized_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return {
                "success": True,
                "organized_dir": str(organized_dir),
                "screenshots": organized_screenshots,
                "metadata_path": str(metadata_path)
            }

        except Exception as e:
            self.logger.error(f"Screenshot organization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_report(self, gui_result: Dict[str, Any], task_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution report"""
        try:
            # Generate comprehensive report
            report = {
                "task_summary": {
                    "product_name": task_parameters.get('product_name', 'Unknown'),
                    "website": task_parameters.get('website', 'Unknown'),
                    "max_price": task_parameters.get('max_price', 0),
                    "quantity": task_parameters.get('quantity', 1),
                    "status": gui_result.get('status', 'unknown')
                },
                "execution_details": {
                    "steps_completed": gui_result.get('steps_completed', 0),
                    "total_steps": gui_result.get('total_steps', 0),
                    "execution_time": gui_result.get('execution_time', 0),
                    "screenshots_count": len(gui_result.get('screenshots', []))
                },
                "system_info": await self.system_monitor.get_system_info(),
                "timestamp": datetime.now().isoformat()
            }

            # Save report
            task_id = task_parameters.get('task_id', 'unknown')
            report_path = Path(f"data/reports/{task_id}_report.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)

            return {
                "success": True,
                "report_path": str(report_path),
                "report": report
            }

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_notifications(self, gui_result: Dict[str, Any], task_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Send notifications about task completion"""
        try:
            # Prepare notification data
            status = gui_result.get('status', 'unknown')
            product_name = task_parameters.get('product_name', 'Unknown')
            website = task_parameters.get('website', 'Unknown')

            notification_message = f"AutoBuy task {status}: {product_name} on {website}"

            # Log notification (can be extended to send emails, webhooks, etc.)
            self.logger.info(f"Notification: {notification_message}")

            # Store notification in database
            await self.database.store_execution_result(
                f"notification_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                {
                    "type": "notification",
                    "message": notification_message,
                    "gui_result": gui_result,
                    "task_parameters": task_parameters
                }
            )

            return {
                "success": True,
                "message": notification_message,
                "channels": ["log", "database"]
            }

        except Exception as e:
            self.logger.error(f"Notification sending failed: {e}")
            return {"success": False, "error": str(e)}

    async def execute_shell_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute shell command safely"""
        try:
            # Security check
            if not self.security.is_command_allowed(command):
                return {
                    "success": False,
                    "error": "Command not allowed in safe mode"
                }

            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.get('interpreter', {}).get('timeout', 300)
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "command": command,
                "timestamp": datetime.now().isoformat()
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Command execution failed: {str(e)}",
                "command": command,
                "timestamp": datetime.now().isoformat()
            }

    async def execute_python_script(self, script: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Python script"""
        return await self.python_executor.execute_python_code(script, context)

    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status"""
        return self.active_sessions.get(session_id)

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Clean up active sessions
            self.active_sessions.clear()

            self.logger.info("OpenInterpreter Controller cleaned up successfully")

        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
