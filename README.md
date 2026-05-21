# wecom-socket-proxy

企业微信**智能机器人 WebSocket 长连接**测试服务。与 [`wecom-proxy`](../wecom-proxy)（Webhook）并列，用于验证长连接能力：欢迎语、流式 echo、模板卡片、主动推送等。

## 与 wecom-proxy 的区别

| 项 | wecom-proxy | wecom-socket-proxy |
|---|---|---|
| 接入 | Webhook 短连接 | WebSocket 长连接 |
| 凭证 | Token + EncodingAESKey | **BotID + Secret** |
| 收消息 | 企微 POST 到公网 URL | **本服务出站连接** `wss://openws.work.weixin.qq.com` |
| 加解密 | 需要 | 不需要 |
| HTTP 8000 | 回调 + H5 上传 | **健康检查 + Webhook 占位 + H5 上传** |

> 同一机器人 API 模式只能二选一（Webhook 或长连接）。测试时请使用**独立测试机器人**，或在服务器上**停 wecom-proxy、启本服务**（同端口 8000，Nginx 无需修改）。

## 快速开始

```powershell
cd D:\aiworkspace\cursor_space\wecom-socket-proxy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# 编辑 .env，填入 WECOM_BOT_ID、WECOM_BOT_SECRET
python run.py
```

## 企微后台配置

1. 智能机器人 → API 模式 → 选择 **长连接**
2. 复制 **BotID**、**Secret** 到 `.env`
3. 保存后，启动本服务；日志应出现 `WebSocket 认证成功`

## HTTP 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务信息 |
| GET | `/health` | 健康检查 + WebSocket 连接状态 |
| GET/POST | `/wecom/aibot/callback` | **占位**（Nginx 兼容，不处理业务） |
| POST | `/api/test/push?chat_id=` | 测试主动推送（可选 chat_id） |
| GET | `/register/upload` | H5 图片上传页（需 token） |
| GET/POST | `/register/upload/api/*` | 上传状态、预览、上传/删除 |

## 需求登记流程

与 `wecom-proxy` 一致，经 WebSocket 收发卡片：

1. 发送 `登记 需求内容` → 确认卡片（含 H5 上传链接）
2. 点「上传图片」→ H5 上传（最多 3 张）
3. 返回卡片点「提交登记」→ 写入智能表格 → 成功/失败卡片

需在 `.env` 配置 `PUBLIC_BASE_URL`、`SMARTSHEET_WEBHOOK_URL` 等（见 `.env.example`）。

## 机器人内测试指令

| 输入 | 行为 |
|------|------|
| 进入单聊 | 欢迎模板卡片 |
| `登记 xxx` | 需求登记确认卡片 |
| `ping` / `测试` | 流式 echo |
| `/help` | 帮助 |
| `卡片` / `/card` | 示例交互卡片 |
| `主动推送` / `/push` | 测试 `aibot_send_msg` |
| 其他文本 | 流式 echo |

## 服务器切换（与 wecom-proxy 共用 Nginx）

```bash
sudo systemctl stop wecom-proxy
cd /path/to/wecom-socket-proxy && git pull
# 配置 .env 后
sudo systemctl start wecom-socket-proxy   # 仍监听 127.0.0.1:8000
curl http://127.0.0.1:8000/health
```

## 仓库

https://github.com/wumn-ops/wecom-socket-proxy
