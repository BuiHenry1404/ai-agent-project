import asyncio
import os
import sys
import time
from inspect import iscoroutinefunction
from typing import AsyncGenerator, Awaitable, Callable, Dict, List, Optional, TypeVar, Union, cast

from autogen_core import CancellationToken
from autogen_core.models import RequestUsage

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.base import Response, TaskResult
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    ModelClientStreamingChunkEvent,
    MultiModalMessage,
    UserInputRequestedEvent,
    ToolCallRequestEvent,
    ToolCallSummaryMessage,
    ToolCallExecutionEvent,
)

T = TypeVar("T", bound=TaskResult | Response)


class FileStreamConsole:
    def __init__(self, log_file: str = "agent_stream.log"):
        self.log_file = log_file
        
    async def awrite(self, output: str, end: str = "\n") -> None:
        """Write output to file asynchronously"""
        content = output + end
        await asyncio.to_thread(self._write_to_file, content)
    
    def _write_to_file(self, content: str) -> None:
        """Write content to file synchronously"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(content)
    
    async def process_stream(
        self,
        stream: AsyncGenerator[BaseAgentEvent | BaseChatMessage | T, None],
        *,
        output_stats: bool = False,
    ) -> T:
        """
        Process the message stream and write messages to file.
        Similar to Console but writes to file instead of stdout.
        Excludes ToolCall-related messages from being written.
        
        Args:
            stream: Message stream to process
            output_stats: If True, will output stats summary
            
        Returns:
            last_processed: TaskResult or Response
        """
        start_time = time.time()
        total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        
        last_processed: Optional[T] = None
        streaming_chunks: List[str] = []
        
        async for message in stream:
            if isinstance(message, TaskResult):
                duration = time.time() - start_time
                if output_stats:
                    output = (
                        f"{'-' * 10} Summary {'-' * 10}\n"
                        f"Number of messages: {len(message.messages)}\n"
                        f"Finish reason: {message.stop_reason}\n"
                        f"Total prompt tokens: {total_usage.prompt_tokens}\n"
                        f"Total completion tokens: {total_usage.completion_tokens}\n"
                        f"Duration: {duration:.2f} seconds\n"
                    )
                    await self.awrite(output, end="")
                
                last_processed = message  # type: ignore
                
            elif isinstance(message, Response):
                duration = time.time() - start_time
                
                # Write final response
                if isinstance(message.chat_message, MultiModalMessage):
                    final_content = message.chat_message.to_text(iterm=False)
                else:
                    final_content = message.chat_message.to_text()
                output = f"{'-' * 10} {message.chat_message.source} {'-' * 10}\n{final_content}\n"
                if message.chat_message.models_usage:
                    if output_stats:
                        output += f"[Prompt tokens: {message.chat_message.models_usage.prompt_tokens}, Completion tokens: {message.chat_message.models_usage.completion_tokens}]\n"
                    total_usage.completion_tokens += message.chat_message.models_usage.completion_tokens
                    total_usage.prompt_tokens += message.chat_message.models_usage.prompt_tokens
                await self.awrite(output, end="")
                
                # Write summary
                if output_stats:
                    if message.inner_messages is not None:
                        num_inner_messages = len(message.inner_messages)
                    else:
                        num_inner_messages = 0
                    output = (
                        f"{'-' * 10} Summary {'-' * 10}\n"
                        f"Number of inner messages: {num_inner_messages}\n"
                        f"Total prompt tokens: {total_usage.prompt_tokens}\n"
                        f"Total completion tokens: {total_usage.completion_tokens}\n"
                        f"Duration: {duration:.2f} seconds\n"
                    )
                    await self.awrite(output, end="")
                
                last_processed = message  # type: ignore
                
            # Skip UserInputRequestedEvent - don't write to file
            elif isinstance(message, UserInputRequestedEvent):
                continue
                
            else:
                # Cast required for mypy to be happy
                message = cast(BaseAgentEvent | BaseChatMessage, message)  # type: ignore
                
                # Skip ToolCall related messages (as requested)
                if isinstance(message, (ToolCallRequestEvent, ToolCallSummaryMessage, ToolCallExecutionEvent)):
                    continue
                
                if not streaming_chunks:
                    # Write message sender
                    await self.awrite(
                        f"{'-' * 10} {message.__class__.__name__} ({message.source}) {'-' * 10}"
                    )
                
                if isinstance(message, ModelClientStreamingChunkEvent):
                    await self.awrite(message.to_text(), end="")
                    streaming_chunks.append(message.content)
                else:
                    if streaming_chunks:
                        streaming_chunks.clear()
                        # Chunked messages are already written, so we just write a newline
                        await self.awrite("", end="\n")
                    elif isinstance(message, MultiModalMessage):
                        await self.awrite(message.to_text(iterm=False))
                    else:
                        await self.awrite(message.to_text())
                        
                    if message.models_usage:
                        if output_stats:
                            await self.awrite(
                                f"[Prompt tokens: {message.models_usage.prompt_tokens}, Completion tokens: {message.models_usage.completion_tokens}]"
                            )
                        total_usage.completion_tokens += message.models_usage.completion_tokens
                        total_usage.prompt_tokens += message.models_usage.prompt_tokens
        
        if last_processed is None:
            raise ValueError("No TaskResult or Response was processed.")
        
        return last_processed
