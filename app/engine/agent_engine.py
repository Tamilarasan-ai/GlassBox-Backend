"""
Agent Engine - Core ReAct Loop with Gemini (google-genai SDK)
"""
import asyncio
import logging
from uuid import UUID
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import MaxIterationsExceeded
from app.core.token_pricing import TokenPricing
from app.crud import crud_trace, crud_session
from app.models.chat_session import Session
from app.models.enums import SessionStatus
from app.engine.tools.calculator import Calculator

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)


class AgentEngine:
    def __init__(self, db: AsyncSession, session_id: UUID):
        self.db = db
        self.session_id = session_id
        self.tools = {
            "calculator": Calculator()
        }
        
    async def _get_history_context(self) -> list[types.Content]:
        """
        Retrieve last 5 traces to build conversation history
        """
        traces = await crud_trace.get_session_traces(self.db, self.session_id)
        # Take last 5, reverse to chronological order
        recent_traces = sorted(traces, key=lambda t: t.created_at)[-5:]
        
        history = []
        for trace in recent_traces:
            if trace.final_output:
                history.append(types.Content(
                    role="user",
                    parts=[types.Part(text=trace.user_input)]
                ))
                history.append(types.Content(
                    role="model",
                    parts=[types.Part(text=trace.final_output)]
                ))
        
        return history

    async def run(self, user_input: str, max_iterations: int | None = None) -> dict:
        """
        Execute the ReAct loop
        """
        max_iter = max_iterations or settings.AGENT_MAX_ITERATIONS
        
        # 1. Get Session & Agent Info
        session = await self.db.get(Session, self.session_id)
        if not session:
            raise ValueError("Session not found")
            
        # 2. Create High-Level Trace
        trace = await crud_trace.create_trace(
            db=self.db,
            session_id=self.session_id,
            agent_id=session.agent_id,
            user_input=user_input,
            run_name="chat_turn"
        )
        
        # Capture system snapshots for observability and replay
        from app.models.agent import Agent
        agent = await self.db.get(Agent, session.agent_id)
        if agent:
            trace.system_prompt_snapshot = agent.system_prompt
            trace.model_config_snapshot = agent.model_config
            await self.db.commit()
            await self.db.refresh(trace)
            logger.debug(f"Captured system snapshots for trace {trace.id}")
        
        # 3. Build Context & Tools
        history = await self._get_history_context()
        
        # Define tools for Gemini using new API
        tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="calculator",
                        description=self.tools["calculator"].description,
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "expression": types.Schema(
                                    type=types.Type.STRING,
                                    description="Mathematical expression to evaluate"
                                )
                            },
                            required=["expression"]
                        )
                    )
                ]
            )
        ]
        
        # 4. ReAct Loop
        import time
        from datetime import datetime
        
        trace_start_time = time.time()
        total_input_tokens = 0
        total_output_tokens = 0
        
        step_count = 0
        final_response = ""
        is_success = False
        error_msg = None
        
        # Build contents list
        contents = history + [types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )]
        
        try:
            # Initial call to model
            logger.debug(f"Calling Gemini API with model: {settings.LLM_MODEL}")
            response = await client.aio.models.generate_content(
                model=settings.LLM_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    tools=tools,
                    temperature=0.1
                )
            )
            logger.debug(f"✓ Received response from Gemini API")
            
            # Extract tokens from response
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                total_input_tokens += response.usage_metadata.prompt_token_count or 0
                total_output_tokens += response.usage_metadata.candidates_token_count or 0
                logger.debug(f"Tokens - Input: {response.usage_metadata.prompt_token_count}, Output: {response.usage_metadata.candidates_token_count}")
            
            # Main ReAct loop
            for iteration in range(max_iter):
                step_count += 1
                
                # Comprehensive validation of response structure
                if not hasattr(response, 'candidates') or not response.candidates:
                    logger.error(f"Empty response from Gemini - no candidates")
                    raise Exception(
                        "⚠️ AI model returned empty response. This may indicate API quota limit reached. "
                        "Please try again later or check your API quota."
                    )
                
                candidate = response.candidates[0]
                if not hasattr(candidate, 'content') or not candidate.content:
                    logger.error(f"Empty candidate content from Gemini")
                    raise Exception("⚠️ AI model returned invalid response structure. Please try again.")
                
                if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                    logger.error(f"Empty parts in candidate content - this is the 'empty output' error")
                    raise Exception(
                        "⚠️ AI model returned empty response. This typically means:\n"
                        "1. API quota exceeded (free tier: 20 requests/day)\n"
                        "2. Rate limit hit\n"
                        "3. Model configuration issue\n\n"
                        "Please wait a moment and try again, or check https://ai.google.dev/pricing"
                    )
                
                # Get the first part
                part = candidate.content.parts[0]
                
                # Check for function call
                if part.function_call:
                    fc = part.function_call
                    tool_name = fc.name
                    tool_args = dict(fc.args)
                    
                    # Log Tool Call Step
                    await crud_trace.create_trace_step(
                        db=self.db,
                        trace_id=trace.id,
                        sequence_order=step_count,
                        step_type="tool_call",
                        step_name=tool_name,
                        input_payload=tool_args
                    )
                    
                    # Execute Tool
                    tool_result = "Error: Tool not found"
                    if tool_name in self.tools:
                        try:
                            if tool_name == "calculator":
                                tool_result = self.tools[tool_name].execute(tool_args.get("expression", ""))
                            else:
                                tool_result = f"Tool {tool_name} not implemented"
                        except Exception as e:
                            tool_result = f"Error executing tool: {str(e)}"
                    
                    # Log Tool Result
                    step_count += 1
                    await crud_trace.create_trace_step(
                        db=self.db,
                        trace_id=trace.id,
                        sequence_order=step_count,
                        step_type="tool_result",
                        step_name=tool_name,
                        output_payload={"result": tool_result}
                    )
                    
                    # Add function response to contents
                    contents.append(response.candidates[0].content)
                    contents.append(types.Content(
                        role="user",
                        parts=[types.Part(
                            function_response=types.FunctionResponse(
                                name=tool_name,
                                response={"result": tool_result}
                            )
                        )]
                    ))
                    
                    # Continue conversation
                    response = await client.aio.models.generate_content(
                        model=settings.LLM_MODEL,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            tools=tools,
                            temperature=0.1
                        )
                    )
                    
                    # Extract tokens from follow-up call
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        total_input_tokens += response.usage_metadata.prompt_token_count or 0
                        total_output_tokens += response.usage_metadata.candidates_token_count or 0
                    
                elif part.text:
                    # Text response - final answer
                    text_content = part.text
                    
                    # Log Thought Step
                    await crud_trace.create_trace_step(
                        db=self.db,
                        trace_id=trace.id,
                        sequence_order=step_count,
                        step_type="thought",
                        step_name="reasoning",
                        output_payload={"thought": text_content}
                    )
                    
                    final_response = text_content
                    is_success = True
                    break
                else:
                    # Unknown part type
                    logger.warning(f"Unknown response part type")
                    break
            else:
                raise MaxIterationsExceeded(f"Exceeded {max_iter} iterations")

        except Exception as e:
            error_msg = str(e)
            is_success = False
            
            logger.error(f"Agent execution failed: {error_msg}", exc_info=True)
            
            # Check for specific error patterns
            if "429" in error_msg or "quota" in error_msg.lower():
                logger.warning(f"Gemini API quota exceeded")
                final_response = (
                    "⚠️ AI quota limit reached. The free tier allows 20 requests per day. "
                    "Please try again tomorrow or upgrade your API plan at https://ai.google.dev/pricing"
                )
            elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
                logger.warning(f"Gemini API rate limit hit")
                final_response = "⏱️ Too many requests. Please wait a moment and try again."
            elif "cannot both be empty" in error_msg.lower() or "must contain" in error_msg.lower():
                logger.warning(f"Gemini returned empty response - likely quota issue")
                final_response = (
                    "⚠️ AI service returned empty response. This usually means:\n"
                    "• Daily quota exceeded (free tier: 20 requests/day)\n"
                    "• Rate limit hit (try again in a few seconds)\n\n"
                    "Upgrade at: https://ai.google.dev/pricing"
                )
            elif "⚠️" in error_msg:
                # User-friendly error already formatted
                final_response = error_msg
            else:
                logger.error(f"Unhandled error: {error_msg}")
                final_response = f"Error: {error_msg}"
            
        # 5. Calculate Metrics and Update Trace
        trace_latency_ms = int((time.time() - trace_start_time) * 1000)
        total_tokens = total_input_tokens + total_output_tokens
        
        # Calculate cost based on Gemini 2.5 Flash Lite pricing
        # Input: $0.075 per 1M tokens, Output: $0.30 per 1M tokens
        cost_usd = (
            (total_input_tokens * 0.075 / 1_000_000) +
            (total_output_tokens * 0.30 / 1_000_000)
        )
        
        logger.info(
            f"Trace metrics - Tokens: {total_tokens} (in:{total_input_tokens}, out:{total_output_tokens}), "
            f"Cost: ${cost_usd:.6f}, Latency: {trace_latency_ms}ms"
        )
        
        await crud_trace.update_trace(
            db=self.db,
            trace_id=trace.id,
            final_output=final_response,
            is_successful=is_success,
            error_message=error_msg,
            total_tokens=total_tokens,
            total_cost=cost_usd,
            latency_ms=trace_latency_ms,
            completed_at=datetime.utcnow()
        )
        
        return {
            "response": final_response,
            "status": SessionStatus.COMPLETED.value if is_success else SessionStatus.FAILED.value,
            "steps_taken": step_count,
            "metrics": {
                "total_tokens": total_tokens,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cost_usd": cost_usd,
                "latency_ms": trace_latency_ms
            }
        }


async def run_agent(
    db: AsyncSession,
    session_id: UUID,
    user_input: str,
    max_iterations: int | None = None,
) -> dict:
    engine = AgentEngine(db, session_id)
    return await engine.run(user_input, max_iterations)
