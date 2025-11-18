#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NTX Binance Meme Rush Monitor
实时监控币安 Meme Rush 排行榜
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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# =============== 配置 ===============

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config_files", "config.json")
STATE_PATH = os.path.join(ROOT, "data", "monitor_state.json")
LOGS_DIR = os.path.join(ROOT, "logs")

# Meme Rush URL
MEME_RUSH_URL = "https://web3.binance.com/zh-CN/meme-rush/rank?chain=bsc"

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

driver = None

# =============== 配置管理 ===============

def ensure_config():
    """确保配置文件存在"""
    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "webui_port": 5002,
            "check_interval": 300,
            "notify_method": "telegram",
            "headless": True,
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


# =============== Selenium 浏览器 ===============

def init_driver():
    """初始化 Selenium WebDriver"""
    global driver
    
    cfg = load_config()
    headless = cfg.get('headless', True)
    
    try:
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("✓ Selenium WebDriver 初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"× Selenium WebDriver 初始化失败: {e}")
        return False


def close_driver():
    """关闭浏览器"""
    global driver
    if driver:
        try:
            driver.quit()
            logger.info("✓ WebDriver 已关闭")
        except:
            pass


# =============== Meme Rush 抓取 ===============

def fetch_meme_tokens():
    """抓取 Meme Rush 代币列表"""
    global driver
    
    if not driver:
        if not init_driver():
            return []
    
    try:
        logger.info(f"访问页面: {MEME_RUSH_URL}")
        driver.get(MEME_RUSH_URL)
        
        # 等待页面加载
        wait = WebDriverWait(driver, 20)
        
        # 等待排行榜元素出现
        time.sleep(5)  # 额外等待 JavaScript 渲染
        
        # 尝试获取代币列表 (需要根据实际页面结构调整选择器)
        tokens = []
        
        # 方案1: 尝试获取表格行
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "tr[data-token], .token-row, [class*='rank-item']")
            logger.info(f"找到 {len(rows)} 个排行项")
            
            for i, row in enumerate(rows[:50]):  # 只取前50
                try:
                    # 提取代币信息 (需要根据实际HTML调整)
                    text = row.text
                    if text:
                        tokens.append({
                            "rank": i + 1,
                            "raw_text": text,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"方案1失败: {e}")
        
        # 方案2: 如果方案1失败,获取整个页面文本分析
        if not tokens:
            try:
                page_source = driver.page_source
                # 保存页面源码用于调试
                with open(os.path.join(LOGS_DIR, 'page_source.html'), 'w', encoding='utf-8') as f:
                    f.write(page_source)
                logger.info("已保存页面源码到 logs/page_source.html")
                
                # 尝试通过 JavaScript 获取数据
                script = """
                return Array.from(document.querySelectorAll('table tbody tr, [class*="rank"], [class*="token-item"]'))
                    .slice(0, 50)
                    .map((el, i) => ({
                        rank: i + 1,
                        text: el.innerText,
                        html: el.outerHTML.substring(0, 200)
                    }));
                """
                results = driver.execute_script(script)
                
                for item in results:
                    if item.get('text'):
                        tokens.append({
                            "rank": item['rank'],
                            "raw_text": item['text'],
                            "html_preview": item.get('html', ''),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                        
                logger.info(f"方案2找到 {len(tokens)} 个代币")
                
            except Exception as e:
                logger.error(f"方案2失败: {e}")
        
        return tokens
        
    except Exception as e:
        logger.error(f"抓取失败: {e}")
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


def notify_new_tokens(new_tokens: List[dict]):
    """通知新代币"""
    cfg = load_config()
    
    if cfg.get('notify_method') not in ['telegram', 'both']:
        return
    
    # 构建消息
    message = f"""🔥 <b>Binance Meme Rush 新币上榜!</b>

发现 {len(new_tokens)} 个新币进入排行榜:

"""
    
    for token in new_tokens[:10]:  # 最多显示10个
        rank = token.get('rank', '?')
        text = token.get('raw_text', 'Unknown')[:100]
        message += f"#{rank}. {text}\n"
    
    message += f"\n⏰ <b>检查时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"🔗 <b>查看详情:</b> {MEME_RUSH_URL}\n\n"
    message += "💡 由 NTX Quest Radar 提供"
    
    # 推送到所有启用的目标
    for target in cfg.get('notify_targets', []):
        if target.get('enabled', True):
            send_telegram(
                target.get('bot_token'),
                target.get('chat_id'),
                message
            )
            time.sleep(2)


# =============== 监控循环 ===============

def monitor_loop():
    """监控循环"""
    global monitor_state
    
    logger.info("监控循环已启动")
    
    # 初始化浏览器
    if not init_driver():
        logger.error("无法初始化浏览器,监控终止")
        return
    
    # 加载上次状态
    monitor_state = load_state()
    is_first_run = not monitor_state.get('tokens')
    
    while True:
        try:
            logger.info("检查 Meme Rush 排行榜...")
            
            # 获取当前代币列表
            current_tokens = fetch_meme_tokens()
            
            if not current_tokens:
                logger.warning("未获取到代币数据")
                time.sleep(60)
                continue
            
            # 提取标识进行比对
            current_texts = {t.get('raw_text', '') for t in current_tokens}
            previous_texts = {t.get('raw_text', '') for t in monitor_state.get('tokens', [])}
            
            # 检测新增代币
            new_texts = current_texts - previous_texts
            
            if new_texts:
                if is_first_run:
                    logger.info(f"首次运行: 发现 {len(current_tokens)} 个代币,跳过推送")
                    is_first_run = False
                else:
                    logger.info(f"🚀 发现 {len(new_texts)} 个新币!")
                    
                    # 找出新币详情并推送
                    new_token_details = [t for t in current_tokens if t.get('raw_text') in new_texts]
                    notify_new_tokens(new_token_details)
            else:
                logger.info("✓ 没有新币上榜")
            
            # 更新状态
            monitor_state = {
                "last_check": datetime.now(timezone.utc).isoformat(),
                "tokens": current_tokens[:100],
                "token_count": len(current_tokens),
                "new_count": len(new_texts) if not is_first_run else 0
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
    tokens = monitor_state.get('tokens', [])[:20]
    last_check = monitor_state.get('last_check', '')
    token_count = monitor_state.get('token_count', 0)
    new_count = monitor_state.get('new_count', 0)
    
    check_time = "从未检查"
    if last_check:
        try:
            dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            check_time = dt.strftime('%m-%d %H:%M')
        except:
            pass
    
    cfg = load_config()
    interval_min = cfg.get('check_interval', 300) // 60
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>NTX Binance Meme Rush Monitor</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
                color: #f5576c;
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
                background: linear-gradient(135deg, #f093fb, #f5576c);
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
                gap: 15px;
            }}
            .token-card {{
                background: rgba(255,255,255,0.95);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 16px rgba(0,0,0,0.1);
            }}
            .token-rank {{
                font-size: 24px;
                font-weight: bold;
                color: #f5576c;
                margin-bottom: 10px;
            }}
            .token-text {{
                color: #333;
                line-height: 1.6;
                white-space: pre-wrap;
            }}
            .btn-manage {{
                display: inline-block;
                background: linear-gradient(135deg, #f093fb, #f5576c);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                margin-top: 20px;
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
                    🔥 NTX Binance Meme Rush Monitor
                    <span class="status-badge">运行中</span>
                </h1>
                <p class="subtitle">实时监控币安 Meme Rush 排行榜 · 每 {interval_min} 分钟检查一次</p>
                
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
                <a href="{MEME_RUSH_URL}" target="_blank" class="btn-manage">🔗 查看原页面</a>
            </div>
            
            <div class="tokens">
    """
    
    for token in tokens:
        rank = token.get('rank', '?')
        text = token.get('raw_text', 'Unknown')
        
        html += f"""
                <div class="token-card">
                    <div class="token-rank">#{rank}</div>
                    <div class="token-text">{text}</div>
                </div>
        """
    
    html += """
            </div>
        </div>
        
        <script>
            setTimeout(() => location.reload(), 300000);
        </script>
    </body>
    </html>
    """
    
    return html


@app.route('/manage')
def manage():
    """管理页面"""
    cfg = load_config()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>管理配置 - NTX Binance Meme Rush Monitor</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
            }}
            h1 {{ color: #f5576c; margin-bottom: 30px; }}
            h2 {{ color: #f093fb; margin: 30px 0 15px; }}
            .info {{ padding: 15px; background: #f0f0f0; border-radius: 8px; margin: 10px 0; }}
            .btn {{ 
                background: linear-gradient(135deg, #f093fb, #f5576c);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                text-decoration: none;
                display: inline-block;
                margin: 10px 5px 0 0;
                cursor: pointer;
                border: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚙️ 管理配置</h1>
            
            <h2>📊 当前配置</h2>
            <div class="info">
                <strong>检查间隔:</strong> {cfg.get('check_interval', 300)} 秒<br>
                <strong>通知方式:</strong> {cfg.get('notify_method', 'none')}<br>
                <strong>无头模式:</strong> {'是' if cfg.get('headless', True) else '否'}
            </div>
            
            <h2>📱 Telegram 推送</h2>
            <div class="info">
                推送目标数: {len(cfg.get('notify_targets', []))}
            </div>
            
            <a href="/" class="btn">← 返回首页</a>
            <a href="/api/state" class="btn">📊 查看状态</a>
            <a href="/api/check_now" class="btn">🔍 立即检查</a>
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
    for target in cfg.get('notify_targets', []):
        if 'bot_token' in target:
            target['bot_token'] = target['bot_token'][:10] + '...'
    return jsonify(cfg)


@app.route('/api/check_now')
def api_check_now():
    """API: 立即检查"""
    try:
        tokens = fetch_meme_tokens()
        if not tokens:
            return jsonify({"status": "error", "message": "无法获取数据"}), 500
        
        return jsonify({
            "status": "success",
            "total": len(tokens),
            "message": f"检查完成: 总共 {len(tokens)} 个代币"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# =============== 主程序 ===============

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("NTX Binance Meme Rush Monitor 启动中...")
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
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
    finally:
        close_driver()
