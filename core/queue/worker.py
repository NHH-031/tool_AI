from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any, AsyncGenerator, Callable, Coroutine, Dict, List, Optional

from core.queue.tasks import TaskPayload, TaskStatus, TaskType

logger = logging.getLogger(__name__)

HandlerFunc = Callable[[TaskPayload], Coroutine[Any, Any, Dict[str, Any]]]


class WorkerQueue:
    """
    Hệ thống hàng đợi tác vụ độc lập (Decoupled Worker Queue):
    - Hỗ trợ Redis Queue & Redis Pub/Sub khi chạy trên môi trường Cloud/Docker Compose.
    - Tự động chuyển đổi sang Local Async Worker Queue (Asyncio + ThreadPool) khi chạy độc lập mà không cần Redis server.
    """

    def __init__(self, redis_url: Optional[str] = None, max_concurrent: int = 2):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.max_concurrent = max_concurrent
        self._handlers: Dict[str, HandlerFunc] = {}
        self._tasks: Dict[str, TaskPayload] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._work_queue: asyncio.Queue[TaskPayload] = asyncio.Queue()
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._redis_client = None
        self._is_redis_active = False

    async def initialize(self) -> None:
        """Thử kết nối Redis. Nếu không có Redis, kích hoạt chế độ Local Worker Queue."""
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(self.redis_url, socket_timeout=1.5)
            await client.ping()
            self._redis_client = client
            self._is_redis_active = True
            logger.info(f"[WorkerQueue] Đã kết nối thành công Redis tại {self.redis_url}")
        except Exception as e:
            self._is_redis_active = False
            self._redis_client = None
            logger.info(f"[WorkerQueue] Không có Redis server ({e}). Khởi chạy Local Async Worker Queue.")

        # Khởi động pool worker nodes
        self._running = True
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker_loop(worker_id=i + 1))
            self._worker_tasks.append(task)
        logger.info(f"[WorkerQueue] Đã khởi động {self.max_concurrent} worker nodes.")

    async def shutdown(self) -> None:
        """Dừng hoạt động hàng đợi và thu hồi tài nguyên worker."""
        self._running = False
        for task in self._worker_tasks:
            task.cancel()
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

        if self._redis_client and self._is_redis_active:
            try:
                await self._redis_client.close()
            except Exception:
                pass
        logger.info("[WorkerQueue] Đã dừng toàn bộ worker nodes.")

    def register_handler(self, task_type: str, handler: HandlerFunc) -> None:
        """Đăng ký hàm xử lý (task handler) cho từng loại tác vụ."""
        self._handlers[task_type] = handler
        logger.info(f"[WorkerQueue] Đăng ký handler cho task type '{task_type}'")

    async def enqueue(
        self,
        task_type: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> TaskPayload:
        """Đẩy một tác vụ vào hàng đợi."""
        tid = task_id or f"task-{uuid.uuid4().hex[:8]}"
        task = TaskPayload(
            task_id=tid,
            task_type=task_type,
            payload=payload,
            status=TaskStatus.PENDING,
            stage="Đang chờ trong hàng đợi tác vụ...",
        )
        self._tasks[tid] = task

        if self._is_redis_active and self._redis_client:
            try:
                await self._redis_client.hset(
                    "wb_tasks", tid, json.dumps(task.model_dump(), ensure_ascii=False)
                )
                await self._redis_client.lpush("wb_queue", tid)
            except Exception as e:
                logger.warning(f"[WorkerQueue] Lỗi lưu Redis, chuyển sang local queue: {e}")
                await self._work_queue.put(task)
        else:
            await self._work_queue.put(task)

        await self._broadcast_task_update(task)
        return task

    def get_task(self, task_id: str) -> Optional[TaskPayload]:
        """Lấy thông tin và trạng thái tác vụ theo ID."""
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[str] = None) -> List[TaskPayload]:
        """Liệt kê danh sách các tác vụ."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    async def update_progress(
        self,
        task_id: str,
        progress: float,
        stage: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        status: Optional[TaskStatus] = None,
    ) -> None:
        """Cập nhật tiến độ tác vụ và phát thông báo qua pub/sub."""
        task = self._tasks.get(task_id)
        if not task:
            return

        task.update_progress(progress, stage)
        if result is not None:
            task.result = result
        if status:
            task.status = status

        if self._is_redis_active and self._redis_client:
            try:
                await self._redis_client.hset(
                    "wb_tasks", task_id, json.dumps(task.model_dump(), ensure_ascii=False)
                )
                await self._redis_client.publish(
                    f"wb_channel:{task_id}", json.dumps(task.model_dump(), ensure_ascii=False)
                )
            except Exception as e:
                logger.debug(f"[WorkerQueue] Redis publish failed: {e}")

        await self._broadcast_task_update(task)

    async def _broadcast_task_update(self, task: TaskPayload) -> None:
        """Phát sự kiện cập nhật tiến độ cho các client đang kết nối SSE / WebSocket."""
        subscribers = self._subscribers.get(task.task_id, [])
        for q in subscribers:
            try:
                q.put_nowait(task.model_dump())
            except Exception:
                pass

    async def subscribe(self, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Lắng nghe luồng sự kiện cập nhật của một tác vụ (dùng cho Server-Sent Events)."""
        queue: asyncio.Queue = asyncio.Queue()
        if task_id not in self._subscribers:
            self._subscribers[task_id] = []
        self._subscribers[task_id].append(queue)

        # Gửi ngay trạng thái hiện tại nếu có
        curr_task = self.get_task(task_id)
        if curr_task:
            yield curr_task.model_dump()

        try:
            while True:
                data = await queue.get()
                yield data
                if data.get("status") in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    break
        finally:
            if task_id in self._subscribers and queue in self._subscribers[task_id]:
                self._subscribers[task_id].remove(queue)
                if not self._subscribers[task_id]:
                    del self._subscribers[task_id]

    async def _worker_loop(self, worker_id: int) -> None:
        """Vòng lặp tiêu thụ tác vụ của từng Worker Node."""
        logger.debug(f"[WorkerNode #{worker_id}] Sẵn sàng nhận job...")
        while self._running:
            task: Optional[TaskPayload] = None
            try:
                if self._is_redis_active and self._redis_client:
                    # Chờ lấy task từ Redis list
                    try:
                        pop_res = await self._redis_client.brpop("wb_queue", timeout=1)
                        if pop_res:
                            _, tid_bytes = pop_res
                            tid = tid_bytes.decode("utf-8") if isinstance(tid_bytes, bytes) else str(tid_bytes)
                            task = self._tasks.get(tid)
                    except Exception:
                        pass

                if not task:
                    try:
                        task = await asyncio.wait_for(self._work_queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        continue

                if not task:
                    continue

                handler = self._handlers.get(task.task_type)
                if not handler:
                    task.mark_failed(f"Không tìm thấy handler cho task type: {task.task_type}")
                    await self._broadcast_task_update(task)
                    continue

                # Thực thi handler
                task.mark_running(f"Worker #{worker_id} đang bắt đầu xử lý...")
                await self._broadcast_task_update(task)

                try:
                    result = await handler(task)
                    task.mark_completed(result=result, stage="Xử lý hoàn tất")
                except Exception as e:
                    logger.error(f"[WorkerNode #{worker_id}] Lỗi xử lý task {task.task_id}: {e}", exc_info=True)
                    task.mark_failed(error=str(e), stage="Lỗi xử lý tác vụ")

                await self._broadcast_task_update(task)

            except asyncio.CancelledError:
                break
            except Exception as e_loop:
                logger.error(f"[WorkerNode #{worker_id}] Ngoại lệ trong loop: {e_loop}", exc_info=True)
                await asyncio.sleep(0.5)


# Global singleton instance
global_worker_queue = WorkerQueue()


def get_worker_queue() -> WorkerQueue:
    return global_worker_queue
