#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查找 Binance Web3 Alpha 积分活动 API
"""

import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 尝试的 API 端点列表
apis = [
    "https://www.binance.com/bapi/composite/v1/public/walletdirect/alphaproject/public-project-list",
    "https://www.binance.com/bapi/composite/v1/public/wallet-direct/alpha/project-list",
    "https://www.binance.com/bapi/growth/v1/public/quest/alpha/list",
    "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20",
    "https://www.binance.com/bapi/composite/v1/public/wallet-direct/project/list",
]

print("🔍 正在查找 Binance Web3 Alpha 积分活动 API...\n")

for i, url in enumerate(apis, 1):
    print(f"[{i}/{len(apis)}] 测试: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"    状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"    ✓ JSON 解析成功")
                print(f"    返回字段: {list(data.keys())}")
                
                # 显示部分数据
                if 'data' in data:
                    print(f"    Data 类型: {type(data['data'])}")
                    if isinstance(data['data'], dict):
                        print(f"    Data 字段: {list(data['data'].keys())}")
                    elif isinstance(data['data'], list):
                        print(f"    Data 长度: {len(data['data'])}")
                        if data['data']:
                            print(f"    第一项字段: {list(data['data'][0].keys())}")
                
                print()
            except:
                print(f"    × JSON 解析失败")
                print(f"    内容: {response.text[:200]}")
                print()
        else:
            print(f"    × 请求失败")
            print()
            
    except Exception as e:
        print(f"    × 错误: {e}\n")

print("=" * 60)
print("尝试搜索文档中的关键词...")

# 尝试搜索相关信息
search_url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20"
try:
    response = requests.get(search_url, headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 找到 {len(data.get('data', {}).get('catalogs', []))} 个文章分类")
except:
    pass
