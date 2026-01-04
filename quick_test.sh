#!/bin/bash
# EVE-NG 快速连接测试脚本

echo "=========================================="
echo "EVE-NG 网络连接快速测试"
echo "=========================================="
echo ""

# 1. 检查pnet9接口配置
echo "[1] 检查pnet9接口配置..."
ifconfig pnet9 | grep "inet " || echo "❌ pnet9未配置IP地址"
echo ""

# 2. Ping测试AR路由器
echo "[2] Ping测试AR路由器 (192.168.10.1)..."
if ping -c 3 -W 2 192.168.10.1 > /dev/null 2>&1; then
    echo "✓ Ping成功 - 网络连通"
else
    echo "✗ Ping失败 - 请检查网络配置"
    exit 1
fi
echo ""

# 3. 检查SSH端口
echo "[3] 检查SSH端口 (22)..."
if timeout 3 bash -c "echo > /dev/tcp/192.168.10.1/22" 2>/dev/null; then
    echo "✓ SSH端口22开放"
else
    echo "✗ SSH端口22未开放或无响应"
fi
echo ""

# 4. 检查Telnet端口
echo "[4] 检查Telnet端口 (23)..."
if timeout 3 bash -c "echo > /dev/tcp/192.168.10.1/23" 2>/dev/null; then
    echo "✓ Telnet端口23开放"
else
    echo "⚠ Telnet端口23未开放（可选）"
fi
echo ""

# 5. 检查Python环境
echo "[5] 检查Python虚拟环境..."
if [ -d "/root/github/python-automation-learning/venv" ]; then
    echo "✓ 虚拟环境存在"
    source /root/github/python-automation-learning/venv/bin/activate
    
    # 检查必要的包
    if python -c "import paramiko" 2>/dev/null; then
        echo "✓ paramiko已安装"
    else
        echo "⚠ paramiko未安装 - 运行: pip install paramiko"
    fi
    
    if python -c "import colorama" 2>/dev/null; then
        echo "✓ colorama已安装"
    else
        echo "⚠ colorama未安装 - 运行: pip install colorama"
    fi
else
    echo "✗ 虚拟环境不存在"
fi
echo ""

echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 如果网络测试通过，运行Python测试脚本："
echo "   cd /root/github/python-automation-learning"
echo "   source venv/bin/activate"
echo "   python test_eve_connection.py"
echo ""
echo "2. 如果需要手动SSH连接："
echo "   ssh admin@192.168.10.1"
echo ""
