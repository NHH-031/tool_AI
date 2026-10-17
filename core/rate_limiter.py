"""Rate Limiter Middleware & Dependency.

Triển khai Sliding Window Rate Limiting dựa trên IP của client, không cần thêm Redis
hay dependency bên thứ ba, bảo vệ các endpoint tài nguyên nặng (Export, AI Image Generation).
"""
from __future__ import annotations

import collections
import time
import threading
from typing import Dict, Deque
from fastapi import Request, HTTPException, status


class SlidingWindowRateLimiter:
    """Sliding Window Rate Limiter thread-safe."""

    def __init__(self, requests_per_minute: int = 60):
        self.rate = requests_per_minute
        self.window = 60.0  # seconds
        self._hits: Dict[str, Deque[float]] = collections.defaultdict(collections.deque)
        self._lock = threading.Lock()

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        with self._lock:
            queue = self._hits[client_ip]
            # Loại bỏ các hit đã quá 60s
            while queue and queue[0] < now - self.window:
                queue.popleft()

            if len(queue) >= self.rate:
                return False

            queue.append(now)
            return True

    def get_retry_after(self, client_ip: str) -> int:
        now = time.time()
        with self._lock:
            queue = self._hits.get(client_ip)
            if not queue:
                return 1
            earliest = queue[0]
            remaining = int(self.window - (now - earliest))
            return max(1, remaining)


# Default general limiter: 120 req/min
general_limiter = SlidingWindowRateLimiter(requests_per_minute=120)

# Strict limiter for expensive AI render/generation: 20 req/min
expensive_limiter = SlidingWindowRateLimiter(requests_per_minute=20)


async def check_general_rate_limit(request: Request) -> None:
    """Dependency kiểm tra rate limit cho các API thông thường."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not general_limiter.is_allowed(client_ip):
        retry_after = general_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quá giới hạn tần suất yêu cầu. Vui lòng thử lại sau {retry_after} giây.",
            headers={"Retry-After": str(retry_after)},
        )


async def check_expensive_rate_limit(request: Request) -> None:
    """Dependency kiểm tra rate limit cho các tác vụ AI nặng (render video, sinh ảnh)."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not expensive_limiter.is_allowed(client_ip):
        retry_after = expensive_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Tác vụ render/AI đang có quá nhiều yêu cầu từ IP của bạn. Vui lòng thử lại sau {retry_after} giây.",
            headers={"Retry-After": str(retry_after)},
        )
