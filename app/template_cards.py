"""企业微信模板卡片构建（101032，长连接模式示例）。"""

from __future__ import annotations

import re
import uuid
from typing import Any


def new_task_id() -> str:
    return re.sub(r"[^0-9A-Za-z_\-@]", "", uuid.uuid4().hex)


def build_button_interaction_card(
    *,
    title: str,
    desc: str = "",
    sub_title: str = "",
    task_id: str | None = None,
    horizontal_items: list[dict[str, Any]] | None = None,
    buttons: list[dict[str, Any]] | None = None,
    source_desc: str = "wecom-socket-proxy",
) -> dict[str, Any]:
    card: dict[str, Any] = {
        "card_type": "button_interaction",
        "source": {
            "icon_url": "https://wework.qpic.cn/wwpic/252813_jOfDHtcISzuodLa_1629280209/0",
            "desc": source_desc,
            "desc_color": 0,
        },
        "main_title": {
            "title": title[:26],
            "desc": desc[:30] if desc else "",
        },
        "button_list": buttons
        or [
            {"text": "确认", "style": 1, "key": "confirm"},
            {"text": "取消", "style": 2, "key": "cancel"},
        ],
        "task_id": task_id or new_task_id(),
    }
    if sub_title:
        card["sub_title_text"] = sub_title[:112]
    if horizontal_items:
        card["horizontal_content_list"] = horizontal_items[:6]
    return card


def build_welcome_card(*, task_id: str | None = None) -> dict[str, Any]:
    return build_button_interaction_card(
        title="欢迎使用长连接机器人",
        desc="WebSocket 模式",
        sub_title="发送 /help 查看可用指令",
        task_id=task_id or new_task_id(),
        horizontal_items=[
            {"keyname": "模式", "value": "长连接"},
            {"keyname": "指令", "value": "/help"},
        ],
        buttons=[
            {"text": "示例卡片", "style": 1, "key": "demo_card"},
            {"text": "功能介绍", "style": 4, "key": "intro"},
        ],
    )


def build_demo_action_card(*, user_text: str, userid: str) -> dict[str, Any]:
    preview = user_text.strip()[:80] or "（空）"
    return build_button_interaction_card(
        title="示例交互卡片",
        desc="点击按钮可更新卡片",
        sub_title=f"您的输入：{preview}",
        task_id=new_task_id(),
        horizontal_items=[
            {"keyname": "用户", "value": userid[:26]},
            {"keyname": "提示", "value": "长连接 WS 测试"},
        ],
        buttons=[
            {"text": "确认", "style": 1, "key": "confirm"},
            {"text": "取消", "style": 2, "key": "cancel"},
        ],
    )


def build_button_clicked_card(*, event_key: str, task_id: str) -> dict[str, Any]:
    labels = {
        "confirm": "确认",
        "cancel": "取消",
        "demo_card": "示例卡片",
        "intro": "功能介绍",
        "start": "开始咨询",
    }
    action = labels.get(event_key, event_key or "未知")
    return build_button_interaction_card(
        title="操作已收到",
        desc="长连接卡片已更新",
        sub_title=f"您点击了：{action}",
        task_id=task_id,
        horizontal_items=[
            {"keyname": "操作", "value": action[:26]},
            {"keyname": "状态", "value": "已处理"},
        ],
        buttons=[
            {"text": "已完成", "style": 4, "key": "done"},
        ],
    )


def build_push_notice_card(*, title: str = "主动推送测试") -> dict[str, Any]:
    return build_button_interaction_card(
        title=title[:26],
        desc="aibot_send_msg",
        sub_title="这是一条主动推送的模板卡片",
        task_id=new_task_id(),
        horizontal_items=[
            {"keyname": "来源", "value": "长连接主动推送"},
        ],
        buttons=[
            {"text": "知道了", "style": 4, "key": "push_ack"},
        ],
    )
