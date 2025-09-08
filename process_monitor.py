#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Process Monitoring System
Supports monitoring single or multiple processes by process name or PID for resource usage
"""

import subprocess
import time
import json
import os
import signal
import sys
import argparse
import threading
from datetime import datetime
import logging
from collections import defaultdict
import glob
import statistics
import platform

# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    
    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

def colorize(text, color):
    """Apply color to text"""
    return f"{color}{text}{Colors.RESET}"

def print_header(title, width=120):
    """Print a formatted header"""
    print("\n" + "=" * width)
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(width)}{Colors.RESET}")
    print("=" * width)

def print_separator(width=120, char="-"):
    """Print a separator line"""
    print(f"{Colors.DIM}{char * width}{Colors.RESET}")

def print_success(message):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_warning(message):
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def print_error(message):
    """Print error message in red"""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


class PerformanceReportTemplate:
    def __init__(self, data_file=None, report_dir=None, command_params=None):
        self.data_file = data_file
        self.report_dir = report_dir
        self.data = None
        self.report_data = {}
        self.system_info = self.get_system_info()
        self.command_params = command_params or {}
        
    def get_system_info(self):
        """Get system information"""
        try:
            system = platform.system()
            machine = platform.machine()
            processor = platform.processor()
            return {
                'system': system,
                'machine': machine,
                'processor': processor,
                'platform': platform.platform()
            }
        except Exception as e:
            return {
                'system': 'Unknown',
                'machine': 'Unknown',
                'processor': 'Unknown',
                'platform': 'Unknown'
            }
    
    def load_data(self, data_file=None):
        """Load monitoring data"""
        if data_file:
            self.data_file = data_file
            
        if not self.data_file:
            return False
            
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✓ Successfully loaded data file: {self.data_file}")
            return True
        except Exception as e:
            print(f"✗ Failed to load data: {e}")
            return False
    
    def analyze_data(self):
        """Analyze monitoring data"""
        if not self.data:
            return False
        
        self.report_data = {}
        
        for process_name, process_data in self.data.items():
            if not process_data:
                continue
            
            # Extract metrics
            timestamps = [datetime.fromisoformat(item['timestamp']) for item in process_data]
            
            # Extract basic metrics (always available)
            cpu_data = [item['cpu_percent'] for item in process_data]
            memory_percent_data = [item['memory_percent'] for item in process_data]
            memory_mb_data = [item['memory_mb'] for item in process_data]
            
            # Extract optional metrics if they exist
            disk_read_data = [item.get('disk_read_bytes', 0) for item in process_data]
            disk_write_data = [item.get('disk_write_bytes', 0) for item in process_data]
            network_rx_data = [item.get('network_rx_bytes', 0) for item in process_data]
            network_tx_data = [item.get('network_tx_bytes', 0) for item in process_data]
            voluntary_switches_data = [item.get('voluntary_switches', 0) for item in process_data]
            involuntary_switches_data = [item.get('involuntary_switches', 0) for item in process_data]
            thread_count_data = [item.get('thread_count', 0) for item in process_data]
            
            # Calculate statistics
            analysis = {
                'process_name': process_name,
                'pid': process_data[0]['pid'],
                'command': process_data[0]['command'],
                'args': process_data[0]['args'],
                'data_points': len(process_data),
                'test_duration': (timestamps[-1] - timestamps[0]).total_seconds(),
                'start_time': timestamps[0],
                'end_time': timestamps[-1],
                'cpu': {
                    'avg': round(statistics.mean(cpu_data), 2),
                    'max': round(max(cpu_data), 2),
                    'min': round(min(cpu_data), 2),
                    'std': round(statistics.stdev(cpu_data) if len(cpu_data) > 1 else 0, 2),
                    'data': cpu_data
                },
                'memory_percent': {
                    'avg': round(statistics.mean(memory_percent_data), 2),
                    'max': round(max(memory_percent_data), 2),
                    'min': round(min(memory_percent_data), 2),
                    'std': round(statistics.stdev(memory_percent_data) if len(memory_percent_data) > 1 else 0, 2),
                    'data': memory_percent_data
                },
                'memory_mb': {
                    'avg': round(statistics.mean(memory_mb_data), 2),
                    'max': round(max(memory_mb_data), 2),
                    'min': round(min(memory_mb_data), 2),
                    'std': round(statistics.stdev(memory_mb_data) if len(memory_mb_data) > 1 else 0, 2),
                    'data': memory_mb_data
                },
                'rss_kb': process_data[0]['rss_kb'],
                'vsz_kb': process_data[0]['vsz_kb']
            }
            
            # Add optional metrics if they have non-zero data
            if any(disk_read_data) or any(disk_write_data):
                analysis['disk_io'] = {
                    'read_bytes': {
                        'avg': round(statistics.mean(disk_read_data), 2),
                        'max': round(max(disk_read_data), 2),
                        'min': round(min(disk_read_data), 2),
                        'std': round(statistics.stdev(disk_read_data) if len(disk_read_data) > 1 else 0, 2),
                        'data': disk_read_data
                    },
                    'write_bytes': {
                        'avg': round(statistics.mean(disk_write_data), 2),
                        'max': round(max(disk_write_data), 2),
                        'min': round(min(disk_write_data), 2),
                        'std': round(statistics.stdev(disk_write_data) if len(disk_write_data) > 1 else 0, 2),
                        'data': disk_write_data
                    }
                }
            
            if any(network_rx_data) or any(network_tx_data):
                analysis['network_io'] = {
                    'rx_bytes': {
                        'avg': round(statistics.mean(network_rx_data), 2),
                        'max': round(max(network_rx_data), 2),
                        'min': round(min(network_rx_data), 2),
                        'std': round(statistics.stdev(network_rx_data) if len(network_rx_data) > 1 else 0, 2),
                        'data': network_rx_data
                    },
                    'tx_bytes': {
                        'avg': round(statistics.mean(network_tx_data), 2),
                        'max': round(max(network_tx_data), 2),
                        'min': round(min(network_tx_data), 2),
                        'std': round(statistics.stdev(network_tx_data) if len(network_tx_data) > 1 else 0, 2),
                        'data': network_tx_data
                    }
                }
            
            if any(voluntary_switches_data) or any(involuntary_switches_data):
                analysis['context_switches'] = {
                    'voluntary': {
                        'avg': round(statistics.mean(voluntary_switches_data), 2),
                        'max': round(max(voluntary_switches_data), 2),
                        'min': round(min(voluntary_switches_data), 2),
                        'std': round(statistics.stdev(voluntary_switches_data) if len(voluntary_switches_data) > 1 else 0, 2),
                        'data': voluntary_switches_data
                    },
                    'involuntary': {
                        'avg': round(statistics.mean(involuntary_switches_data), 2),
                        'max': round(max(involuntary_switches_data), 2),
                        'min': round(min(involuntary_switches_data), 2),
                        'std': round(statistics.stdev(involuntary_switches_data) if len(involuntary_switches_data) > 1 else 0, 2),
                        'data': involuntary_switches_data
                    }
                }
            
            if any(thread_count_data):
                analysis['thread_count'] = {
                    'avg': round(statistics.mean(thread_count_data), 2),
                    'max': round(max(thread_count_data), 2),
                    'min': round(min(thread_count_data), 2),
                    'std': round(statistics.stdev(thread_count_data) if len(thread_count_data) > 1 else 0, 2),
                    'data': thread_count_data
                }
            
            self.report_data[process_name] = analysis
        
        print(f"✓ 数据分析完成，共分析 {len(self.report_data)} 个进程")
        return True
    
    def generate_summary_table(self):
        """Generate summary table"""
        if not self.report_data:
            return ""
        
        # Determine which metrics are available
        has_disk_io = any('disk_io' in data for data in self.report_data.values())
        has_network_io = any('network_io' in data for data in self.report_data.values())
        has_context_switches = any('context_switches' in data for data in self.report_data.values())
        has_thread_count = any('thread_count' in data for data in self.report_data.values())
        
        table = "## 性能指标汇总表\n\n"
        
        # Build table header
        header = "| 进程名称 | PID | CPU使用率(%) | 内存使用率(%) | 内存使用量(MB) |"
        if has_disk_io:
            header += " 磁盘读取(KB) | 磁盘写入(KB) |"
        if has_network_io:
            header += " 网络接收(KB) | 网络发送(KB) |"
        if has_context_switches:
            header += " 自愿切换 | 非自愿切换 |"
        if has_thread_count:
            header += " 线程数 |"
        header += " 测试时长(秒) |"
        
        table += header + "\n"
        
        # Build separator row
        separator = "|----------|-----|--------------|---------------|----------------|"
        if has_disk_io:
            separator += "--------------|--------------|"
        if has_network_io:
            separator += "--------------|--------------|"
        if has_context_switches:
            separator += "----------|----------|"
        if has_thread_count:
            separator += "--------|"
        separator += "--------------|"
        
        table += separator + "\n"
        
        # Build data rows
        for process_name, data in self.report_data.items():
            row = f"| {process_name} | {data['pid']} | {data['cpu']['avg']} | {data['memory_percent']['avg']} | {data['memory_mb']['avg']} |"
            
            if has_disk_io:
                if 'disk_io' in data:
                    row += f" {data['disk_io']['read_bytes']['avg']:.0f} | {data['disk_io']['write_bytes']['avg']:.0f} |"
                else:
                    row += " 0 | 0 |"
            
            if has_network_io:
                if 'network_io' in data:
                    row += f" {data['network_io']['rx_bytes']['avg']:.0f} | {data['network_io']['tx_bytes']['avg']:.0f} |"
                else:
                    row += " 0 | 0 |"
            
            if has_context_switches:
                if 'context_switches' in data:
                    row += f" {data['context_switches']['voluntary']['avg']:.0f} | {data['context_switches']['involuntary']['avg']:.0f} |"
                else:
                    row += " 0 | 0 |"
            
            if has_thread_count:
                if 'thread_count' in data:
                    row += f" {data['thread_count']['avg']:.0f} |"
                else:
                    row += " 0 |"
            
            row += f" {data['test_duration']:.0f} |"
            table += row + "\n"
        
        return table
    
    def generate_detailed_analysis(self):
        """Generate detailed analysis"""
        if not self.report_data:
            return ""
        
        analysis = "## 详细性能分析\n\n"
        
        for process_name, data in self.report_data.items():
            analysis += f"### {process_name} 详细分析\n\n"
            analysis += f"**基本信息**\n\n"
            analysis += f"- 进程ID: {data['pid']}\n"
            analysis += f"- 进程名称: {data['process_name']}\n"
            analysis += f"- 启动参数: `{data['args']}`\n"
            analysis += f"- 虚拟内存: {data['vsz_kb']:,} KB ({data['vsz_kb']/1024:.1f} MB)\n"
            analysis += f"- 物理内存: {data['rss_kb']:,} KB ({data['rss_kb']/1024:.1f} MB)\n"
            analysis += f"- 测试时长: {data['test_duration']:.0f} 秒\n"
            analysis += f"- 数据样本: {data['data_points']} 个\n\n"
            
            analysis += f"**性能指标**\n\n"
            analysis += f"| 指标 | 平均值 | 最大值 | 最小值 | 标准差 |\n"
            analysis += f"|------|--------|--------|--------|--------|\n"
            analysis += f"| CPU使用率 (%) | {data['cpu']['avg']} | {data['cpu']['max']} | {data['cpu']['min']} | {data['cpu']['std']} |\n"
            analysis += f"| 内存使用率 (%) | {data['memory_percent']['avg']} | {data['memory_percent']['max']} | {data['memory_percent']['min']} | {data['memory_percent']['std']} |\n"
            analysis += f"| 内存使用量 (MB) | {data['memory_mb']['avg']} | {data['memory_mb']['max']} | {data['memory_mb']['min']} | {data['memory_mb']['std']} |\n"
            
            # Add optional metrics if they exist
            if 'disk_io' in data:
                analysis += f"| 磁盘读取 (字节) | {data['disk_io']['read_bytes']['avg']:.0f} | {data['disk_io']['read_bytes']['max']:.0f} | {data['disk_io']['read_bytes']['min']:.0f} | {data['disk_io']['read_bytes']['std']:.0f} |\n"
                analysis += f"| 磁盘写入 (字节) | {data['disk_io']['write_bytes']['avg']:.0f} | {data['disk_io']['write_bytes']['max']:.0f} | {data['disk_io']['write_bytes']['min']:.0f} | {data['disk_io']['write_bytes']['std']:.0f} |\n"
            
            if 'network_io' in data:
                analysis += f"| 网络接收 (字节) | {data['network_io']['rx_bytes']['avg']:.0f} | {data['network_io']['rx_bytes']['max']:.0f} | {data['network_io']['rx_bytes']['min']:.0f} | {data['network_io']['rx_bytes']['std']:.0f} |\n"
                analysis += f"| 网络发送 (字节) | {data['network_io']['tx_bytes']['avg']:.0f} | {data['network_io']['tx_bytes']['max']:.0f} | {data['network_io']['tx_bytes']['min']:.0f} | {data['network_io']['tx_bytes']['std']:.0f} |\n"
            
            if 'context_switches' in data:
                analysis += f"| 自愿上下文切换 | {data['context_switches']['voluntary']['avg']:.0f} | {data['context_switches']['voluntary']['max']:.0f} | {data['context_switches']['voluntary']['min']:.0f} | {data['context_switches']['voluntary']['std']:.0f} |\n"
                analysis += f"| 非自愿上下文切换 | {data['context_switches']['involuntary']['avg']:.0f} | {data['context_switches']['involuntary']['max']:.0f} | {data['context_switches']['involuntary']['min']:.0f} | {data['context_switches']['involuntary']['std']:.0f} |\n"
            
            if 'thread_count' in data:
                analysis += f"| 线程数 | {data['thread_count']['avg']:.0f} | {data['thread_count']['max']:.0f} | {data['thread_count']['min']:.0f} | {data['thread_count']['std']:.0f} |\n"
            
            analysis += "\n"
            
            # Performance evaluation
            analysis += f"**性能评估**\n\n"
            
            # CPU evaluation
            if data['cpu']['avg'] < 1.0:
                analysis += f"- ✅ **CPU性能优秀**: 平均CPU使用率 {data['cpu']['avg']}%，对系统性能影响极小\n"
            elif data['cpu']['avg'] < 5.0:
                analysis += f"- ✅ **CPU性能良好**: 平均CPU使用率 {data['cpu']['avg']}%，CPU占用适中\n"
            else:
                analysis += f"- ⚠️ **CPU性能需关注**: 平均CPU使用率 {data['cpu']['avg']}%，CPU占用较高\n"
            
            # Memory evaluation
            if data['memory_mb']['avg'] < 50:
                analysis += f"- ✅ **内存使用合理**: 平均内存使用量 {data['memory_mb']['avg']} MB，内存占用适中\n"
            elif data['memory_mb']['avg'] < 200:
                analysis += f"- ✅ **内存使用可接受**: 平均内存使用量 {data['memory_mb']['avg']} MB，内存占用较高但可接受\n"
            else:
                analysis += f"- ⚠️ **内存使用需关注**: 平均内存使用量 {data['memory_mb']['avg']} MB，内存占用较高\n"
            
            # Stability evaluation
            if data['cpu']['std'] == 0 and data['memory_mb']['std'] == 0:
                analysis += f"- ✅ **运行稳定**: 所有指标在测试期间保持完全稳定，无波动\n"
            elif data['cpu']['std'] < 0.1 and data['memory_mb']['std'] < 1.0:
                analysis += f"- ✅ **运行稳定**: 指标波动很小，运行稳定\n"
            else:
                analysis += f"- ⚠️ **运行波动**: 指标存在一定波动，需要关注\n"
            
            analysis += "\n"
        
        return analysis
    
    def get_test_target_description(self):
        """Get test target description from command parameters"""
        targets = self.command_params.get('targets', [])
        if not targets:
            # Fallback to process names from data
            targets = list(self.report_data.keys()) if self.report_data else ['未知进程']
        
        if len(targets) == 1:
            return f"{targets[0]} 进程"
        elif len(targets) <= 3:
            return f"{', '.join(targets)} 进程"
        else:
            return f"{', '.join(targets[:3])} 等 {len(targets)} 个进程"
    
    def get_sampling_interval(self):
        """Get sampling interval from command parameters"""
        return self.command_params.get('interval', 2)
    
    def get_monitoring_duration(self):
        """Get monitoring duration from command parameters"""
        return self.command_params.get('duration', '未指定')
    
    def get_test_tool_version(self):
        """Get test tool version information"""
        version = self.command_params.get('version', 'v1.0')
        return f"进程监控系统 monitor {version}"
    
    def generate_conclusions(self):
        """Generate conclusions and recommendations"""
        if not self.report_data:
            return ""
        
        conclusions = "## 测试结论与建议\n\n"
        
        # Key findings
        conclusions += "### 关键发现\n\n"
        
        for process_name, data in self.report_data.items():
            conclusions += f"#### {process_name}\n\n"
            
            if data['cpu']['avg'] < 1.0:
                conclusions += f"- ✅ **CPU效率优秀**: {data['cpu']['avg']}%的CPU使用率表明对系统性能影响极小\n"
            else:
                conclusions += f"- ⚠️ **CPU使用需关注**: {data['cpu']['avg']}%的CPU使用率需要关注\n"
            
            if data['memory_mb']['avg'] < 50:
                conclusions += f"- ✅ **内存使用合理**: {data['memory_mb']['avg']} MB的内存使用量在可接受范围内\n"
            else:
                conclusions += f"- ⚠️ **内存使用需关注**: {data['memory_mb']['avg']} MB的内存使用量需要关注\n"
            
            if data['cpu']['std'] == 0 and data['memory_mb']['std'] == 0:
                conclusions += f"- ✅ **运行稳定**: 测试期间所有指标保持完全稳定\n"
            else:
                conclusions += f"- ⚠️ **存在波动**: 测试期间指标存在一定波动\n"
            
            conclusions += "\n"
        
        return conclusions
    
    def generate_report(self, output_file=None):
        """Generate complete report"""
        if not self.load_data():
            return False
        
        if not self.analyze_data():
            return False
        
        # Get first process data for report metadata
        first_process = list(self.report_data.keys())[0] if self.report_data else None
        if not first_process:
            print("✗ No process data available for report generation")
            return False
        
        first_data = self.report_data[first_process]
        
        # Generate report content
        test_target = self.get_test_target_description()
        sampling_interval = self.get_sampling_interval()
        monitoring_duration = self.get_monitoring_duration()
        test_tool = self.get_test_tool_version()
        
        report = f"""# 性能测试报告

## 报告概述

**测试日期**: {datetime.now().strftime('%Y年%m月%d日')}  
**测试时间**: {first_data['start_time'].strftime('%H:%M:%S')} - {first_data['end_time'].strftime('%H:%M:%S')}  
**测试工具**: {test_tool}  
**操作系统**: {self.system_info['platform']}
**系统架构**: {self.system_info['machine']}

## 测试目标

本次性能测试旨在评估 {test_target} 在正常运行状态下的资源使用情况，包括：

- CPU使用率分析
- 内存使用情况评估

## 测试环境

### 测试配置

- **监控进程**: {', '.join(self.report_data.keys())}
- **监控时长**: {first_data['test_duration']:.0f}秒
- **采样间隔**: {sampling_interval}秒
- **数据样本**: {first_data['data_points']}个/进程

## 测试结果

{self.generate_summary_table()}
{self.generate_detailed_analysis()}
{self.generate_conclusions()}
## 附录

### 测试数据文件

- **原始数据**: `{os.path.basename(self.data_file) if self.data_file else 'N/A'}`
- **可视化图表**: `performance_chart.png`
- **监控日志**: `logs/process_monitor.log`

---

**报告生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**报告版本**: v1.0  
**测试工程师**: AI Assistant  
**审核状态**: 待审核
"""
        
        # Save report
        if not output_file:
            if self.report_dir:
                output_file = os.path.join(self.report_dir, "performance_report.md")
            else:
                output_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✓ 性能测试报告已生成: {output_file}")
            return True
        except Exception as e:
            print(f"✗ 保存报告失败: {e}")
            return False


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProcessMonitor:
    def __init__(self, targets=None, monitor_config=None):
        """
        Initialize process monitor
        
        Args:
            targets: List of monitoring targets, can be process names or PIDs
                    Format: ['process_name1', '1234', 'process_name2', '5678']
            monitor_config: Dictionary defining which metrics to monitor
        """
        self.targets = targets or []
        self.monitoring = False
        self.monitor_thread = None
        self.data = defaultdict(list)  # Store data grouped by target identifier
        self.data_lock = threading.Lock()
        self.report_dir = None  # Report directory for this monitoring session
        
        # Default monitoring configuration
        self.default_config = {
            'cpu_percent': True,
            'memory_percent': True,
            'memory_mb': True,
            'file_descriptors': False,
            'thread_count': False
        }
        
        # Merge with user configuration
        self.monitor_config = self.default_config.copy()
        if monitor_config:
            self.monitor_config.update(monitor_config)
    
    def create_report_directory(self):
        """Create a unique report directory with sequence number and timestamp"""
        try:
            # Ensure report directory exists
            os.makedirs('report', exist_ok=True)
            
            # Get next sequence number
            existing_dirs = glob.glob('report/[0-9][0-9][0-9]_*')
            if existing_dirs:
                # Extract sequence numbers and find the highest
                seq_numbers = []
                for dir_path in existing_dirs:
                    try:
                        seq_num = int(os.path.basename(dir_path).split('_')[0])
                        seq_numbers.append(seq_num)
                    except (ValueError, IndexError):
                        continue
                next_seq = max(seq_numbers) + 1 if seq_numbers else 1
            else:
                next_seq = 1
            
            # Create directory with sequence number and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dir_name = f"{next_seq:03d}_{timestamp}"
            self.report_dir = os.path.join('report', dir_name)
            os.makedirs(self.report_dir, exist_ok=True)
            
            logger.info(f"Created report directory: {self.report_dir}")
            return self.report_dir
            
        except Exception as e:
            logger.error(f"Failed to create report directory: {e}")
            # Fallback to timestamp-only directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.report_dir = os.path.join('report', f"monitor_{timestamp}")
            os.makedirs(self.report_dir, exist_ok=True)
            return self.report_dir
        
    
    def is_pid(self, target):
        """Check if target is a PID"""
        try:
            int(target)
            return True
        except ValueError:
            return False
    
    def find_process_by_name(self, process_name):
        """Find process PID by process name, matching only executable files"""
        try:
            # First try to find exact executable name match
            result = subprocess.run(['pgrep', '-x', process_name], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                valid_pids = []
                for pid in pids:
                    if pid.isdigit():
                        # Verify this PID actually matches the executable
                        if self.verify_process_executable(int(pid), process_name):
                            valid_pids.append(int(pid))
                return valid_pids
            
            # If no exact match, try to find processes where the command starts with the process name
            result = subprocess.run(['pgrep', '-f', f'^{process_name}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                valid_pids = []
                for pid in pids:
                    if pid.isdigit():
                        # Verify this PID actually matches the executable
                        if self.verify_process_executable(int(pid), process_name):
                            valid_pids.append(int(pid))
                return valid_pids
            
            return []
        except subprocess.TimeoutExpired:
            logger.warning(f"pgrep command timeout (process: {process_name})")
            return []
        except Exception as e:
            logger.error(f"Failed to find process PID (process: {process_name}): {e}")
            return []
    
    def verify_process_executable(self, pid, process_name):
        """Verify that the process with given PID actually has the expected executable name"""
        try:
            # Get process command line
            cmd = ['ps', '-p', str(pid), '-o', 'comm=']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0 and result.stdout.strip():
                comm = result.stdout.strip()
                # Check if the command name matches (case-insensitive)
                if comm.lower() == process_name.lower():
                    return True
                
                # Also check if it's a full path that ends with the process name
                if comm.endswith('/' + process_name) or comm.endswith('\\' + process_name):
                    return True
            
            return False
        except Exception as e:
            logger.debug(f"Failed to verify process executable for PID {pid}: {e}")
            return False
    
    def get_process_info(self, pid):
        """Get detailed process information"""
        try:
            cmd = ['ps', '-p', str(pid), '-o', 'pid,ppid,pcpu,pmem,rss,vsz,etime,comm,args']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:  # 跳过标题行
                    parts = lines[1].split()
                    if len(parts) >= 8:
                        # 获取完整的命令行参数
                        full_args = ' '.join(parts[8:]) if len(parts) > 8 else parts[7]
                        
                        process_info = {
                            'pid': int(parts[0]),
                            'ppid': int(parts[1]),
                            'cpu_percent': float(parts[2]),
                            'memory_percent': float(parts[3]),
                            'rss_kb': int(parts[4]),
                            'vsz_kb': int(parts[5]),
                            'etime': parts[6],
                            'comm': parts[7],
                            'args': full_args
                        }
                        
                        # 在日志中输出完整的进程命令
                        logger.info(f"监控进程 PID {pid}: {full_args}")
                        
                        return process_info
            else:
                # 进程不存在，返回None
                logger.warning(f"进程 PID {pid} 不存在或已结束")
                return None
        except subprocess.TimeoutExpired:
            logger.warning(f"ps command timeout (PID: {pid})")
            return None
        except Exception as e:
            logger.error(f"Failed to get process info (PID: {pid}): {e}")
            return None
    
    
    
    
    def get_file_descriptors_info(self, pid):
        """Get file descriptors count for a process"""
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Use lsof to count file descriptors
                cmd = ['lsof', '-p', str(pid)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Count lines (excluding header)
                    lines = result.stdout.strip().split('\n')
                    fd_count = max(0, len(lines) - 1)  # Subtract header line
                    return {'fd_count': fd_count}
                return {'fd_count': 0}
            else:  # Linux
                # Count files in /proc/pid/fd directory
                try:
                    fd_dir = f'/proc/{pid}/fd'
                    if os.path.exists(fd_dir):
                        fd_count = len(os.listdir(fd_dir))
                        return {'fd_count': fd_count}
                    return {'fd_count': 0}
                except (OSError, PermissionError):
                    return {'fd_count': 0}
        except Exception as e:
            logger.debug(f"Failed to get file descriptors info for PID {pid}: {e}")
            return {'fd_count': 0}
    
    def get_thread_count_info(self, pid):
        """Get thread count information for a process"""
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Use ps to get thread count
                cmd = ['ps', '-p', str(pid), '-o', 'pid,nlwp']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        parts = lines[1].split()
                        if len(parts) >= 2:
                            return {'thread_count': int(parts[1]) if parts[1].isdigit() else 0}
                return {'thread_count': 0}
            else:  # Linux
                # Read from /proc/pid/status
                try:
                    with open(f'/proc/{pid}/status', 'r') as f:
                        for line in f:
                            if line.startswith('Threads:'):
                                return {'thread_count': int(line.split(':')[1].strip())}
                    return {'thread_count': 0}
                except FileNotFoundError:
                    return {'thread_count': 0}
        except Exception as e:
            logger.debug(f"Failed to get thread count info for PID {pid}: {e}")
            return {'thread_count': 0}
    
    def get_system_info(self):
        """Get system overall information"""
        try:
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # 使用top命令获取系统负载
                result = subprocess.run(['top', '-l', '1', '-n', '0'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    load_avg = 0.0
                    for line in lines:
                        if 'load averages:' in line:
                            parts = line.split('load averages:')[1].strip().split()
                            if parts:
                                load_avg = float(parts[0])
                            break
                
                # 使用vm_stat获取内存信息
                result = subprocess.run(['vm_stat'], capture_output=True, text=True, timeout=5)
                mem_total_kb = 0
                mem_free_kb = 0
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Pages free:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                mem_free_kb = int(parts[1].strip().rstrip('.')) * 4  # 4KB per page
                        elif 'Pages active:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                mem_total_kb += int(parts[1].strip().rstrip('.')) * 4
                        elif 'Pages inactive:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                mem_total_kb += int(parts[1].strip().rstrip('.')) * 4
                        elif 'Pages speculative:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                mem_total_kb += int(parts[1].strip().rstrip('.')) * 4
                        elif 'Pages wired down:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                mem_total_kb += int(parts[1].strip().rstrip('.')) * 4
                
                return {
                    'load_1min': load_avg,
                    'load_5min': load_avg,
                    'load_15min': load_avg,
                    'mem_total_kb': mem_total_kb,
                    'mem_available_kb': mem_free_kb,
                    'mem_free_kb': mem_free_kb
                }
            else:  # Linux
                # 获取系统负载
                with open('/proc/loadavg', 'r') as f:
                    loadavg = f.read().strip().split()
                
                # 获取内存信息
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            meminfo[key.strip()] = value.strip()
                
                return {
                    'load_1min': float(loadavg[0]),
                    'load_5min': float(loadavg[1]),
                    'load_15min': float(loadavg[2]),
                    'mem_total_kb': int(meminfo.get('MemTotal', '0').split()[0]),
                    'mem_available_kb': int(meminfo.get('MemAvailable', '0').split()[0]),
                    'mem_free_kb': int(meminfo.get('MemFree', '0').split()[0])
                }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return None
    
    def collect_data_for_target(self, target):
        """Collect resource usage data for specified target"""
        try:
            if self.is_pid(target):
                # Use PID directly
                pid = int(target)
                process_info = self.get_process_info(pid)
                if not process_info:
                    # 进程不存在，返回零值数据
                    logger.info(f"进程 PID {pid} 不存在，记录零值数据")
                    return self.create_zero_data(target, f"PID_{pid}", pid)
                target_name = f"PID_{pid}"
            else:
                # Find by process name
                pids = self.find_process_by_name(target)
                if not pids:
                    # 进程不存在，返回零值数据
                    logger.info(f"进程 {target} 不存在，记录零值数据")
                    return self.create_zero_data(target, target, None)
                
                # Get first found process info
                pid = pids[0]
                process_info = self.get_process_info(pid)
                if not process_info:
                    # 进程不存在，返回零值数据
                    logger.info(f"进程 {target} (PID {pid}) 不存在，记录零值数据")
                    return self.create_zero_data(target, target, pid)
                target_name = target
            
            # Get system information
            system_info = self.get_system_info()
            
            # Calculate memory usage (MB)
            memory_mb = process_info.get('rss_kb', 0) / 1024.0
            
            # Initialize data with basic information
            data = {
                'timestamp': datetime.now(),
                'target': target,
                'target_name': target_name,
                'pid': pid,
                'command': process_info.get('comm', ''),
                'args': process_info.get('args', ''),
                'system_load': system_info.get('load_1min', 0.0) if system_info else 0.0,
                'system_mem_available_mb': (system_info.get('mem_available_kb', 0) / 1024.0) if system_info else 0.0
            }
            
            # Add basic metrics (always collected)
            data.update({
                'cpu_percent': process_info.get('cpu_percent', 0.0),
                'memory_percent': process_info.get('memory_percent', 0.0),
                'memory_mb': memory_mb,
                'rss_kb': process_info.get('rss_kb', 0),
                'vsz_kb': process_info.get('vsz_kb', 0)
            })
            
            # Add optional metrics based on configuration
            if self.monitor_config.get('file_descriptors', False):
                fd_info = self.get_file_descriptors_info(pid)
                data.update({
                    'fd_count': fd_info.get('fd_count', 0)
                })
            
            if self.monitor_config.get('thread_count', False):
                thread_info = self.get_thread_count_info(pid)
                data.update({
                    'thread_count': thread_info.get('thread_count', 0)
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to collect data for target {target}: {e}")
            return None
    
    def create_zero_data(self, target, target_name, pid):
        """Create zero-value data for non-existent processes"""
        system_info = self.get_system_info()
        
        # Initialize with basic data
        data = {
            'timestamp': datetime.now(),
            'target': target,
            'target_name': target_name,
            'pid': pid if pid is not None else 0,
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_mb': 0.0,
            'rss_kb': 0,
            'vsz_kb': 0,
            'command': '',
            'args': '',
            'system_load': system_info.get('load_1min', 0.0) if system_info else 0.0,
            'system_mem_available_mb': (system_info.get('mem_available_kb', 0) / 1024.0) if system_info else 0.0
        }
        
        # Add zero values for optional metrics based on configuration
        if self.monitor_config.get('file_descriptors', False):
            data.update({
                'fd_count': 0
            })
        
        if self.monitor_config.get('thread_count', False):
            data.update({
                'thread_count': 0
            })
        
        return data
    
    def collect_all_data(self):
        """Collect data for all targets"""
        all_data = {}
        for target in self.targets:
            data = self.collect_data_for_target(target)
            if data:
                all_data[target] = data
            else:
                # 即使进程不存在，也创建零值数据
                logger.warning(f"Target not found: {target}, creating zero data")
                all_data[target] = self.create_zero_data(target, target, None)
        return all_data
    
    def start_monitoring(self, interval=5, duration=None):
        """Start monitoring"""
        if self.monitoring:
            logger.warning("Monitoring is already running")
            return
        
        # Create report directory for this monitoring session
        self.create_report_directory()
        
        # Store monitoring parameters for report generation
        self.sampling_interval = interval
        self.monitoring_duration = duration
        
        self.monitoring = True
        self.data = defaultdict(list)
        
        def monitor_loop():
            start_time = time.time()
            sample_count = 0
            
            # Print beautiful header
            print_header("🚀 进程监控系统启动", 120)
            print_info(f"监控目标: {', '.join(self.targets)}")
            print_info(f"采样间隔: {interval} 秒")
            if duration:
                print_info(f"监控时长: {duration} 秒")
            else:
                print_info("监控时长: 持续监控 (按 Ctrl+C 停止)")
            print_separator(120)
            
            # Print beautiful table header for separate process display
            header = f"{Colors.BOLD}{Colors.CYAN}{'时间':<20}{Colors.RESET} {Colors.BOLD}{Colors.MAGENTA}{'进程名':<15}{Colors.RESET} {Colors.BOLD}{Colors.YELLOW}{'PID':<8}{Colors.RESET}"
            if self.monitor_config.get('cpu_percent', True):
                header += f" {Colors.BOLD}{Colors.RED}{'CPU%':<8}{Colors.RESET}"
            if self.monitor_config.get('memory_percent', True):
                header += f" {Colors.BOLD}{Colors.GREEN}{'内存%':<8}{Colors.RESET}"
            if self.monitor_config.get('memory_mb', True):
                header += f" {Colors.BOLD}{Colors.BLUE}{'内存MB':<8}{Colors.RESET}"
            if self.monitor_config.get('file_descriptors', False):
                header += f" {Colors.BOLD}{Colors.BRIGHT_YELLOW}{'文件描述符':<8}{Colors.RESET}"
            if self.monitor_config.get('thread_count', False):
                header += f" {Colors.BOLD}{Colors.BRIGHT_GREEN}{'线程数':<8}{Colors.RESET}"
            print(header)
            print_separator(120, "─")  # Use Unicode box drawing character
            
            while self.monitoring:
                try:
                    all_data = self.collect_all_data()
                    if all_data:
                        with self.data_lock:
                            for target, data in all_data.items():
                                self.data[target].append(data)
                        
                        # 实时显示数据 - 每个进程单独一行
                        timestamp_str = datetime.now().strftime('%H:%M:%S')
                        
                        for target in self.targets:
                            line = f"{Colors.BOLD}{Colors.CYAN}{timestamp_str:<20}{Colors.RESET}"
                            
                            if target in all_data:
                                data = all_data[target]
                                # 如果进程不存在，显示0值而不是N/A
                                if data['pid'] == 0 or data['cpu_percent'] == 0.0:
                                    line += f" {Colors.DIM}{target:<15}{Colors.RESET} {Colors.DIM}{'0':<8}{Colors.RESET}"
                                else:
                                    line += f" {Colors.MAGENTA}{target:<15}{Colors.RESET} {Colors.YELLOW}{data['pid']:<8}{Colors.RESET}"
                                
                                # Add metrics based on configuration with colors
                                if self.monitor_config.get('cpu_percent', True):
                                    cpu_val = data['cpu_percent']
                                    cpu_color = Colors.RED if cpu_val > 50 else Colors.BRIGHT_RED if cpu_val > 20 else Colors.GREEN
                                    line += f" {cpu_color}{cpu_val:<8.2f}{Colors.RESET}"
                                if self.monitor_config.get('memory_percent', True):
                                    mem_val = data['memory_percent']
                                    mem_color = Colors.GREEN if mem_val > 50 else Colors.BRIGHT_GREEN if mem_val > 20 else Colors.GREEN
                                    line += f" {mem_color}{mem_val:<8.2f}{Colors.RESET}"
                                if self.monitor_config.get('memory_mb', True):
                                    mem_mb_val = data['memory_mb']
                                    mem_mb_color = Colors.BLUE if mem_mb_val > 100 else Colors.BRIGHT_BLUE if mem_mb_val > 50 else Colors.BLUE
                                    line += f" {mem_mb_color}{mem_mb_val:<8.2f}{Colors.RESET}"
                                if self.monitor_config.get('file_descriptors', False):
                                    fd_count = data.get('fd_count', 0)
                                    line += f" {Colors.BRIGHT_YELLOW}{fd_count:<8}{Colors.RESET}"
                                if self.monitor_config.get('thread_count', False):
                                    threads = data.get('thread_count', 0)
                                    line += f" {Colors.BRIGHT_GREEN}{threads:<8}{Colors.RESET}"
                            else:
                                line += f" {Colors.DIM}{target:<15}{Colors.RESET} {Colors.DIM}{'0':<8}{Colors.RESET}"
                                # Add zero values for all enabled metrics
                                if self.monitor_config.get('cpu_percent', True):
                                    line += f" {Colors.DIM}{'0.00':<8}{Colors.RESET}"
                                if self.monitor_config.get('memory_percent', True):
                                    line += f" {Colors.DIM}{'0.00':<8}{Colors.RESET}"
                                if self.monitor_config.get('memory_mb', True):
                                    line += f" {Colors.DIM}{'0.00':<8}{Colors.RESET}"
                                if self.monitor_config.get('file_descriptors', False):
                                    line += f" {Colors.DIM}{'0':<8}{Colors.RESET}"
                                if self.monitor_config.get('thread_count', False):
                                    line += f" {Colors.DIM}{'0':<8}{Colors.RESET}"
                            
                            print(line)
                        sample_count += 1
                    else:
                        # 没有数据时，每个进程也单独显示一行
                        timestamp_str = datetime.now().strftime('%H:%M:%S')
                        for target in self.targets:
                            line = f"{Colors.BOLD}{Colors.CYAN}{timestamp_str:<20}{Colors.RESET}"
                            line += f" {Colors.DIM}{target:<15}{Colors.RESET} {Colors.DIM}{'0':<8}{Colors.RESET}"
                            # Add zero values for all enabled metrics
                            if self.monitor_config.get('cpu_percent', True):
                                line += f" {Colors.DIM}{'0.00':<8}{Colors.RESET}"
                            if self.monitor_config.get('memory_percent', True):
                                line += f" {Colors.DIM}{'0.00':<8}{Colors.RESET}"
                            if self.monitor_config.get('memory_mb', True):
                                line += f" {Colors.DIM}{'0.00':<8}{Colors.RESET}"
                            if self.monitor_config.get('file_descriptors', False):
                                line += f" {Colors.DIM}{'0':<8}{Colors.RESET}"
                            if self.monitor_config.get('thread_count', False):
                                line += f" {Colors.DIM}{'0':<8}{Colors.RESET}"
                            print(line)
                    
                    # Check if monitoring duration reached
                    if duration and (time.time() - start_time) >= duration:
                        logger.info(f"Monitoring duration {duration} seconds reached, stopping monitoring")
                        self.monitoring = False
                        break
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(interval)
            
            print_separator(120, "─")
            print_success(f"监控完成！共收集 {sample_count} 个数据样本")
            print_header("📊 监控统计信息", 120)
            
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Started monitoring targets, sampling interval: {interval} seconds")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Monitoring stopped")
    
    def get_data(self):
        """Get collected data"""
        with self.data_lock:
            return dict(self.data)
    
    def save_data_to_file(self, filename=None):
        """Save data to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.report_dir:
                filename = os.path.join(self.report_dir, f"monitor_data_{timestamp}.json")
            else:
                filename = f"process_monitor_data_{timestamp}.json"
        
        try:
            with self.data_lock:
                data_to_save = {}
                for target, target_data in self.data.items():
                    data_to_save[target] = []
                    for item in target_data:
                        # Create base data structure
                        save_item = {
                            'timestamp': item['timestamp'].isoformat(),
                            'target': item['target'],
                            'target_name': item['target_name'],
                            'pid': item['pid'],
                            'cpu_percent': item['cpu_percent'],
                            'memory_percent': item['memory_percent'],
                            'memory_mb': item['memory_mb'],
                            'rss_kb': item['rss_kb'],
                            'vsz_kb': item['vsz_kb'],
                            'command': item['command'],
                            'args': item['args'],
                            'system_load': item['system_load'],
                            'system_mem_available_mb': item['system_mem_available_mb']
                        }
                        
                        # Add optional metrics if they exist
                        if 'fd_count' in item:
                            save_item['fd_count'] = item['fd_count']
                        
                        if 'thread_count' in item:
                            save_item['thread_count'] = item['thread_count']
                        
                        data_to_save[target].append(save_item)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Data saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return None
    
    def load_data_from_file(self, filename):
        """Load data from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with self.data_lock:
                self.data = defaultdict(list)
                for target, target_data in data.items():
                    for item in target_data:
                        # Create base data structure
                        load_item = {
                            'timestamp': datetime.fromisoformat(item['timestamp']),
                            'target': item['target'],
                            'target_name': item['target_name'],
                            'pid': item['pid'],
                            'cpu_percent': item['cpu_percent'],
                            'memory_percent': item['memory_percent'],
                            'memory_mb': item['memory_mb'],
                            'rss_kb': item['rss_kb'],
                            'vsz_kb': item['vsz_kb'],
                            'command': item['command'],
                            'args': item['args'],
                            'system_load': item['system_load'],
                            'system_mem_available_mb': item['system_mem_available_mb']
                        }
                        
                        # Add optional metrics if they exist in the loaded data
                        if 'fd_count' in item:
                            load_item['fd_count'] = item['fd_count']
                        
                        if 'thread_count' in item:
                            load_item['thread_count'] = item['thread_count']
                        
                        self.data[target].append(load_item)
            
            logger.info(f"Loaded {sum(len(target_data) for target_data in self.data.values())} data points from file: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def generate_visualization(self, output_file=None, show_plot=True, show_all_ticks=True, max_ticks=20):
        """Generate visualization charts"""
        try:
            # Check if matplotlib is available
            try:
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                import matplotlib.font_manager as fm
            except ImportError:
                logger.error("matplotlib not installed, cannot generate visualization charts")
                logger.info("Please run: pip3 install matplotlib")
                return None
            
            data = self.get_data()
            if not data:
                logger.warning("No data available for visualization")
                return
            
            # Set font to support Chinese characters and emoji
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Use system fonts that support Chinese and emoji
                plt.rcParams['font.sans-serif'] = ['Apple Color Emoji', 'PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'SimHei', 'DejaVu Sans', 'Arial', 'sans-serif']
            elif system == "Windows":
                # Windows Chinese fonts
                plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans', 'Arial', 'sans-serif']
            else:  # Linux
                # Linux Chinese fonts
                plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'DejaVu Sans', 'Arial', 'sans-serif']
            
            plt.rcParams['axes.unicode_minus'] = False
            logger.info(f"Using fonts for {system} system with Chinese and emoji support")
            
            # Calculate chart layout based on enabled metrics
            num_targets = len(data)
            if num_targets == 0:
                logger.warning("No target data available for display")
                return
            
            # Count enabled metrics
            enabled_metrics = []
            if self.monitor_config.get('cpu_percent', True):
                enabled_metrics.append('cpu_percent')
            if self.monitor_config.get('memory_percent', True):
                enabled_metrics.append('memory_percent')
            if self.monitor_config.get('memory_mb', True):
                enabled_metrics.append('memory_mb')
            if self.monitor_config.get('file_descriptors', False):
                enabled_metrics.append('fd_count')
            if self.monitor_config.get('thread_count', False):
                enabled_metrics.append('thread_count')
            
            num_charts = len(enabled_metrics)
            if num_charts == 0:
                logger.warning("No metrics enabled for visualization")
                return
            
            # Create subplots: one row per metric, one column per target
            # Increase figure size and add more spacing between charts
            fig, axes = plt.subplots(num_charts, num_targets, figsize=(6 * num_targets, 4 * num_charts))
            
            # If only one target, ensure axes is 2D array
            if num_targets == 1:
                axes = axes.reshape(-1, 1)
            elif num_charts == 1:
                axes = axes.reshape(1, -1)
            
            # Set main title with better styling
            fig.suptitle('Process Resource Monitoring Report', fontsize=18, fontweight='bold', y=0.94)
            
            # Create charts for each metric and target
            for metric_idx, metric in enumerate(enabled_metrics):
                for target_idx, (target, target_data) in enumerate(data.items()):
                    if not target_data:
                        continue
                    
                    # Parse data
                    timestamps = [item['timestamp'] for item in target_data]
                    
                    # Set time axis display
                    if show_all_ticks and len(timestamps) <= max_ticks:
                        selected_timestamps = timestamps
                    else:
                        if len(timestamps) <= max_ticks:
                            step = 1
                        else:
                            step = max(1, len(timestamps) // max_ticks)
                        selected_timestamps = timestamps[::step]
                    
                    # Get data for this metric
                    if metric == 'cpu_percent':
                        metric_data = [item['cpu_percent'] for item in target_data]
                        ylabel = 'CPU Usage (%)'
                        title = f'{target}\nCPU Usage'
                        color = 'b'
                        marker = 'o'
                    elif metric == 'memory_percent':
                        metric_data = [item['memory_percent'] for item in target_data]
                        ylabel = 'Memory Usage (%)'
                        title = f'{target}\nMemory Usage %'
                        color = 'r'
                        marker = 's'
                    elif metric == 'memory_mb':
                        metric_data = [item['memory_mb'] for item in target_data]
                        ylabel = 'Memory Usage (MB)'
                        title = f'{target}\nMemory Usage'
                        color = 'g'
                        marker = '^'
                    elif metric == 'fd_count':
                        metric_data = [item.get('fd_count', 0) for item in target_data]
                        ylabel = 'File Descriptors'
                        title = f'{target}\nFile Descriptors'
                        color = 'orange'
                        marker = 'D'
                    elif metric == 'thread_count':
                        metric_data = [item.get('thread_count', 0) for item in target_data]
                        ylabel = 'Thread Count'
                        title = f'{target}\nThread Count'
                        color = 'gray'
                        marker = 'h'
                    else:
                        continue
                    
                    # Create the chart with improved styling
                    ax = axes[metric_idx, target_idx] if num_charts > 1 else axes[target_idx]
                    ax.plot(timestamps, metric_data, color=color, linewidth=2.5, marker=marker, 
                           markersize=4, markerfacecolor='white', markeredgecolor=color, 
                           markeredgewidth=1.5)
                    ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
                    ax.set_title(title, fontsize=13, fontweight='bold', pad=8)
                    ax.grid(True, linestyle='--', linewidth=0.8)
                    
                    # Add subtle background color
                    ax.set_facecolor('#f8f9fa')
                    
                    # Set y-axis range
                    metric_max = max(metric_data) if metric_data else 0
                    if metric_max > 0:
                        ax.set_ylim(0, metric_max * 1.1)
                    else:
                        ax.set_ylim(0, 10)  # When all data is 0, set a small range
                    
                    # Set time axis with improved styling
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                    ax.set_xticks(selected_timestamps)
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9, fontweight='bold')
                    ax.xaxis.set_minor_locator(mdates.SecondLocator(interval=1))
                    ax.tick_params(axis='x', which='minor', length=3)
                    ax.tick_params(axis='y', labelsize=9, labelcolor='#333333')
                    
                    # Add x-axis label only to the bottom row
                    if metric_idx == num_charts - 1:
                        ax.set_xlabel('Time', fontsize=11, fontweight='bold', color='#333333')
            
            # Adjust layout with more spacing between charts
            plt.tight_layout()
            # Increase spacing between subplots with more white space around charts
            plt.subplots_adjust(
                bottom=0.15,  # More space at bottom for x-axis labels
                top=0.90,     # More space at top for title
                left=0.10,    # More space on left
                right=0.92,   # More space on right
                hspace=0.8,   # Reduced vertical spacing between charts
                wspace=0.3    # Increased horizontal spacing between charts
            )
            
            # Save or display chart
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                logger.info(f"Chart saved to: {output_file}")
            elif self.report_dir:
                # Auto-save to report directory if no specific output file
                chart_file = os.path.join(self.report_dir, "performance_chart.png")
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                logger.info(f"Chart saved to: {chart_file}")
            
            if show_plot:
                plt.show()
            
            # Generate statistics
            stats = {}
            for target, target_data in data.items():
                if target_data:
                    stats[target] = {
                        'data_points': len(target_data),
                        'pid': target_data[0]['pid'],
                        'command': target_data[0]['command']
                    }
                    
                    # Add statistics for enabled metrics
                    if self.monitor_config.get('cpu_percent', True):
                        cpu_data = [item['cpu_percent'] for item in target_data]
                        stats[target].update({
                            'avg_cpu_percent': round(sum(cpu_data) / len(cpu_data), 2),
                            'max_cpu_percent': round(max(cpu_data), 2)
                        })
                    
                    if self.monitor_config.get('memory_mb', True):
                        memory_mb_data = [item['memory_mb'] for item in target_data]
                        stats[target].update({
                            'avg_memory_mb': round(sum(memory_mb_data) / len(memory_mb_data), 2),
                            'max_memory_mb': round(max(memory_mb_data), 2)
                        })
                    
                    if self.monitor_config.get('memory_percent', True):
                        memory_percent_data = [item['memory_percent'] for item in target_data]
                        stats[target].update({
                            'avg_memory_percent': round(sum(memory_percent_data) / len(memory_percent_data), 2),
                            'max_memory_percent': round(max(memory_percent_data), 2)
                        })
                    
                    if self.monitor_config.get('file_descriptors', False):
                        fd_data = [item.get('fd_count', 0) for item in target_data]
                        stats[target].update({
                            'avg_fd_count': round(sum(fd_data) / len(fd_data), 2),
                            'max_fd_count': round(max(fd_data), 2)
                        })
                    
                    if self.monitor_config.get('thread_count', False):
                        thread_data = [item.get('thread_count', 0) for item in target_data]
                        stats[target].update({
                            'avg_thread_count': round(sum(thread_data) / len(thread_data), 2),
                            'max_thread_count': round(max(thread_data), 2)
                        })
            
            logger.info(f"Process monitoring statistics:")
            for target, target_stats in stats.items():
                logger.info(f"  {target}:")
                for key, value in target_stats.items():
                    logger.info(f"    {key}: {value}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to generate visualization: {e}")
            return None
    
    def print_summary(self):
        """Print monitoring summary"""
        data = self.get_data()
        if not data:
            print_error("没有可用的数据进行分析")
            return
        
        print_header("📈 进程监控汇总报告", 100)
        
        for target, target_data in data.items():
            if not target_data:
                continue
            
            # 计算统计信息
            cpu_data = [item['cpu_percent'] for item in target_data]
            memory_mb_data = [item['memory_mb'] for item in target_data]
            memory_percent_data = [item['memory_percent'] for item in target_data]
            
            avg_cpu = sum(cpu_data) / len(cpu_data)
            max_cpu = max(cpu_data)
            avg_memory_mb = sum(memory_mb_data) / len(memory_mb_data)
            max_memory_mb = max(memory_mb_data)
            avg_memory_percent = sum(memory_percent_data) / len(memory_percent_data)
            max_memory_percent = max(memory_percent_data)
            
            duration = (target_data[-1]['timestamp'] - target_data[0]['timestamp']).total_seconds()
            
            print(f"\n{Colors.BOLD}{Colors.MAGENTA}🎯 监控目标: {target}{Colors.RESET}")
            print(f"  {Colors.YELLOW}📋 PID:{Colors.RESET} {target_data[0]['pid']}")
            print(f"  {Colors.BLUE}⚙️  命令:{Colors.RESET} {target_data[0]['command']}")
            print(f"  {Colors.CYAN}⏱️  监控时长:{Colors.RESET} {duration:.0f} 秒")
            print(f"  {Colors.GREEN}📊 数据样本:{Colors.RESET} {len(target_data)} 个")
            
            # CPU 使用率统计
            cpu_color = Colors.RED if avg_cpu > 50 else Colors.BRIGHT_RED if avg_cpu > 20 else Colors.GREEN
            print(f"  {Colors.RED}🖥️  CPU使用率:{Colors.RESET} {cpu_color}平均 {avg_cpu:.2f}%{Colors.RESET}, {Colors.RED}最大 {max_cpu:.2f}%{Colors.RESET}")
            
            # 内存使用统计
            mem_color = Colors.BLUE if avg_memory_mb > 100 else Colors.BRIGHT_BLUE if avg_memory_mb > 50 else Colors.BLUE
            print(f"  {Colors.BLUE}💾 内存使用量:{Colors.RESET} {mem_color}平均 {avg_memory_mb:.2f} MB{Colors.RESET}, {Colors.BLUE}最大 {max_memory_mb:.2f} MB{Colors.RESET}")
            
            # 内存使用百分比统计
            mem_pct_color = Colors.GREEN if avg_memory_percent > 50 else Colors.BRIGHT_GREEN if avg_memory_percent > 20 else Colors.GREEN
            print(f"  {Colors.GREEN}📈 内存使用率:{Colors.RESET} {mem_pct_color}平均 {avg_memory_percent:.2f}%{Colors.RESET}, {Colors.GREEN}最大 {max_memory_percent:.2f}%{Colors.RESET}")
        
        print_separator(100, "=")
    
    def generate_performance_report(self, data_file=None, command_params=None):
        """Generate performance test report"""
        try:
            if not data_file:
                # Find the most recent data file in report directory
                if self.report_dir:
                    data_files = glob.glob(os.path.join(self.report_dir, "monitor_data_*.json"))
                    if data_files:
                        data_file = max(data_files, key=os.path.getctime)
                    else:
                        logger.warning("No data files found in report directory")
                        return False
                else:
                    logger.warning("No report directory available")
                    return False
            
            if not os.path.exists(data_file):
                logger.error(f"Data file not found: {data_file}")
                return False
            
            # Prepare command parameters
            if not command_params:
                command_params = {
                    'targets': self.targets,
                    'interval': getattr(self, 'sampling_interval', 2),
                    'duration': getattr(self, 'monitoring_duration', None),
                    'version': 'v1.0'
                }
            
            # Generate performance report
            report_generator = PerformanceReportTemplate(data_file, self.report_dir, command_params)
            success = report_generator.generate_report()
            
            if success:
                logger.info("Performance test report generated successfully")
                return True
            else:
                logger.error("Failed to generate performance test report")
                return False
                
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return False

def signal_handler(signum, frame):
    """Signal handler"""
    logger.info("Received stop signal, shutting down monitoring...")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Universal Process Monitoring System')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring mode')
    parser.add_argument('--duration', type=int, help='Monitoring duration (seconds)')
    parser.add_argument('--interval', type=int, default=5, help='Monitoring sampling interval (seconds)')
    parser.add_argument('--visualize', action='store_true', help='Generate visualization charts')
    parser.add_argument('--load-data', type=str, help='Load data from JSON file')
    parser.add_argument('--save-data', type=str, help='Save data to JSON file')
    parser.add_argument('--output', type=str, help='Chart output file path')
    parser.add_argument('--targets', type=str, nargs='+', help='List of targets to monitor (process names or PIDs)')
    parser.add_argument('--no-show', action='store_true', help='Do not display charts, only save')
    parser.add_argument('--summary', action='store_true', help='Display monitoring summary')
    parser.add_argument('--show-all-ticks', action='store_true', help='Show all time points')
    parser.add_argument('--max-ticks', type=int, default=20, help='Maximum number of time points to display')
    parser.add_argument('--generate-report', action='store_true', help='Generate performance test report')
    
    # Report generation options
    parser.add_argument('--data-file', type=str, help='Monitoring data JSON file path for report generation')
    parser.add_argument('--report-dir', type=str, help='Report directory path')
    parser.add_argument('--report-output', type=str, help='Report output file path')
    parser.add_argument('--version', type=str, default='v1.0', help='Tool version')
    
    # Monitoring configuration options
    parser.add_argument('--enable-file-descriptors', action='store_true', help='Enable file descriptors monitoring')
    parser.add_argument('--enable-thread-count', action='store_true', help='Enable thread count monitoring')
    parser.add_argument('--disable-cpu', action='store_true', help='Disable CPU monitoring')
    parser.add_argument('--disable-memory', action='store_true', help='Disable memory monitoring')
    
    args = parser.parse_args()
    
    # Logs are now only output to console
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Use default targets if none specified
    if not args.targets:
        args.targets = ['monitor']
    
    # Build monitoring configuration
    monitor_config = {
        'cpu_percent': not args.disable_cpu,
        'memory_percent': not args.disable_memory,
        'memory_mb': not args.disable_memory,
        'file_descriptors': args.enable_file_descriptors,
        'thread_count': args.enable_thread_count
    }
    
    # Handle standalone report generation
    if args.data_file and not args.monitor and not args.load_data:
        if not os.path.exists(args.data_file):
            print(f"✗ Data file does not exist: {args.data_file}")
            return
        
        # Prepare command parameters for report generation
        command_params = {
            'targets': args.targets or [],
            'interval': args.interval,
            'duration': args.duration,
            'version': args.version
        }
        
        # Generate performance report
        report_generator = PerformanceReportTemplate(args.data_file, args.report_dir, command_params)
        success = report_generator.generate_report(args.report_output)
        
        if success:
            print("✓ Performance test report generated successfully")
        else:
            print("✗ Failed to generate performance test report")
        return
    
    monitor = ProcessMonitor(targets=args.targets, monitor_config=monitor_config)
    
    try:
        if args.load_data:
            if monitor.load_data_from_file(args.load_data):
                if args.summary:
                    monitor.print_summary()
                if args.visualize:
                    monitor.generate_visualization(
                        args.output, 
                        not args.no_show, 
                        args.show_all_ticks, 
                        args.max_ticks
                    )
        elif args.monitor:
            monitor.start_monitoring(args.interval, args.duration)
            logger.info("Monitoring started, press Ctrl+C to stop")
            
            try:
                while monitor.monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
            
            monitor.stop_monitoring()
            
            # Save data
            if args.save_data:
                monitor.save_data_to_file(args.save_data)
            else:
                # Default save data
                monitor.save_data_to_file()
            
            # Display summary
            monitor.print_summary()
            
            # Generate visualization
            if args.visualize:
                monitor.generate_visualization(
                    args.output, 
                    not args.no_show, 
                    args.show_all_ticks, 
                    args.max_ticks
                )
            
            # Generate performance report
            if args.generate_report:
                command_params = {
                    'targets': args.targets,
                    'interval': args.interval,
                    'duration': args.duration,
                    'version': 'v1.0'
                }
                monitor.generate_performance_report(command_params=command_params)
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Program execution error: {e}")
    finally:
        monitor.stop_monitoring()

if __name__ == '__main__':
    main()
