"""WebSocket 消息与事件处理。"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from wecom_aibot_sdk import WSClient, generate_req_id

from app import connection_state
from app.template_cards import (
    build_button_clicked_card,
    build_demo_action_card,
    build_push_notice_card,
    build_welcome_card,
)

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "可用指令：\n"
    "- ping / 测试：流式 echo\n"
    "- /help：本帮助\n"
    "- 卡片 / /card：回复示例交互卡片\n"
    "- 主动推送 / /push：测试 aibot_send_msg\n"
    "- 其他文本：流式 echo 回复"
)


def _frame_body(frame: dict[str, Any]) -> dict[str, Any]:
    body = frame.get("body")
    return body if isinstance(body, dict) else {}


def _chat_target(body: dict[str, Any]) -> str:
    chatid = str(body.get("chatid") or "").strip()
    if chatid:
        return chatid
    from_info = body.get("from") or {}
    return str(from_info.get("userid") or "").strip()


def _userid(body: dict[str, Any]) -> str:
    from_info = body.get("from") or {}
    return str(from_info.get("userid") or "").strip()


def _remember_context(body: dict[str, Any]) -> None:
    chat_id = _chat_target(body)
    userid = _userid(body)
    if chat_id:
        connection_state.state.last_chat_id = chat_id
    if userid:
        connection_state.state.last_userid = userid
    connection_state.state.touch()


def _template_card_event(body: dict[str, Any]) -> dict[str, Any]:
    event = body.get("event") or {}
    if not isinstance(event, dict):
        return {}
    card_event = event.get("template_card_event") or {}
    return card_event if isinstance(card_event, dict) else {}


class BotMessageHandler:
    def __init__(self, client: WSClient) -> None:
        self._client = client

    async def on_enter_chat(self, frame: dict[str, Any]) -> None:
        body = _frame_body(frame)
        _remember_context(body)
        logger.info("进入会话 chat=%s user=%s", _chat_target(body), _userid(body))
        await self._client.reply_welcome(
            frame,
            {
                "msgtype": "template_card",
                "template_card": build_welcome_card(),
            },
        )

    async def on_template_card_event(self, frame: dict[str, Any]) -> None:
        body = _frame_body(frame)
        _remember_context(body)
        card_event = _template_card_event(body)
        event_key = str(card_event.get("event_key") or "")
        task_id = str(card_event.get("task_id") or "")
        if not task_id:
            logger.warning("模板卡片事件缺少 task_id: %s", card_event)
            return
        logger.info("模板卡片点击 event_key=%s task_id=%s", event_key, task_id)
        updated = build_button_clicked_card(event_key=event_key, task_id=task_id)
        await self._client.update_template_card(frame, updated)

    async def on_text(self, frame: dict[str, Any]) -> None:
        body = _frame_body(frame)
        _remember_context(body)
        text_obj = body.get("text") or {}
        content = str(text_obj.get("content") or "").strip()
        userid = _userid(body)
        logger.info("收到文本 user=%s content=%s", userid, content[:120])

        normalized = content.lower()
        if normalized in {"ping", "测试", "test"}:
            await self._reply_echo(frame, f"pong · 用户 `{userid}` · 长连接正常")
            return
        if normalized.startswith("/help") or content == "帮助":
            await self._reply_echo(frame, HELP_TEXT)
            return
        if normalized in {"/card", "卡片"}:
            await self._client.reply_template_card(
                frame,
                build_demo_action_card(user_text=content, userid=userid),
            )
            return
        if normalized in {"/push", "主动推送"}:
            await self._send_proactive_push()
            await self._reply_echo(frame, "已发送主动推送消息，请查看会话。")
            return

        await self._reply_echo(frame, f"echo: {content or '（空）'}")

    async def _reply_echo(self, frame: dict[str, Any], content: str) -> None:
        stream_id = generate_req_id("stream")
        await self._client.reply_stream(frame, stream_id, "处理中…", False)
        await asyncio.sleep(0.3)
        await self._client.reply_stream(frame, stream_id, content, True)

    async def send_proactive_push(self, chat_id: str | None = None) -> bool:
        target = (chat_id or connection_state.state.last_chat_id).strip()
        if not target:
            logger.warning("主动推送失败：无可用 chat_id")
            return False
        await self._client.send_message(
            target,
            {
                "msgtype": "template_card",
                "template_card": build_push_notice_card(),
            },
        )
        logger.info("主动推送成功 chat=%s", target)
        return True

    async def _send_proactive_push(self) -> None:
        ok = await self.send_proactive_push()
        if not ok:
            raise RuntimeError("无会话上下文，请先与机器人发一条消息")
