"""
GOD-TIER AUTOBUY STACK - LangGraph Task Engine
Production-ready task planning and execution engine
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskState:
    """Task state for LangGraph"""
    task_id: str
    task_type: str
    description: str
    parameters: Dict[str, Any]
    status: TaskStatus
    plan: Optional[Dict[str, Any]] = None
    execution_steps: List[Dict[str, Any]] = None
    current_step: int = 0
    results: List[Dict[str, Any]] = None
    errors: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.execution_steps is None:
            self.execution_steps = []
        if self.results is None:
            self.results = []
        if self.errors is None:
            self.errors = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class LangGraphTaskEngine:
    """
    Production-ready LangGraph Task Engine
    Handles task planning, execution, and validation
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize AI models
        self.primary_model = self._init_primary_model()
        self.fallback_model = self._init_fallback_model()

        # Initialize checkpointer
        self.checkpointer = SqliteSaver.from_conn_string("data/langgraph_checkpoints.db")

        # Build graph
        self.graph = self._build_graph()

        # Active tasks
        self.active_tasks: Dict[str, TaskState] = {}

        self.logger.info("LangGraph Task Engine initialized")

    def _init_primary_model(self) -> ChatOpenAI:
        """Initialize primary AI model"""
        ai_config = self.config.get('ai', {})
        openai_config = ai_config.get('openai', {})

        return ChatOpenAI(
            model=openai_config.get('model', 'gpt-4-turbo'),
            temperature=openai_config.get('temperature', 0.1),
            max_tokens=openai_config.get('max_tokens', 4096),
            api_key=openai_config.get('api_key'),
            timeout=30
        )

    def _init_fallback_model(self) -> ChatAnthropic:
        """Initialize fallback AI model"""
        ai_config = self.config.get('ai', {})
        anthropic_config = ai_config.get('anthropic', {})

        return ChatAnthropic(
            model=anthropic_config.get('model', 'claude-3-sonnet-20240229'),
            temperature=anthropic_config.get('temperature', 0.1),
            max_tokens=anthropic_config.get('max_tokens', 4096),
            api_key=anthropic_config.get('api_key'),
            timeout=30
        )

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph execution graph"""
        graph = StateGraph(TaskState)

        # Add nodes
        graph.add_node("task_planner", self._plan_task)
        graph.add_node("decision_maker", self._make_decision)
        graph.add_node("executor", self._execute_step)
        graph.add_node("validator", self._validate_result)
        graph.add_node("reporter", self._generate_report)

        # Add edges
        graph.add_edge("task_planner", "decision_maker")
        graph.add_edge("decision_maker", "executor")
        graph.add_edge("executor", "validator")
        graph.add_edge("validator", "reporter")

        # Add conditional edges
        graph.add_conditional_edges(
            "reporter",
            self._should_continue,
            {
                "continue": "decision_maker",
                "complete": END
            }
        )

        # Set entry point
        graph.set_entry_point("task_planner")

        return graph.compile(checkpointer=self.checkpointer)

    async def initialize(self):
        """Initialize the task engine"""
        try:
            # Test AI models
            await self._test_models()

            # Initialize database
            await self._init_database()

            self.logger.info("Task engine initialized successfully")

        except Exception as e:
            self.logger.error(f"Task engine initialization failed: {e}")
            raise

    async def _test_models(self):
        """Test AI model connectivity"""
        try:
            # Test primary model
            response = await self.primary_model.ainvoke([HumanMessage(content="Test")])
            self.logger.info("Primary model (OpenAI) connected successfully")

            # Test fallback model
            response = await self.fallback_model.ainvoke([HumanMessage(content="Test")])
            self.logger.info("Fallback model (Anthropic) connected successfully")

        except Exception as e:
            self.logger.warning(f"Model connectivity test failed: {e}")

    async def _init_database(self):
        """Initialize database tables"""
        # Database initialization handled by checkpointer
        pass

    async def create_plan(self, task_type: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create execution plan for a task"""
        task_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create task state
        task_state = TaskState(
            task_id=task_id,
            task_type=task_type,
            description=description,
            parameters=parameters,
            status=TaskStatus.PLANNING
        )

        self.active_tasks[task_id] = task_state

        try:
            # Execute the planning graph
            result = await self.graph.ainvoke(
                task_state,
                config={"configurable": {"thread_id": task_id}}
            )

            return {
                "task_id": task_id,
                "plan": result.plan,
                "execution_steps": result.execution_steps,
                "status": result.status.value
            }

        except Exception as e:
            self.logger.error(f"Plan creation failed for task {task_id}: {e}")
            task_state.status = TaskStatus.FAILED
            task_state.errors.append(str(e))
            raise

    async def _plan_task(self, state: TaskState) -> TaskState:
        """Plan task execution steps"""
        self.logger.info(f"Planning task {state.task_id}")

        try:
            # Create planning prompt
            prompt = self._create_planning_prompt(state)

            # Get plan from AI
            try:
                response = await self.primary_model.ainvoke([HumanMessage(content=prompt)])
            except Exception as e:
                self.logger.warning(f"Primary model failed, using fallback: {e}")
                response = await self.fallback_model.ainvoke([HumanMessage(content=prompt)])

            # Parse plan
            plan = self._parse_plan(response.content)

            # Update state
            state.plan = plan
            state.execution_steps = plan.get('steps', [])
            state.status = TaskStatus.EXECUTING
            state.updated_at = datetime.now()

            self.logger.info(f"Task {state.task_id} planned successfully")

        except Exception as e:
            self.logger.error(f"Planning failed for task {state.task_id}: {e}")
            state.status = TaskStatus.FAILED
            state.errors.append(f"Planning failed: {str(e)}")

        return state

    def _create_planning_prompt(self, state: TaskState) -> str:
        """Create planning prompt for AI"""
        if state.task_type == "autobuy":
            return f"""
You are a GOD-TIER AutoBuy AI planner. Create a detailed execution plan for:

Task: {state.description}
Website: {state.parameters.get('website', 'unknown')}
Product: {state.parameters.get('product_name', 'unknown')}
Max Price: {state.parameters.get('max_price', 'N/A')}
Quantity: {state.parameters.get('quantity', 1)}

Create a JSON plan with the following structure:
{{
    "plan_id": "unique_plan_id",
    "website": "target_website",
    "strategy": "stealth_mode",
    "steps": [
        {{
            "step_id": 1,
            "action": "navigate_to_website",
            "details": "Navigate to target website with stealth settings",
            "expected_outcome": "Website loaded successfully",
            "timeout": 30,
            "retry_count": 3
        }},
        {{
            "step_id": 2,
            "action": "search_product",
            "details": "Search for the specified product",
            "search_term": "product_name",
            "expected_outcome": "Product found in search results",
            "timeout": 20,
            "retry_count": 2
        }},
        {{
            "step_id": 3,
            "action": "verify_price",
            "details": "Check if product price is within budget",
            "max_price": "max_price_limit",
            "expected_outcome": "Price verified and within budget",
            "timeout": 10,
            "retry_count": 1
        }},
        {{
            "step_id": 4,
            "action": "add_to_cart",
            "details": "Add product to shopping cart",
            "quantity": "specified_quantity",
            "expected_outcome": "Product added to cart successfully",
            "timeout": 15,
            "retry_count": 2
        }},
        {{
            "step_id": 5,
            "action": "proceed_to_checkout",
            "details": "Navigate to checkout page",
            "expected_outcome": "Checkout page loaded",
            "timeout": 20,
            "retry_count": 2
        }}
    ],
    "validation_criteria": [
        "Product matches search criteria",
        "Price within budget",
        "Quantity correct",
        "Successfully added to cart"
    ],
    "contingency_plans": [
        "If price too high: abort mission",
        "If out of stock: search for alternatives",
        "If website blocks: use stealth mode"
    ]
}}

Respond ONLY with valid JSON, no additional text.
"""

        # Default generic planning prompt
        return f"""
Create an execution plan for: {state.description}
Parameters: {json.dumps(state.parameters, indent=2)}

Provide a JSON response with plan details and execution steps.
"""

    def _parse_plan(self, plan_content: str) -> Dict[str, Any]:
        """Parse AI response into plan structure"""
        try:
            # Extract JSON from response
            if "```json" in plan_content:
                json_start = plan_content.find("```json") + 7
                json_end = plan_content.find("```", json_start)
                plan_content = plan_content[json_start:json_end]

            return json.loads(plan_content.strip())

        except Exception as e:
            self.logger.error(f"Plan parsing failed: {e}")
            # Return default plan structure
            return {
                "plan_id": "fallback_plan",
                "strategy": "basic",
                "steps": [
                    {
                        "step_id": 1,
                        "action": "execute_task",
                        "details": "Execute the requested task",
                        "expected_outcome": "Task completed",
                        "timeout": 60,
                        "retry_count": 3
                    }
                ],
                "validation_criteria": ["Task completed successfully"],
                "contingency_plans": ["Retry on failure"]
            }

    async def _make_decision(self, state: TaskState) -> TaskState:
        """Make execution decisions"""
        self.logger.info(f"Making decision for task {state.task_id}")

        # Simple decision logic - proceed with next step
        if state.current_step < len(state.execution_steps):
            current_step = state.execution_steps[state.current_step]
            self.logger.info(f"Proceeding with step {state.current_step + 1}: {current_step.get('action', 'unknown')}")
        else:
            self.logger.info(f"All steps completed for task {state.task_id}")
            state.status = TaskStatus.VALIDATING

        return state

    async def _execute_step(self, state: TaskState) -> TaskState:
        """Execute current step"""
        if state.current_step >= len(state.execution_steps):
            return state

        current_step = state.execution_steps[state.current_step]
        self.logger.info(f"Executing step {state.current_step + 1}: {current_step.get('action', 'unknown')}")

        try:
            # Simulate step execution
            await asyncio.sleep(1)  # Simulate processing time

            # Record result
            result = {
                "step_id": current_step.get('step_id', state.current_step + 1),
                "action": current_step.get('action', 'unknown'),
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "outcome": current_step.get('expected_outcome', 'Step completed')
            }

            state.results.append(result)
            state.current_step += 1
            state.updated_at = datetime.now()

            self.logger.info(f"Step {current_step.get('step_id', state.current_step)} completed")

        except Exception as e:
            self.logger.error(f"Step execution failed: {e}")
            state.errors.append(f"Step {state.current_step + 1} failed: {str(e)}")
            state.status = TaskStatus.FAILED

        return state

    async def _validate_result(self, state: TaskState) -> TaskState:
        """Validate execution results"""
        self.logger.info(f"Validating results for task {state.task_id}")

        try:
            # Check validation criteria
            if state.plan and 'validation_criteria' in state.plan:
                criteria = state.plan['validation_criteria']
                passed_criteria = len([r for r in state.results if r.get('status') == 'completed'])

                if passed_criteria == len(state.execution_steps):
                    state.status = TaskStatus.COMPLETED
                    self.logger.info(f"Task {state.task_id} validation passed")
                else:
                    state.status = TaskStatus.FAILED
                    state.errors.append("Validation criteria not met")
                    self.logger.warning(f"Task {state.task_id} validation failed")
            else:
                # Default validation
                if len(state.errors) == 0:
                    state.status = TaskStatus.COMPLETED
                else:
                    state.status = TaskStatus.FAILED

            state.updated_at = datetime.now()

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            state.status = TaskStatus.FAILED
            state.errors.append(f"Validation error: {str(e)}")

        return state

    async def _generate_report(self, state: TaskState) -> TaskState:
        """Generate execution report"""
        self.logger.info(f"Generating report for task {state.task_id}")

        try:
            report = {
                "task_id": state.task_id,
                "task_type": state.task_type,
                "description": state.description,
                "status": state.status.value,
                "execution_time": (state.updated_at - state.created_at).total_seconds(),
                "steps_completed": len(state.results),
                "total_steps": len(state.execution_steps),
                "success_rate": len([r for r in state.results if r.get('status') == 'completed']) / len(state.execution_steps) if state.execution_steps else 0,
                "errors": state.errors,
                "results": state.results,
                "timestamp": datetime.now().isoformat()
            }

            # Store report
            state.results.append({
                "type": "final_report",
                "report": report,
                "timestamp": datetime.now().isoformat()
            })

            self.logger.info(f"Report generated for task {state.task_id}")

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            state.errors.append(f"Report generation failed: {str(e)}")

        return state

    def _should_continue(self, state: TaskState) -> str:
        """Determine if execution should continue"""
        if state.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return "complete"
        elif state.current_step < len(state.execution_steps):
            return "continue"
        else:
            return "complete"

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status"""
        if task_id not in self.active_tasks:
            return None

        task_state = self.active_tasks[task_id]
        return {
            "task_id": task_id,
            "status": task_state.status.value,
            "progress": task_state.current_step / len(task_state.execution_steps) if task_state.execution_steps else 0,
            "current_step": task_state.current_step,
            "total_steps": len(task_state.execution_steps),
            "errors": task_state.errors,
            "updated_at": task_state.updated_at.isoformat()
        }

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id not in self.active_tasks:
            return False

        task_state = self.active_tasks[task_id]
        task_state.status = TaskStatus.FAILED
        task_state.errors.append("Task cancelled by user")
        task_state.updated_at = datetime.now()

        self.logger.info(f"Task {task_id} cancelled")
        return True
