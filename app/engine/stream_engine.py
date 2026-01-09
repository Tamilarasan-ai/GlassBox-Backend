"""
Streaming Agent Engine - SSE Support
"""
import asyncio
import logging
from uuid import UUID
from typing import AsyncGenerator, Dict, Any
import json

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import MaxIterationsExceeded
from app.crud import crud_trace, crud_session
from app.models.chat_session import Session
from app.models.enums import SessionStatus
from app.engine.tools.calculator import Calculator

logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def stream_agent_execution(
    db: AsyncSession,
    session_id: UUID,
    user_input: str,
    max_iterations: int | None = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream agent execution events in real-time
    
    Yields events:
    - {"type": "start", "session_id": "..."}
    - {"type": "thought", "content": "..."}
    - {"type": "tool_call", "name": "...", "args": {...}}
    - {"type": "tool_result", "result": "..."}
    - {"type": "response", "content": "..."}
    - {"type": "complete", "success": true, "steps": 5}
    - {"type": "error", "message": "..."}
    """
    
    max_iter = max_iterations or settings.AGENT_MAX_ITERATIONS
    tools_map = {"calculator": Calculator()}
    
    try:
        # 1. Get Session
        yield {"type": "start", "session_id": str(session_id)}
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="calculator",
                        description=tools_map["calculator"].description,
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
        
        # Build contents
        contents = history + [types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )]
        
        # 4. Stream ReAct Loop
        import time
        from datetime import datetime
        
        trace_start_time = time.time()
        total_input_tokens = 0
        total_output_tokens = 0
        
        step_count = 0
        final_response = ""
        is_success = False
        error_msg = None
        
        # Initial call
        yield {"type": "thinking", "content": "Processing your request..."}
        
        response = await client.aio.models.generate_content(
            model=settings.LLM_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=tools,
                temperature=0.1
            )
        )
        
        # Extract tokens from initial response
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            total_input_tokens += response.usage_metadata.prompt_token_count or 0
            total_output_tokens += response.usage_metadata.candidates_token_count or 0
        
        # Main loop
        for iteration in range(max_iter):
            step_count += 1
            
            # Validate response
            if not hasattr(response, 'candidates') or not response.candidates:
                yield {"type": "error", "message": "Empty response from AI model"}
                break
                
            candidate = response.candidates[0]
            if not hasattr(candidate, 'content') or not candidate.content:
                yield {"type": "error", "message": "Invalid response structure"}
                break
                
            if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                yield {
                    "type": "error",
                    "message": "AI quota exceeded or rate limit hit. Please try again later."
                }
                break
            
            part = candidate.content.parts[0]
            
            # Handle function call
            if part.function_call:
                fc = part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args)
                
                # Stream tool call event
                yield {
                    "type": "tool_call",
                    "name": tool_name,
                    "args": tool_args
                }
                
                # Log to trace
                await crud_trace.create_trace_step(
                    db=db,
                    trace_id=trace.id,
                    sequence_order=step_count,
                    step_type="tool_call",
                    step_name=tool_name,
                    input_payload=tool_args
                )
                
                # Execute tool
                tool_result = "Error: Tool not found"
                if tool_name in tools_map:
                    try:
                        if tool_name == "calculator":
                            tool_result = tools_map[tool_name].execute(tool_args.get("expression", ""))
                        else:
                            tool_result = f"Tool {tool_name} not implemented"
                    except Exception as e:
                        tool_result = f"Error: {str(e)}"
                
                # Stream tool result
                yield {
                    "type": "tool_result",
                    "name": tool_name,
                    "result": tool_result
                }
                
                # Log result
                step_count += 1
                await crud_trace.create_trace_step(
                    db=db,
                    trace_id=trace.id,
                    sequence_order=step_count,
                    step_type="tool_result",
                    step_name=tool_name,
                    output_payload={"result": tool_result}
                )
                
                # Continue conversation
                contents.append(candidate.content)
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(
                        function_response=types.FunctionResponse(
                            name=tool_name,
                            response={"result": tool_result}
                        )
                    )]
                ))
                
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
                # Final text response
                text_content = part.text
                
                # Stream response
                yield {
                    "type": "response",
                    "content": text_content
                }
                
                # Log thought
                await crud_trace.create_trace_step(
                    db=db,
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
                break
        else:
            yield {"type": "error", "message": f"Exceeded {max_iter} iterations"}
            error_msg = "Max iterations exceeded"
        
        # Calculate metrics
        trace_latency_ms = int((time.time() - trace_start_time) * 1000)
        total_tokens = total_input_tokens + total_output_tokens
        
        # Calculate cost based on Gemini 2.5 Flash Lite pricing
        cost_usd = (
            (total_input_tokens * 0.075 / 1_000_000) +
            (total_output_tokens * 0.30 / 1_000_000)
        )
        
        # Update trace
        await crud_trace.update_trace(
            db=db,
            trace_id=trace.id,
            final_output=final_response,
            is_successful=is_success,
            error_message=error_msg,
            total_tokens=total_tokens,
            total_cost=cost_usd,
            latency_ms=trace_latency_ms,
            completed_at=datetime.utcnow()
        )
        
        # Final event
        yield {
            "type": "complete",
            "success": is_success,
            "steps": step_count,
            "response": final_response
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Streaming error: {e}", exc_info=True)
        
        # Detect specific error types
        if "429" in error_msg or "quota" in error_msg.lower():
            yield {
                "type": "error",
                "message": "⚠️ AI quota limit reached. Free tier allows 20 requests/day. Try again tomorrow or upgrade at https://ai.google.dev/pricing"
            }
        elif "cannot both be empty" in error_msg.lower() or "must contain" in error_msg.lower():
            yield {
                "type": "error",
                "message": "⚠️ AI service quota exceeded. Daily limit reached (20 requests/day). Please try again tomorrow or upgrade at https://ai.google.dev/pricing"
            }
        elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
            yield {
                "type": "error",
                "message": "⏱️ Rate limit hit. Please wait a moment and try again."
            }
        else:
            yield {
                "type": "error",
                "message": str(e)
            }
