# Binance Alpha Monitor

币安 Alpha 新币监控系统 - 实时监控币安 Alpha 项目上新

## 功能特性

- ✅ 实时监控币安 Alpha 新增代币
- ✅ Telegram 多Bot/多群组推送
- ✅ Web UI 管理界面
- ✅ 自动去重检测
- ✅ 支持分类管理

## 快速开始

### 本地运行

```bash
# 安装依赖
pip3 install -r requirements.txt

# 启动服务
python3 src/app.py
```

访问: http://localhost:5002

### 服务器部署

```bash
# 部署到服务器
./deploy_to_server.sh
```

## 配置说明

编辑 `config_files/config.json`:

```json
{
  "webui_port": 5002,
  "notify_method": "telegram",
  "notify_targets": [
    {
      "name": "NTX Community",
      "bot_token": "YOUR_BOT_TOKEN",
      "chat_id": "YOUR_CHAT_ID",
      "enabled": true
    }
  ]
}
```

## 技术栈

- Python 3.6+
- Flask 2.0.3
- Binance Official API

## License

MIT
