import uuid
from datetime import datetime
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from domain.models.task import CreateTaskRequest, TaskResponse, TaskStatus
from infrastructure.llm import llm_manager
from services.StudyPlanningTeam import study_planning_manager

# logger = logging.getLogger(__name__)
router = APIRouter()

# Tạm thời lưu task trong bộ nhớ (Production nên dùng DB)
tasks_storage: dict[str, dict] = {}


@router.post("/", response_model=TaskResponse)
async def create_task(request: CreateTaskRequest, background_tasks: BackgroundTasks):
    """Tạo task mới và bắt đầu hội thoại với agent"""

    # Tạo ID duy nhất cho task
    task_id = str(uuid.uuid4())

    # Khởi tạo dữ liệu task
    task_data = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "task_type": request.task_type,
        "user_message": request.user_message,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "conversation_history": [],
        "result": None,
        "error_message": None,
        "llm_provider": request.llm_provider,
        "max_turns": request.max_turns,
        "user_id": request.user_id,
    }

    # Lưu vào storage
    tasks_storage[task_id] = task_data
    # logger.info(f"[TASK CREATED] {task_id} - Type: {request.task_type}")

    # Chạy xử lý nền
    background_tasks.add_task(run_agent_conversation, task_id, request)

    return TaskResponse(**task_data)


async def run_agent_conversation(task_id: str, request: CreateTaskRequest):
    """Xử lý hội thoại của agent trong background"""
    try:
        # Cập nhật trạng thái sang IN_PROGRESS
        tasks_storage[task_id]["status"] = TaskStatus.IN_PROGRESS
        tasks_storage[task_id]["updated_at"] = datetime.now()
        # logger.info(f"[TASK START] {task_id}")

        # Lấy client LLM
        llm_client = llm_manager.get_client()

        # Tạo nhóm agent
        team = study_planning_manager.create_team(task_id, llm_client, request.max_turns)

        # Chạy hội thoại
        result = await team.run_conversation(request.user_message)

        # Lưu kết quả
        tasks_storage[task_id]["status"] = TaskStatus.COMPLETED
        tasks_storage[task_id]["result"] = result
        tasks_storage[task_id]["conversation_history"] = result.get("conversation_history", [])
        tasks_storage[task_id]["updated_at"] = datetime.now()

        # logger.info(f"[TASK COMPLETED] {task_id}")

    except Exception as e:
        # Nếu lỗi thì lưu trạng thái FAILED
        tasks_storage[task_id]["status"] = TaskStatus.FAILED
        tasks_storage[task_id]["error_message"] = str(e)
        tasks_storage[task_id]["updated_at"] = datetime.now()

        # logger.error(f"[TASK FAILED] {task_id} - Error: {str(e)}", exc_info=True)
        # Dọn dẹp team sau khi xong
        study_planning_manager.remove_team(task_id)
        print(f"Error running conversation for task {task_id}: {str(e)}")



@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Lấy thông tin của một task"""
    task = tasks_storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task)
