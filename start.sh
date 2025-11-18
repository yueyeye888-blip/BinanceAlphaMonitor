#!/bin/bash

# NTX Binance Alpha Monitor - 启动脚本

PROJECT_DIR="/Users/xingxiu/Desktop/Glaxe 项目抓取备份/BinanceAlphaMonitor"
cd "$PROJECT_DIR"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}NTX Binance Alpha Monitor${NC}"
echo -e "${BLUE}================================${NC}"

# 检查端口
if lsof -ti:5002 > /dev/null; then
    echo -e "${YELLOW}⚠️  端口 5002 已被占用${NC}"
    read -p "是否停止现有服务? (y/n): " answer
    if [ "$answer" = "y" ]; then
        echo "停止现有服务..."
        lsof -ti:5002 | xargs kill -9 2>/dev/null
        sleep 2
        echo -e "${GREEN}✓ 已停止${NC}"
    else
        echo "退出启动"
        exit 0
    fi
fi

# 检查 Python 依赖
if ! python3 -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  缺少依赖,正在安装...${NC}"
    pip3 install -r requirements.txt
fi

# 启动服务
echo -e "${GREEN}🚀 启动服务...${NC}"
echo ""

# 方式1: 前台运行(可以看到日志)
python3 src/app.py

# 方式2: 后台运行(取消注释以使用)
# nohup python3 src/app.py > logs/app.log 2>&1 &
# echo -e "${GREEN}✓ 服务已在后台启动${NC}"
# echo -e "${BLUE}📊 Web UI: http://localhost:5002${NC}"
# echo -e "${BLUE}📝 日志: tail -f logs/app.log${NC}"
