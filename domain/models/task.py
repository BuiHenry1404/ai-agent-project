from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Trạng thái của task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Loại task - hiện tại chỉ dùng Study Planning"""
    STUDY_PLANNING = "study_planning"


class CreateTaskRequest(BaseModel):
    """Request tạo mới Study Planning task"""
    task_type: TaskType = Field(default=TaskType.STUDY_PLANNING, description="Loại task (cố định: study_planning)")
    user_message: str = Field(..., description="Tin nhắn ban đầu của người dùng")
    llm_provider: str = Field(default="gemini", description="LLM provider (mặc định: gemini)")
    max_turns: int = Field(default=10, description="Số lượt hội thoại tối đa")
    user_id: Optional[str] = Field(None, description="ID người dùng")


class ConversationMessage(BaseModel):
    """Tin nhắn hội thoại giữa user và agent"""
    agent_name: str = Field(..., description="Tên agent")
    message: str = Field(..., description="Nội dung tin nhắn")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Thời gian gửi")
    message_type: str = Field(default="text", description="Loại tin nhắn (text, tool_call,...)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Thông tin phụ")


class TaskResponse(BaseModel):
    """Phản hồi khi thao tác với task"""
    task_id: str = Field(..., description="ID task")
    status: TaskStatus = Field(..., description="Trạng thái hiện tại")
    task_type: TaskType = Field(..., description="Loại task")
    user_message: str = Field(..., description="Tin nhắn ban đầu")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Thời gian tạo")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Thời gian cập nhật cuối")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="Lịch sử hội thoại")
    result: Optional[Dict[str, Any]] = Field(None, description="Kết quả (ví dụ JSON lịch học)")
    error_message: Optional[str] = Field(None, description="Thông báo lỗi nếu thất bại")


class TaskUpdateRequest(BaseModel):
    """Request cập nhật task"""
    status: Optional[TaskStatus] = Field(None, description="Trạng thái mới")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="Cập nhật lịch sử hội thoại")
    result: Optional[Dict[str, Any]] = Field(None, description="Cập nhật kết quả")
    error_message: Optional[str] = Field(None, description="Cập nhật thông báo lỗi")


class TaskListResponse(BaseModel):
    """Danh sách task"""
    tasks: List[TaskResponse] = Field(..., description="Danh sách task")
    total: int = Field(..., description="Tổng số task")

