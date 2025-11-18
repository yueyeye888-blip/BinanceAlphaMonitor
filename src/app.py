#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NTX Binance Alpha Monitor
实时监控币安 Alpha 新增代币
"""

import json
import os
import threading
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List

import requests
from flask import Flask, request, jsonify, send_from_directory

# =============== 配置 ===============

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config_files", "config.json")
STATE_PATH = os.path.join(ROOT, "data", "monitor_state.json")
LOGS_DIR = os.path.join(ROOT, "logs")

# 币安 Alpha API
BINANCE_ALPHA_API = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"

# 创建目录
os.makedirs(os.path.join(ROOT, "config_files"), exist_ok=True)
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# =============== 日志配置 ===============

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============== Flask 应用 ===============

app = Flask(__name__, static_folder=os.path.join(ROOT, 'static'))

# =============== 全局状态 ===============

monitor_state = {
    "last_check": "",
    "tokens": [],
    "token_count": 0
}

# =============== 配置管理 ===============

def ensure_config():
    """确保配置文件存在"""
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "webui_port": 5002,
            "check_interval": 300,  # 5分钟检查一次
            "notify_method": "telegram",
            "notify_targets": [
                {
                    "name": "NTX Community",
                    "bot_token": "8331180504:AAFU-JyITKlfH7mvqrz5tspcvS2VTseW0yI",
                    "chat_id": "-1002436131413",
                    "enabled": True
                }
            ]
        }
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        logger.info(f"已创建默认配置: {CONFIG_PATH}")


def load_config():
    """加载配置"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {}


def save_config(cfg: dict):
    """保存配置"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存配置失败: {e}")


def load_state():
    """加载状态"""
    try:
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载状态失败: {e}")
    return {"last_check": "", "tokens": [], "token_count": 0}


def save_state(state: dict):
    """保存状态"""
    try:
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存状态失败: {e}")


# =============== 币安 Alpha API ===============

def fetch_alpha_tokens():
    """获取币安 Alpha 代币列表"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get(BINANCE_ALPHA_API, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == '000000':
                return data.get('data', [])
        logger.error(f"API请求失败: {response.status_code}")
    except Exception as e:
        logger.error(f"获取Alpha代币失败: {e}")
    
    return []


# =============== Telegram 推送 ===============

def send_telegram(bot_token: str, chat_id: str, text: str):
    """发送Telegram消息"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"Telegram推送成功: {chat_id}")
            return True
        else:
            logger.error(f"Telegram推送失败: {response.status_code}")
    except Exception as e:
        logger.error(f"Telegram推送异常: {e}")
    
    return False


def notify_new_token(token: dict):
    """通知新代币"""
    cfg = load_config()
    
    if cfg.get('notify_method') not in ['telegram', 'both']:
        return
    
    # 构建消息
    message = f"""🚀 <b>币安 Alpha 新币上线!</b>

📌 <b>名称:</b> {token.get('name')}
🔤 <b>代号:</b> {token.get('symbol')}
🆔 <b>Alpha ID:</b> {token.get('alphaId')}
⛓ <b>链:</b> {token.get('chainId')}
📜 <b>合约:</b> <code>{token.get('contractAddress', 'N/A')}</code>

⏰ <b>发现时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💡 由 NTX Quest Radar 提供"""
    
    # 推送到所有启用的目标
    for target in cfg.get('notify_targets', []):
        if target.get('enabled', True):
            send_telegram(
                target.get('bot_token'),
                target.get('chat_id'),
                message
            )
            time.sleep(2)  # 增加间隔,避免429频率限制


# =============== 监控循环 ===============

def monitor_loop():
    """监控循环"""
    global monitor_state
    
    logger.info("监控循环已启动")
    
    # 加载上次状态
    monitor_state = load_state()
    is_first_run = not monitor_state.get('tokens')  # 判断是否首次运行
    
    while True:
        try:
            logger.info("检查币安 Alpha 新币...")
            
            # 获取当前代币列表
            current_tokens = fetch_alpha_tokens()
            
            if not current_tokens:
                logger.warning("未获取到代币数据")
                time.sleep(60)
                continue
            
            # 提取 alphaId 作为唯一标识
            current_ids = {t.get('alphaId') for t in current_tokens}
            previous_ids = {t.get('alphaId') for t in monitor_state.get('tokens', [])}
            
            # 检测新增代币
            new_ids = current_ids - previous_ids
            
            if new_ids:
                if is_first_run:
                    logger.info(f"首次运行: 发现 {len(current_ids)} 个代币,跳过推送")
                    is_first_run = False
                else:
                    logger.info(f"🚀 发现 {len(new_ids)} 个新币!")
                    
                    # 找出新币详情并推送
                    for token in current_tokens:
                        if token.get('alphaId') in new_ids:
                            logger.info(f"新币: {token.get('symbol')} ({token.get('name')})")
                            notify_new_token(token)
            else:
                logger.info("✓ 没有新币上线")
            
            # 更新状态
            monitor_state = {
                "last_check": datetime.now(timezone.utc).isoformat(),
                "tokens": current_tokens[:100],  # 只保存最新100个
                "token_count": len(current_tokens),
                "new_count": len(new_ids) if not is_first_run else 0
            }
            save_state(monitor_state)
            
            # 等待下次检查
            cfg = load_config()
            interval = cfg.get('check_interval', 300)
            logger.info(f"等待 {interval} 秒后下次检查...")
            time.sleep(interval)
            
        except Exception as e:
            logger.error(f"监控循环异常: {e}")
            time.sleep(60)


def start_monitor():
    """启动监控线程"""
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    logger.info("监控线程已启动")


# =============== Web 路由 ===============

@app.route('/')
def index():
    """首页"""
    tokens = monitor_state.get('tokens', [])[:20]  # 显示最新20个
    last_check = monitor_state.get('last_check', '')
    token_count = monitor_state.get('token_count', 0)
    new_count = monitor_state.get('new_count', 0)
    
    # 格式化时间
    check_time = "从未检查"
    if last_check:
        try:
            dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            check_time = dt.strftime('%m-%d %H:%M')
        except:
            pass
    
    # 配置信息
    cfg = load_config()
    interval_min = cfg.get('check_interval', 300) // 60
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>NTX Binance Alpha Monitor</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                background: rgba(255,255,255,0.95);
                border-radius: 16px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #667eea;
                font-size: 32px;
                margin-bottom: 10px;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 20px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
            }}
            .stat-value {{
                font-size: 36px;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .stat-label {{
                opacity: 0.9;
                font-size: 14px;
            }}
            .tokens {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
            }}
            .token-card {{
                background: rgba(255,255,255,0.95);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }}
            .token-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            }}
            .token-symbol {{
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 10px;
            }}
            .token-name {{
                color: #666;
                margin-bottom: 15px;
            }}
            .token-info {{
                font-size: 13px;
                color: #888;
                line-height: 1.8;
            }}
            .token-info div {{
                padding: 2px 0;
            }}
            .btn-manage {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                margin-top: 20px;
                transition: opacity 0.2s;
            }}
            .btn-manage:hover {{
                opacity: 0.9;
            }}
            .status-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                background: #10b981;
                color: white;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>
                    🚀 NTX Binance Alpha Monitor
                    <span class="status-badge">运行中</span>
                </h1>
                <p class="subtitle">实时监控币安 Alpha 新币上线 · 每 {interval_min} 分钟检查一次</p>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value">{token_count}</div>
                        <div class="stat-label">总代币数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{new_count}</div>
                        <div class="stat-label">本次新增</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{len(tokens)}</div>
                        <div class="stat-label">显示数量</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{check_time}</div>
                        <div class="stat-label">最后检查</div>
                    </div>
                </div>
                
                <a href="/manage" class="btn-manage">⚙️ 管理配置</a>
            </div>
            
            <div class="tokens">
    """
    
    for token in tokens:
        contract = token.get('contractAddress', 'N/A')
        if len(contract) > 20:
            contract = contract[:10] + '...' + contract[-8:]
        
        html += f"""
                <div class="token-card">
                    <div class="token-symbol">{token.get('symbol', 'N/A')}</div>
                    <div class="token-name">{token.get('name', 'Unknown')}</div>
                    <div class="token-info">
                        <div>🆔 ID: {token.get('alphaId', 'N/A')}</div>
                        <div>⛓ Chain: {token.get('chainId', 'N/A')}</div>
                        <div>📜 Contract: {contract}</div>
                    </div>
                </div>
        """
    
    html += """
            </div>
        </div>
        
        <script>
            // 自动刷新
            setTimeout(() => location.reload(), 300000);  // 5分钟刷新
        </script>
    </body>
    </html>
    """
    
    return html


@app.route('/manage')
def manage():
    """管理页面"""
    cfg = load_config()
    
    targets_html = ""
    for i, target in enumerate(cfg.get('notify_targets', [])):
        enabled = "✅" if target.get('enabled', True) else "❌"
        targets_html += f"""
        <tr>
            <td>{target.get('name', 'N/A')}</td>
            <td>{enabled}</td>
            <td>{target.get('chat_id', 'N/A')}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>管理配置 - NTX Binance Alpha Monitor</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: rgba(255,255,255,0.95);
                border-radius: 16px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #667eea; margin-bottom: 30px; }}
            h2 {{ color: #764ba2; margin: 30px 0 15px; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{ background: #f5f5f5; }}
            .btn {{ 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                text-decoration: none;
                display: inline-block;
                margin: 10px 5px 0 0;
            }}
            input, select {{
                width: 100%;
                padding: 10px;
                margin: 5px 0 15px;
                border: 1px solid #ddd;
                border-radius: 6px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚙️ 管理配置</h1>
            
            <h2>📊 当前配置</h2>
            <div>
                <strong>检查间隔:</strong> {cfg.get('check_interval', 300)} 秒<br>
                <strong>通知方式:</strong> {cfg.get('notify_method', 'none')}
            </div>
            
            <h2>📱 Telegram 推送目标</h2>
            <table>
                <tr>
                    <th>名称</th>
                    <th>状态</th>
                    <th>Chat ID</th>
                </tr>
                {targets_html}
            </table>
            
            <a href="/" class="btn">← 返回首页</a>
            <a href="/api/state" class="btn">📊 查看状态</a>
            <a href="/api/check_now" class="btn">🔍 立即检查</a>
            <a href="/api/test_push" class="btn">📤 测试推送</a>
            
            <script>
                // 拦截测试推送点击
                document.querySelectorAll('a[href="/api/test_push"], a[href="/api/check_now"]').forEach(btn => {{
                    btn.addEventListener('click', async (e) => {{
                        e.preventDefault();
                        const url = e.target.getAttribute('href');
                        const response = await fetch(url);
                        const data = await response.json();
                        alert(data.message || JSON.stringify(data));
                    }});
                }});
            </script>
        </div>
    </body>
    </html>
    """
    
    return html


@app.route('/api/state')
def api_state():
    """API: 获取状态"""
    return jsonify(monitor_state)


@app.route('/api/config')
def api_config():
    """API: 获取配置"""
    cfg = load_config()
    # 隐藏敏感信息
    for target in cfg.get('notify_targets', []):
        if 'bot_token' in target:
            target['bot_token'] = target['bot_token'][:10] + '...'
    return jsonify(cfg)


@app.route('/api/test_push')
def api_test_push():
    """API: 测试推送"""
    try:
        test_token = {
            'name': '测试代币',
            'symbol': 'TEST',
            'alphaId': 'test-123',
            'chainId': 'ETH',
            'contractAddress': '0x1234567890abcdef'
        }
        notify_new_token(test_token)
        return jsonify({"status": "success", "message": "测试推送已发送"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/check_now')
def api_check_now():
    """API: 立即检查"""
    try:
        current_tokens = fetch_alpha_tokens()
        if not current_tokens:
            return jsonify({"status": "error", "message": "无法获取代币数据"}), 500
        
        current_ids = {t.get('alphaId') for t in current_tokens}
        previous_ids = {t.get('alphaId') for t in monitor_state.get('tokens', [])}
        new_ids = current_ids - previous_ids
        
        return jsonify({
            "status": "success",
            "total": len(current_tokens),
            "new": len(new_ids),
            "message": f"检查完成: 总共 {len(current_tokens)} 个代币, 新增 {len(new_ids)} 个"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# =============== 主程序 ===============

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("NTX Binance Alpha Monitor 启动中...")
    logger.info("=" * 60)
    
    # 确保配置存在
    ensure_config()
    
    # 加载配置
    cfg = load_config()
    port = cfg.get('webui_port', 5002)
    
    # 启动监控线程
    start_monitor()
    
    # 启动 Flask
    logger.info(f"Web UI: http://localhost:{port}")
    logger.info(f"管理页面: http://localhost:{port}/manage")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )
