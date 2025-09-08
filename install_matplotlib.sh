#!/bin/bash
# 安装matplotlib和相关依赖

echo "=== 安装matplotlib可视化依赖 ==="

# 检查Python版本
echo "1. 检查Python环境..."
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查pip
echo
echo "2. 检查pip..."
if command -v pip3 &> /dev/null; then
    pip3 --version
else
    echo "错误: pip3 未安装"
    exit 1
fi

# 安装matplotlib
echo
echo "3. 安装matplotlib..."
pip3 install matplotlib

# 检查安装结果
echo
echo "4. 验证安装..."
python3 -c "import matplotlib; print('matplotlib版本:', matplotlib.__version__)"

echo
echo "=== 安装完成 ==="
echo "现在可以使用完整的可视化功能:"
echo "python3 system_monitor.py --monitor --duration 60 --visualize"