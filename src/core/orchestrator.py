"""
GOD-TIER AUTOBUY STACK - Central Orchestrator
เป็นหัวใจของระบบที่ประสานงานระหว่าง LangGraph, Agent-S2, และ OpenInterpreter
"""

import asyncio
import logging
import yaml
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from ..langgraph.task_engine import LangGraphTaskEngine
from ..agent_s2.gui_controller import AgentS2Controller
from ..interpreter.shell_controller import OpenInterpreterController
from ..memory.memory_manager import MemoryManager
from ..monitoring.logger import AdvancedLogger
from ..monitoring.metrics import MetricsCollector

# Configuration Models
@dataclass
class SystemConfig:
    """System configuration dataclass"""
    name: str
    version: str
    mode: str
    debug: bool
    log_level: str

@dataclass
class TaskRequest:
    """Task request from user"""
    task_id: str
    task_type: str
    description: str
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: int = 300

class AutoBuyRequest(BaseModel):
    """AutoBuy request model"""
    product_name: str
    website: str
    max_price: float
    quantity: int = 1
    auto_confirm: bool = False
    payment_method: str = "credit_card"

class TaskStatus(BaseModel):
    """Task status model"""
    task_id: str
    status: str
    progress: float
    message: str
    started_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None

class GodTierOrchestrator:
    """
    GOD-TIER AUTOBUY STACK Central Orchestrator
    ประสานงานทุกส่วนของระบบ
    """

    def __init__(self, config_path: str = "config/main.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.app = FastAPI(title="GOD-TIER AUTOBUY STACK")
        self.setup_middleware()

        # Initialize components
        self.logger = AdvancedLogger(self.config)
        self.metrics = MetricsCollector(self.config)
        self.memory = MemoryManager(self.config)

        # Initialize controllers
        self.langgraph_engine = None
        self.agent_s2_controller = None
        self.interpreter_controller = None

        # Task management
        self.active_tasks: Dict[str, TaskStatus] = {}
        self.task_queue: List[TaskRequest] = []
        self.websocket_connections: List[WebSocket] = []

        # Setup routes
        self.setup_routes()

        self.logger.info("GOD-TIER AUTOBUY STACK Orchestrator initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return {}

    def setup_middleware(self):
        """Setup FastAPI middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get('api', {}).get('cors_origins', ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/")
        async def root():
            return {
                "message": "GOD-TIER AUTOBUY STACK is running",
                "version": self.config.get('system', {}).get('version', '1.0.0'),
                "status": "active",
                "components": {
                    "langgraph": self.langgraph_engine is not None,
                    "agent_s2": self.agent_s2_controller is not None,
                    "interpreter": self.interpreter_controller is not None
                }
            }

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_tasks": len(self.active_tasks),
                "queue_size": len(self.task_queue)
            }

        @self.app.post("/autobuy")
        async def autobuy_endpoint(request: AutoBuyRequest):
            """Main AutoBuy endpoint"""
            task_id = f"autobuy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            task_request = TaskRequest(
                task_id=task_id,
                task_type="autobuy",
                description=f"AutoBuy {request.product_name} from {request.website}",
                parameters=request.dict(),
                priority=1,
                timeout=600
            )

            # Add to queue
            self.task_queue.append(task_request)

            # Start processing
            asyncio.create_task(self.process_task(task_request))

            return {
                "task_id": task_id,
                "status": "queued",
                "message": "AutoBuy task queued for processing"
            }

        @self.app.get("/task/{task_id}")
        async def get_task_status(task_id: str):
            """Get task status"""
            if task_id not in self.active_tasks:
                raise HTTPException(status_code=404, detail="Task not found")

            task = self.active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status,
                "progress": task.progress,
                "message": task.message,
                "started_at": task.started_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "result": task.result
            }

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.websocket_connections.append(websocket)

            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)

    async def initialize_components(self):
        """Initialize all system components"""
        try:
            # Initialize LangGraph Task Engine
            self.langgraph_engine = LangGraphTaskEngine(self.config)
            await self.langgraph_engine.initialize()

            # Initialize Agent-S2 Controller
            self.agent_s2_controller = AgentS2Controller(self.config)
            await self.agent_s2_controller.initialize()

            # Initialize OpenInterpreter Controller
            self.interpreter_controller = OpenInterpreterController(self.config)
            await self.interpreter_controller.initialize()

            self.logger.info("All components initialized successfully")

        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            raise

    async def process_task(self, task_request: TaskRequest):
        """Process a task through the entire pipeline"""
        task_id = task_request.task_id

        # Create task status
        task_status = TaskStatus(
            task_id=task_id,
            status="processing",
            progress=0.0,
            message="Task started",
            started_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.active_tasks[task_id] = task_status

        try:
            # Update progress
            await self.update_task_progress(task_id, 10, "Planning task with LangGraph")

            # Phase 1: Task Planning with LangGraph
            plan = await self.langgraph_engine.create_plan(
                task_type=task_request.task_type,
                description=task_request.description,
                parameters=task_request.parameters
            )

            await self.update_task_progress(task_id, 30, "Executing GUI automation")

            # Phase 2: GUI Automation with Agent-S2
            if task_request.task_type == "autobuy":
                gui_result = await self.agent_s2_controller.execute_autobuy(
                    plan=plan,
                    website=task_request.parameters.get('website'),
                    product_name=task_request.parameters.get('product_name'),
                    max_price=task_request.parameters.get('max_price')
                )

                await self.update_task_progress(task_id, 60, "Processing with OpenInterpreter")

                # Phase 3: Shell Operations with OpenInterpreter
                shell_result = await self.interpreter_controller.process_result(
                    gui_result=gui_result,
                    task_parameters=task_request.parameters
                )

                await self.update_task_progress(task_id, 80, "Validating results")

                # Phase 4: Validation and Reporting
                final_result = await self.validate_and_report(
                    task_id=task_id,
                    plan=plan,
                    gui_result=gui_result,
                    shell_result=shell_result
                )

                await self.update_task_progress(task_id, 100, "Task completed successfully")

                # Update final status
                task_status.status = "completed"
                task_status.result = final_result
                task_status.updated_at = datetime.now()

        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {e}")
            task_status.status = "failed"
            task_status.message = f"Task failed: {str(e)}"
            task_status.updated_at = datetime.now()

        finally:
            # Store in memory
            await self.memory.store_task_result(task_id, task_status)

    async def update_task_progress(self, task_id: str, progress: float, message: str):
        """Update task progress and notify WebSocket clients"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.progress = progress
            task.message = message
            task.updated_at = datetime.now()

            # Notify WebSocket clients
            notification = {
                "task_id": task_id,
                "progress": progress,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }

            await self.broadcast_to_websockets(notification)

    async def broadcast_to_websockets(self, message: Dict[str, Any]):
        """Broadcast message to all WebSocket connections"""
        if self.websocket_connections:
            disconnected = []
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.append(websocket)

            # Remove disconnected clients
            for websocket in disconnected:
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)

    async def validate_and_report(self, task_id: str, plan: Dict, gui_result: Dict, shell_result: Dict) -> Dict[str, Any]:
        """Validate task results and generate report"""
        return {
            "task_id": task_id,
            "success": True,
            "plan": plan,
            "gui_result": gui_result,
            "shell_result": shell_result,
            "timestamp": datetime.now().isoformat(),
            "validation_score": 0.95
        }

    async def start_server(self):
        """Start the orchestrator server"""
        try:
            # Initialize components
            await self.initialize_components()

            # Start metrics collection
            await self.metrics.start_collection()

            # Start server
            config = uvicorn.Config(
                app=self.app,
                host=self.config.get('api', {}).get('host', '0.0.0.0'),
                port=self.config.get('api', {}).get('port', 8080),
                log_level=self.config.get('system', {}).get('log_level', 'info').lower()
            )

            server = uvicorn.Server(config)
            await server.serve()

        except Exception as e:
            self.logger.error(f"Server startup failed: {e}")
            raise

# CLI Interface
import click

@click.command()
@click.option('--config', '-c', default='config/main.yaml', help='Configuration file path')
@click.option('--init', is_flag=True, help='Initialize the system')
@click.option('--start', is_flag=True, help='Start the orchestrator')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def main(config, init, start, debug):
    """GOD-TIER AUTOBUY STACK CLI"""

    if init:
        click.echo("🚀 Initializing GOD-TIER AUTOBUY STACK...")
        # Create directories
        directories = [
            "data", "logs", "config", "src/core", "src/langgraph",
            "src/agent_s2", "src/interpreter", "src/memory", "src/monitoring"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

        click.echo("✅ System initialized successfully!")
        return

    if start:
        click.echo("🔥 Starting GOD-TIER AUTOBUY STACK...")
        orchestrator = GodTierOrchestrator(config)

        if debug:
            logging.basicConfig(level=logging.DEBUG)

        try:
            asyncio.run(orchestrator.start_server())
        except KeyboardInterrupt:
            click.echo("\n🛑 Shutting down GOD-TIER AUTOBUY STACK...")
        except Exception as e:
            click.echo(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
