#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查找 Binance Meme Rush API
"""

import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://web3.binance.com/zh-CN/meme-rush/rank?chain=bsc',
}

# 可能的 API 端点
apis = [
    # Meme Rush 相关
    "https://www.binance.com/bapi/composite/v1/public/meme-rush/rank/list?chain=bsc&page=1&size=100",
    "https://www.binance.com/bapi/composite/v1/public/meme/rush/rank?chain=bsc",
    "https://web3.binance.com/api/meme-rush/rank?chain=bsc",
    "https://www.binance.com/bapi/composite/v1/public/wallet-direct/meme/rank?chain=bsc&pageNum=1&pageSize=50",
    "https://www.binance.com/bapi/growth/v1/public/meme/rank/list?chain=bsc",
]

print("🔍 正在查找 Binance Meme Rush API...\n")
print("=" * 70)

for i, url in enumerate(apis, 1):
    print(f"\n[{i}/{len(apis)}] 测试: {url}")
    print("-" * 70)
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✓ JSON 解析成功!")
                print(f"返回字段: {list(data.keys())}")
                
                if data.get('code') == '000000' or data.get('success'):
                    print(f"✓✓✓ API 可用!")
                    
                    # 分析数据结构
                    if 'data' in data:
                        print(f"\nData 类型: {type(data['data'])}")
                        
                        if isinstance(data['data'], dict):
                            print(f"Data 字段: {list(data['data'].keys())}")
                            
                            # 查找列表数据
                            for key in ['list', 'items', 'ranks', 'tokens']:
                                if key in data['data']:
                                    items = data['data'][key]
                                    if items:
                                        print(f"\n找到列表: {key}, 长度: {len(items)}")
                                        print(f"第一项数据:")
                                        print(json.dumps(items[0], indent=2, ensure_ascii=False))
                                        break
                        
                        elif isinstance(data['data'], list) and data['data']:
                            print(f"Data 是列表, 长度: {len(data['data'])}")
                            print(f"第一项字段: {list(data['data'][0].keys())}")
                            print(f"\n第一项数据:")
                            print(json.dumps(data['data'][0], indent=2, ensure_ascii=False))
                
                else:
                    print(f"× Code: {data.get('code')}, Message: {data.get('message')}")
                    
            except json.JSONDecodeError:
                print(f"× JSON 解析失败")
                print(f"内容预览: {response.text[:300]}")
        else:
            print(f"× HTTP 错误")
            
    except requests.exceptions.Timeout:
        print(f"× 请求超时")
    except Exception as e:
        print(f"× 错误: {e}")

print("\n" + "=" * 70)
print("测试完成!")
