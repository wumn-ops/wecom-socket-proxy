"""智能表格查询记录（get_records，101167）。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings
from app.wecom_token import get_corp_access_token_provider

logger = logging.getLogger(__name__)

_QYAPI = "https://qyapi.weixin.qq.com/cgi-bin/wedoc/smartsheet/get_records"


@dataclass(frozen=True)
class SmartsheetRecord:
    record_id: str
    submitter_userid: str
    progress_text: str
    demand_content: str
    system_name: str


def parse_select_text(value: Any) -> str:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return str(first.get("text") or "").strip()
    return ""


def parse_user_id(value: Any) -> str:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return str(first.get("user_id") or "").strip()
    return ""


def parse_text_field(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return str(first.get("text") or "").strip()
    return ""


def _normalize_record(raw: dict[str, Any]) -> SmartsheetRecord | None:
    settings = get_settings()
    values = raw.get("values") or {}
    record_id = str(raw.get("record_id") or "").strip()
    if not record_id:
        return None

    return SmartsheetRecord(
        record_id=record_id,
        submitter_userid=parse_user_id(values.get(settings.smartsheet_field_submitter)),
        progress_text=parse_select_text(values.get(settings.smartsheet_field_progress)),
        demand_content=parse_text_field(values.get(settings.smartsheet_field_demand_content)),
        system_name=parse_text_field(values.get(settings.smartsheet_field_system)),
    )


def fetch_records_page(*, offset: int = 0, limit: int = 100) -> tuple[list[dict[str, Any]], bool, int]:
    """拉取一页原始记录，返回 (records, has_more, next_offset)。"""
    settings = get_settings()
    provider = get_corp_access_token_provider()
    if provider is None:
        raise RuntimeError("未配置 WECOM_CORP_ID / WECOM_CORP_SECRET")
    if not settings.smartsheet_docid or not settings.smartsheet_sheet_id:
        raise RuntimeError("未配置 SMARTSHEET_DOCID / SMARTSHEET_SHEET_ID")

    access_token = provider.get_access_token()
    payload = {
        "docid": settings.smartsheet_docid,
        "sheet_id": settings.smartsheet_sheet_id,
        "key_type": "CELL_VALUE_KEY_TYPE_FIELD_ID",
        "field_ids": [
            settings.smartsheet_field_progress,
            settings.smartsheet_field_submitter,
            settings.smartsheet_field_demand_content,
            settings.smartsheet_field_system,
        ],
        "offset": offset,
        "limit": limit,
    }

    response = httpx.post(
        _QYAPI,
        params={"access_token": access_token},
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("errcode", 0) != 0:
        raise RuntimeError(
            f"get_records errcode={data.get('errcode')} errmsg={data.get('errmsg')}"
        )

    records = data.get("records") or []
    has_more = bool(data.get("has_more"))
    next_offset = int(data.get("next") or (offset + len(records)))
    return records, has_more, next_offset


def fetch_launched_records() -> list[SmartsheetRecord]:
    """拉取进度为「已上线」且含提出人的记录。"""
    settings = get_settings()
    target_progress = settings.launch_progress_value.strip()
    matched: list[SmartsheetRecord] = []
    offset = 0

    while True:
        raw_records, has_more, offset = fetch_records_page(offset=offset, limit=100)
        for raw in raw_records:
            record = _normalize_record(raw)
            if record is None:
                continue
            if record.progress_text != target_progress:
                continue
            if not record.submitter_userid:
                logger.warning(
                    "跳过无提出人的已上线记录 record_id=%s",
                    record.record_id,
                )
                continue
            matched.append(record)

        if not has_more:
            break

    return matched
