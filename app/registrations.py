"""需求登记会话存储（WebSocket 与 H5 上传共享）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

MAX_REGISTRATION_IMAGES = 3


@dataclass
class RegistrationSession:
    task_id: str
    demand_content: str
    userid: str
    chattype: str = "single"
    uploaded_images: list[dict[str, str]] = field(default_factory=list)


class RegistrationStore:
    def __init__(self) -> None:
        self._registrations: dict[str, RegistrationSession] = {}
        self._user_pending: dict[str, str] = {}
        self._lock = Lock()

    def create(
        self,
        *,
        task_id: str,
        demand_content: str,
        userid: str,
        chattype: str = "single",
    ) -> RegistrationSession:
        with self._lock:
            old_task_id = self._user_pending.get(userid)
            if old_task_id:
                self._registrations.pop(old_task_id, None)

            session = RegistrationSession(
                task_id=task_id,
                demand_content=demand_content,
                userid=userid,
                chattype=chattype,
            )
            self._registrations[task_id] = session
            self._user_pending[userid] = task_id
            return session

    def get(self, task_id: str) -> RegistrationSession | None:
        with self._lock:
            return self._registrations.get(task_id)

    def get_pending(self, userid: str) -> RegistrationSession | None:
        with self._lock:
            task_id = self._user_pending.get(userid)
            if not task_id:
                return None
            return self._registrations.get(task_id)

    def clear(self, task_id: str, userid: str) -> None:
        with self._lock:
            session = self._registrations.get(task_id)
            if session is None:
                return
            self._registrations.pop(task_id, None)
            if self._user_pending.get(userid) == session.task_id:
                self._user_pending.pop(userid, None)

    def add_uploaded_image(
        self,
        task_id: str,
        *,
        title: str,
        image_base64: str,
    ) -> tuple[bool, str]:
        with self._lock:
            session = self._registrations.get(task_id)
            if session is None:
                return False, "登记会话不存在或已过期"
            if len(session.uploaded_images) >= MAX_REGISTRATION_IMAGES:
                return False, f"最多上传 {MAX_REGISTRATION_IMAGES} 张图片"
            session.uploaded_images.append(
                {"title": title, "image_base64": image_base64}
            )
            return True, "ok"

    def remove_uploaded_image(self, task_id: str, index: int) -> tuple[bool, str]:
        with self._lock:
            session = self._registrations.get(task_id)
            if session is None:
                return False, "登记会话不存在或已过期"
            if index < 0 or index >= len(session.uploaded_images):
                return False, "图片不存在"
            session.uploaded_images.pop(index)
            return True, "ok"

    def list_smartsheet_images(self, task_id: str) -> list[dict[str, str]]:
        with self._lock:
            session = self._registrations.get(task_id)
            if session is None:
                return []
            return list(session.uploaded_images)


registration_store = RegistrationStore()
