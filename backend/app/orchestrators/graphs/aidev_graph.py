"""
AI-Dev Graph - Code Generation using LangGraph
===========================================
Cyclic state machine for code writing, testing, and debugging.
Uses latest LangGraph patterns with StateGraph, START, and END.
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import structlog

from ...core.config import get_llm_config_for_domain, create_openrouter_llm
from ...core.schemas import CodeGenerationResponse, CodeDebugResponse
from ...tools.mcp_client import get_aidev_task_tools

logger = structlog.get_logger()


def _extract_content(response: Any) -> str:
    """Extract content from LLM response safely."""
    if hasattr(response, 'content'):
        content = response.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle list of content parts (e.g., [{"type": "text", "text": "..."}])
            return " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
    return str(response)


class AIDevState(TypedDict):
    """State for AI-Dev LangGraph using TypedDict with reducers."""
    task_description: str
    language: str
    constraints: List[str]
    generated_code: Annotated[Optional[str], lambda x, y: y or x]
    test_code: Annotated[Optional[str], lambda x, y: y or x]
    test_results: Annotated[Optional[str], lambda x, y: y or x]
    evaluation: Annotated[Optional[Literal["pass", "fail", "needs_fix"]], lambda x, y: y or x]
    fixed_code: Annotated[Optional[str], lambda x, y: y or x]
    error_message: Annotated[Optional[str], lambda x, y: y or x]
    iterations: int
    max_iterations: int


class AIDevGraph:
    """
    AI-Dev Graph using LangGraph for cyclic code generation.
    
    Workflow:
    Write Code -> Execute Tool -> Evaluate -> Fix (Loop)
    
    Uses latest LangGraph patterns:
    - StateGraph with TypedDict
    - START and END from langgraph.graph
    - MemorySaver for checkpointing
    """
    
    def __init__(self):
        """Initialize the AI-Dev Graph."""
        self.llm_config = get_llm_config_for_domain("aidev")
        self.llm = create_openrouter_llm("aidev")
        
        # Bind MCP tools to LLM for function calling
        try:
            task_tools = get_aidev_task_tools()
            langchain_tools = task_tools.get_langchain_tools()
            if langchain_tools:
                self.llm = self.llm.bind_tools(langchain_tools)
                logger.info("aidev_tools_bound", tool_count=len(langchain_tools))
        except Exception as e:
            logger.warning("aidev_tools_not_available", error=str(e))
        
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph state machine using latest patterns."""
        
        graph = StateGraph(AIDevState)
        
        # Add nodes
        graph.add_node("write_code", self._write_code)
        graph.add_node("execute_code", self._execute_code)
        graph.add_node("evaluate", self._evaluate)
        graph.add_node("fix_code", self._fix_code)
        
        # Add edges using START (latest pattern)
        graph.add_edge(START, "write_code")
        graph.add_edge("write_code", "execute_code")
        graph.add_edge("execute_code", "evaluate")
        
        # Conditional edge based on evaluation
        graph.add_conditional_edges(
            "evaluate",
            self._should_continue,
            {
                "continue": "fix_code",
                "end": END,
            }
        )
        
        graph.add_edge("fix_code", "execute_code")
        
        # Compile with checkpoint saver for state persistence
        return graph.compile(checkpointer=MemorySaver())
    
    def _write_code(self, state: AIDevState) -> Dict[str, Any]:
        """Write code node using LLM."""
        logger.info("aidev_writing_code", iterations=state["iterations"])
        
        prompt = f"""Write {state['language']} code for the following task:
Task: {state['task_description']}
Constraints: {', '.join(state['constraints']) if state['constraints'] else 'None'}

Generate clean, well-documented code that accomplishes the task."""

        try:
            response = self.llm.invoke(prompt)
            code = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error("aidev_llm_error", error=str(e))
            code = f"# Code generation failed: {str(e)}\n# Placeholder code\n"
        
        return {"generated_code": code}
    
    def _execute_code(self, state: AIDevState) -> Dict[str, Any]:
        """Execute code node."""
        logger.info("aidev_executing_code")
        
        code = state.get("generated_code", "")
        if not code or code.startswith("# Code generation failed"):
            return {"test_results": "No code to execute"}
        
        # Placeholder for actual execution
        # In production, this would use a sandboxed execution environment
        return {"test_results": "Execution pending - requires sandbox environment"}
    
    def _evaluate(self, state: AIDevState) -> Dict[str, Any]:
        """Evaluate code node using LLM."""
        logger.info("aidev_evaluating")
        
        code = state.get("generated_code", "")
        test_results = state.get("test_results", "")
        
        if not code:
            return {"evaluation": "needs_fix", "error_message": "No code generated"}
        
        # Use LLM to evaluate code quality
        prompt = f"""Evaluate this {state['language']} code:
        
```{state['language']}
{code}
```

Test Results: {test_results}

Respond with ONLY one word: 'pass' if code looks correct, 'needs_fix' if it has issues."""
        
        try:
            response = self.llm.invoke(prompt)
            evaluation = _extract_content(response).strip().lower()
            
            if "pass" in evaluation and "need" not in evaluation:
                evaluation = "pass"
            else:
                evaluation = "needs_fix"
        except Exception as e:
            logger.error("aidev_evaluation_error", error=str(e))
            evaluation = "needs_fix"
        
        return {"evaluation": evaluation}
    
    def _fix_code(self, state: AIDevState) -> Dict[str, Any]:
        """Fix code node using LLM."""
        new_iterations = state["iterations"] + 1
        logger.info("aidev_fixing_code", iterations=new_iterations)
        
        current_code = state.get("generated_code", "")
        error_msg = state.get("error_message", "Code needs improvement")
        
        prompt = f"""Fix this {state['language']} code. The code has the following issues:
{error_msg}

Original Code:
```{state['language']}
{current_code}
```

Provide the corrected code:"""

        try:
            response = self.llm.invoke(prompt)
            fixed_code = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error("aidev_fix_error", error=str(e))
            fixed_code = current_code  # Keep original if fix fails
        
        return {
            "fixed_code": fixed_code,
            "generated_code": fixed_code,
            "iterations": new_iterations,
        }
    
    def _should_continue(self, state: AIDevState) -> Literal["continue", "end"]:
        """Determine if should continue fixing or end."""
        if state["iterations"] >= state["max_iterations"]:
            return "end"
        if state.get("evaluation") == "pass":
            return "end"
        return "continue"
    
    def generate_code(
        self,
        task_description: str,
        language: str,
        constraints: Optional[List[str]] = None,
    ) -> CodeGenerationResponse:
        """
        Generate code using LangGraph.
        
        Args:
            task_description: Description of the coding task
            language: Programming language
            constraints: Optional constraints
        
        Returns:
            CodeGenerationResponse with generated code
        """
        logger.info("aidev_generating_code", language=language)
        
        initial_state: AIDevState = {
            "task_description": task_description,
            "language": language,
            "constraints": constraints or [],
            "generated_code": None,
            "test_code": None,
            "test_results": None,
            "evaluation": None,
            "fixed_code": None,
            "error_message": None,
            "iterations": 0,
            "max_iterations": 5,
        }
        
        # Run the graph
        config = {"configurable": {"thread_id": f"aidev-{language}"}}
        
        try:
            result = self.graph.invoke(initial_state, config)  # type: ignore[arg-type]
            generated = result.get("generated_code", "# Code generation failed")
        except Exception as e:
            logger.error("aidev_graph_error", error=str(e))
            generated = f"# Error during code generation: {str(e)}\n# Please try again"
        
        return CodeGenerationResponse(
            session_id=config["configurable"]["thread_id"],
            generated_code=generated,
            explanation="Code generated using LangGraph workflow",
            file_name=f"generated.{language}",
            dependencies=[],
            test_code=None,
        )
    
    def debug_code(
        self,
        code: str,
        error_message: Optional[str],
        language: str,
    ) -> CodeDebugResponse:
        """
        Debug code using LangGraph.
        
        Args:
            code: Code to debug
            error_message: Optional error message
            language: Programming language
        
        Returns:
            CodeDebugResponse with fixed code
        """
        logger.info("aidev_debugging_code", language=language)
        
        prompt = f"""Debug this {language} code. Here's the error message:
{error_message or 'No specific error provided'}

Code:
```{language}
{code}
```

Provide the fixed code with explanations:"""

        try:
            response = self.llm.invoke(prompt)
            fixed = _extract_content(response)
            issues = [{"issue": error_message or "Code review", "status": "fixed"}]
        except Exception as e:
            logger.error("aidev_debug_error", error=str(e))
            fixed = code
            issues = [{"issue": str(e), "status": "error"}]
        
        return CodeDebugResponse(
            session_id="debug-session",
            issues_found=issues,
            fixed_code=fixed,
            explanation="Code debugged using LLM",
        )


# Global instance
_aidev_graph: Optional[AIDevGraph] = None


def get_aidev_graph() -> AIDevGraph:
    """Get or create the AI-Dev Graph instance."""
    global _aidev_graph
    if _aidev_graph is None:
        _aidev_graph = AIDevGraph()
    return _aidev_graph


__all__ = ["AIDevGraph", "AIDevState", "get_aidev_graph"]
