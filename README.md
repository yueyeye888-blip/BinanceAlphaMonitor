# NTX Binance Meme Rush Monitor

🔥 实时监控币安 Meme Rush 排行榜,第一时间发现新上榜的 Meme 币!

## ✨ 功能特性

- 🔄 自动监控 Binance Meme Rush BSC 链排行榜
- 📱 Telegram 实时推送新上榜代币
- 🎨 精美的 Web 界面
- 🤖 使用 Selenium 自动化抓取
- ⚙️ 可配置检查间隔和推送方式
- 💾 本地状态持久化

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

需要安装 Google Chrome 浏览器(ChromeDriver 会自动下载)

### 2. 配置

首次运行会自动生成配置文件 `config_files/config.json`:

```json
{
  "webui_port": 5002,
  "check_interval": 300,
  "notify_method": "telegram",
  "headless": true,
  "notify_targets": [...]
}
```

### 3. 启动服务

```bash
# 方式1: 直接运行
python3 src/app_meme.py

# 方式2: 使用启动脚本
./start.sh
```

### 4. 访问界面

- Web UI: http://localhost:5002
- 管理页面: http://localhost:5002/manage

## 📊 监控说明

- **目标页面**: https://web3.binance.com/zh-CN/meme-rush/rank?chain=bsc
- **监控链**: BSC (Binance Smart Chain)
- **检查间隔**: 默认 5 分钟
- **推送方式**: Telegram

## 🔧 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| webui_port | Web 界面端口 | 5002 |
| check_interval | 检查间隔(秒) | 300 |
| notify_method | 通知方式 | telegram |
| headless | 无头模式 | true |

## 📱 Telegram 推送

新币上榜时会推送消息,包含:
- 排名
- 代币信息
- 上榜时间
- 查看链接

## 🛠️ 技术栈

- **后端**: Python 3.9+, Flask 2.0.3
- **抓取**: Selenium + Chrome WebDriver
- **推送**: Telegram Bot API
- **数据**: JSON 本地存储

## 📝 API 接口

- `GET /` - 首页
- `GET /manage` - 管理页面
- `GET /api/state` - 获取监控状态
- `GET /api/config` - 获取配置信息
- `GET /api/check_now` - 立即检查

## 🔒 注意事项

1. 需要安装 Chrome 浏览器
2. 首次运行会自动下载 ChromeDriver
3. 无头模式可节省资源
4. 建议检查间隔不低于 300 秒

## 📦 项目结构

```
BinanceMemeMonitor/
├── src/
│   ├── __init__.py
│   └── app_meme.py          # 主程序
├── config_files/
│   └── config.json          # 配置文件
├── data/
│   └── monitor_state.json   # 监控状态
├── logs/
│   ├── app.log             # 运行日志
│   └── page_source.html    # 页面源码(调试)
├── requirements.txt
├── start.sh                # 启动脚本
├── test_api.py            # API 测试工具
└── README.md
```

## 🌟 由 NTX Quest Radar 提供

Monitor your Web3 journey! 🚀
