#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 API 工具
"""

import requests
import json

BASE_URL = "http://localhost:5002"

def test_state():
    """测试获取状态"""
    print("\n=== 测试获取状态 ===")
    response = requests.get(f"{BASE_URL}/api/state")
    data = response.json()
    print(f"总代币数: {data.get('token_count')}")
    print(f"最后检查: {data.get('last_check')}")
    print(f"显示代币: {len(data.get('tokens', []))}")
    print(f"新增数量: {data.get('new_count', 0)}")

def test_config():
    """测试获取配置"""
    print("\n=== 测试获取配置 ===")
    response = requests.get(f"{BASE_URL}/api/config")
    data = response.json()
    print(f"检查间隔: {data.get('check_interval')} 秒")
    print(f"Web端口: {data.get('webui_port')}")
    print(f"通知方式: {data.get('notify_method')}")
    print(f"推送目标数: {len(data.get('notify_targets', []))}")

def test_check_now():
    """测试立即检查"""
    print("\n=== 测试立即检查 ===")
    response = requests.get(f"{BASE_URL}/api/check_now")
    data = response.json()
    print(f"状态: {data.get('status')}")
    print(f"消息: {data.get('message')}")
    if data.get('status') == 'success':
        print(f"总计: {data.get('total')}")
        print(f"新增: {data.get('new')}")

def test_push():
    """测试推送"""
    print("\n=== 测试推送 ===")
    response = requests.get(f"{BASE_URL}/api/test_push")
    data = response.json()
    print(f"状态: {data.get('status')}")
    print(f"消息: {data.get('message')}")

if __name__ == "__main__":
    try:
        print("🚀 NTX Binance Alpha Monitor - API 测试工具")
        print("=" * 60)
        
        test_state()
        test_config()
        test_check_now()
        
        # 询问是否测试推送
        answer = input("\n是否发送测试推送? (y/n): ")
        if answer.lower() == 'y':
            test_push()
        
        print("\n✅ 测试完成!")
        
    except requests.exceptions.ConnectionError:
        print("❌ 错误: 无法连接到服务,请确认服务正在运行")
    except Exception as e:
        print(f"❌ 错误: {e}")
