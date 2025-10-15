"""
网络设备巡检模块 - Device Inspector Module
支持批量设备巡检、性能采集、报告生成和告警

作者：袁瑞
版本：v2.0
日期：2025-10-15
"""

import time
import subprocess
import platform
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from colorama import Fore, Style, init

init(autoreset=True)


class DeviceInspector:
    """设备巡检器 - 核心类"""
    
    def __init__(self, max_workers=5):
        """
        初始化巡检器
        
        Args:
            max_workers: 最大并发线程数（默认5）
        """
        self.max_workers = max_workers
        self.results = {}
        
    def ping(self, host: str, count: int = 3, timeout: int = 3) -> Dict:
        """
        Ping检测设备可达性
        
        Args:
            host: 目标主机IP
            count: Ping包数量
            timeout: 超时时间（秒）
            
        Returns:
            {
                'host': str,
                'reachable': bool,
                'avg_rtt': float (ms),
                'packet_loss': float (%),
                'error': str or None
            }
        """
        print(Fore.CYAN + f"[Ping检测] 正在检测 {host}...")
        
        result = {
            'host': host,
            'reachable': False,
            'avg_rtt': None,
            'packet_loss': 100.0,
            'error': None
        }
        
        try:
            # 根据操作系统选择ping命令
            if platform.system().lower() == 'windows':
                cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
            else:
                cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
            
            # 执行ping命令
            output = subprocess.check_output(
                cmd, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=timeout * count + 5
            )
            
            # 解析结果（Windows）
            if platform.system().lower() == 'windows':
                # 检查丢包率
                loss_match = re.search(r'(\d+)%.*loss', output, re.IGNORECASE)
                if loss_match:
                    result['packet_loss'] = float(loss_match.group(1))
                
                # 检查平均延迟
                rtt_match = re.search(r'Average = (\d+)ms', output, re.IGNORECASE)
                if rtt_match:
                    result['avg_rtt'] = float(rtt_match.group(1))
            else:
                # Linux/Mac解析
                loss_match = re.search(r'(\d+)% packet loss', output)
                if loss_match:
                    result['packet_loss'] = float(loss_match.group(1))
                    
                rtt_match = re.search(r'avg = ([\d.]+)', output)
                if rtt_match:
                    result['avg_rtt'] = float(rtt_match.group(1))
            
            # 判断可达性
            result['reachable'] = result['packet_loss'] < 100
            
            if result['reachable']:
                print(Fore.GREEN + f"✓ {host} 在线 (RTT: {result['avg_rtt']}ms)")
            else:
                print(Fore.RED + f"✗ {host} 离线")
                
        except subprocess.TimeoutExpired:
            result['error'] = 'Ping超时'
            print(Fore.RED + f"✗ {host} 超时")
        except subprocess.CalledProcessError:
            result['error'] = 'Ping失败（目标不可达）'
            print(Fore.RED + f"✗ {host} 不可达")
        except Exception as e:
            result['error'] = str(e)
            print(Fore.RED + f"✗ {host} 错误: {e}")
        
        return result
    
    def batch_ping(self, hosts: List[str]) -> Dict[str, Dict]:
        """
        批量Ping检测
        
        Args:
            hosts: IP地址列表
            
        Returns:
            {host: ping_result, ...}
        """
        print(Fore.YELLOW + f"\n{'='*60}")
        print(Fore.YELLOW + f"开始批量Ping检测 - 共 {len(hosts)} 台设备")
        print(Fore.YELLOW + f"{'='*60}\n")
        
        results = {}
        start_time = time.time()
        
        # 使用线程池并发执行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_host = {
                executor.submit(self.ping, host): host 
                for host in hosts
            }
            
            for future in as_completed(future_to_host):
                result = future.result()
                results[result['host']] = result
        
        elapsed = time.time() - start_time
        
        # 统计结果
        online_count = sum(1 for r in results.values() if r['reachable'])
        offline_count = len(hosts) - online_count
        
        print(Fore.YELLOW + f"\n{'='*60}")
        print(Fore.GREEN + f"✓ 在线: {online_count}/{len(hosts)}")
        print(Fore.RED + f"✗ 离线: {offline_count}/{len(hosts)}")
        print(Fore.CYAN + f"⏱ 耗时: {elapsed:.2f}秒")
        print(Fore.YELLOW + f"{'='*60}\n")
        
        return results
    
    def collect_device_info(self, ssh_session, prompts: Dict) -> Dict:
        """
        通过SSH采集设备信息
        
        Args:
            ssh_session: VisualSSH实例
            prompts: 提示符字典 {'user': b'>', 'system': b']'}
            
        Returns:
            {
                'cpu_usage': float,
                'memory_usage': float,
                'interfaces': list,
                'version': str,
                'uptime': str
            }
        """
        print(Fore.CYAN + "[设备信息采集] 开始采集...")
        
        info = {
            'cpu_usage': None,
            'memory_usage': None,
            'interfaces': [],
            'version': None,
            'uptime': None,
            'raw_outputs': {}
        }
        
        try:
            # 进入系统视图（如果还没有）
            ssh_session.write(b"system-view")
            ssh_session.read_until(prompts.get('system', b']'))
            
            # 1. 采集CPU使用率
            print(Fore.CYAN + "  - 采集CPU使用率...")
            output = ssh_session.execute(b"display cpu-usage")
            info['raw_outputs']['cpu'] = output
            
            # 解析CPU（示例：提取数字）
            cpu_match = re.search(r'(\d+)%', output)
            if cpu_match:
                info['cpu_usage'] = float(cpu_match.group(1))
                print(Fore.GREEN + f"    CPU使用率: {info['cpu_usage']}%")
            
            # 2. 采集内存使用率
            print(Fore.CYAN + "  - 采集内存使用率...")
            output = ssh_session.execute(b"display memory-usage")
            info['raw_outputs']['memory'] = output
            
            # 解析内存（示例：提取数字）
            mem_match = re.search(r'(\d+)%', output)
            if mem_match:
                info['memory_usage'] = float(mem_match.group(1))
                print(Fore.GREEN + f"    内存使用率: {info['memory_usage']}%")
            
            # 3. 采集接口状态
            print(Fore.CYAN + "  - 采集接口状态...")
            output = ssh_session.execute(b"display ip interface brief")
            info['raw_outputs']['interfaces'] = output
            
            # 简单解析接口（实际项目中应使用TextFSM）
            lines = output.split('\n')
            for line in lines:
                if 'up' in line.lower() or 'down' in line.lower():
                    info['interfaces'].append(line.strip())
            
            print(Fore.GREEN + f"    接口数量: {len(info['interfaces'])}")
            
            # 4. 采集版本信息
            print(Fore.CYAN + "  - 采集版本信息...")
            output = ssh_session.execute(b"display version")
            info['raw_outputs']['version'] = output
            
            # 提取版本号（示例）
            version_match = re.search(r'Version ([\d.]+)', output, re.IGNORECASE)
            if version_match:
                info['version'] = version_match.group(1)
                print(Fore.GREEN + f"    版本: {info['version']}")
            
            print(Fore.GREEN + "✓ 设备信息采集完成\n")
            
        except Exception as e:
            print(Fore.RED + f"✗ 采集失败: {e}\n")
            info['error'] = str(e)
        
        return info
    
    def check_thresholds(self, device_name: str, info: Dict, 
                        thresholds: Dict = None) -> List[str]:
        """
        检查性能阈值并生成告警
        
        Args:
            device_name: 设备名称
            info: 设备信息字典
            thresholds: 阈值字典 {'cpu': 80, 'memory': 70}
            
        Returns:
            告警消息列表
        """
        if thresholds is None:
            thresholds = {'cpu': 80, 'memory': 70}
        
        alerts = []
        
        # 检查CPU
        if info.get('cpu_usage') is not None:
            if info['cpu_usage'] > thresholds.get('cpu', 80):
                msg = f"⚠️  {device_name} CPU使用率过高: {info['cpu_usage']}%"
                alerts.append(msg)
                print(Fore.YELLOW + msg)
        
        # 检查内存
        if info.get('memory_usage') is not None:
            if info['memory_usage'] > thresholds.get('memory', 70):
                msg = f"⚠️  {device_name} 内存使用率过高: {info['memory_usage']}%"
                alerts.append(msg)
                print(Fore.YELLOW + msg)
        
        # 检查接口Down（简单示例）
        down_interfaces = [
            intf for intf in info.get('interfaces', []) 
            if 'down' in intf.lower()
        ]
        if down_interfaces:
            msg = f"⚠️  {device_name} 有 {len(down_interfaces)} 个接口Down"
            alerts.append(msg)
            print(Fore.YELLOW + msg)
        
        return alerts
    
    def generate_text_report(self, results: Dict, filename: str = None) -> str:
        """
        生成文本格式巡检报告
        
        Args:
            results: 巡检结果字典
            filename: 保存文件名（可选）
            
        Returns:
            报告文本内容
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("网络设备巡检报告".center(80))
        report_lines.append("=" * 80)
        report_lines.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"巡检设备数量: {len(results)}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # 汇总统计
        online_devices = sum(1 for r in results.values() if r.get('ping', {}).get('reachable'))
        report_lines.append(f"【设备可用性】")
        report_lines.append(f"  在线设备: {online_devices}/{len(results)}")
        report_lines.append(f"  离线设备: {len(results) - online_devices}/{len(results)}")
        report_lines.append("")
        
        # 详细信息
        report_lines.append("【详细巡检结果】")
        report_lines.append("")
        
        for device_name, data in results.items():
            report_lines.append(f"设备: {device_name}")
            report_lines.append("-" * 80)
            
            # Ping结果
            ping_result = data.get('ping', {})
            if ping_result.get('reachable'):
                report_lines.append(f"  状态: ✓ 在线")
                report_lines.append(f"  延迟: {ping_result.get('avg_rtt', 'N/A')} ms")
                report_lines.append(f"  丢包率: {ping_result.get('packet_loss', 'N/A')}%")
            else:
                report_lines.append(f"  状态: ✗ 离线")
                if ping_result.get('error'):
                    report_lines.append(f"  错误: {ping_result['error']}")
            
            # 设备信息
            device_info = data.get('info', {})
            if device_info:
                report_lines.append(f"  CPU使用率: {device_info.get('cpu_usage', 'N/A')}%")
                report_lines.append(f"  内存使用率: {device_info.get('memory_usage', 'N/A')}%")
                report_lines.append(f"  接口数量: {len(device_info.get('interfaces', []))}")
                report_lines.append(f"  系统版本: {device_info.get('version', 'N/A')}")
            
            # 告警信息
            alerts = data.get('alerts', [])
            if alerts:
                report_lines.append(f"  ⚠️  告警: {len(alerts)}条")
                for alert in alerts:
                    report_lines.append(f"    - {alert}")
            
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("报告结束".center(80))
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        
        # 保存到文件
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(Fore.GREEN + f"✓ 报告已保存: {filename}")
        
        return report_text


class EmailAlerter:
    """邮件告警类"""
    
    def __init__(self, smtp_server: str, smtp_port: int, 
                 username: str, password: str):
        """
        初始化邮件告警器
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            username: 邮箱用户名
            password: 邮箱密码
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_alert(self, subject: str, body: str, to_addrs: List[str]):
        """
        发送告警邮件
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            to_addrs: 收件人列表
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(to_addrs)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 连接SMTP服务器
            print(Fore.CYAN + f"正在连接SMTP服务器 {self.smtp_server}:{self.smtp_port}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            # 发送邮件
            server.send_message(msg)
            server.quit()
            
            print(Fore.GREEN + f"✓ 告警邮件已发送至 {', '.join(to_addrs)}")
            
        except Exception as e:
            print(Fore.RED + f"✗ 邮件发送失败: {e}")


def demo_ping_inspection():
    """演示：批量Ping巡检"""
    print(Fore.MAGENTA + Style.BRIGHT + "\n【演示】批量Ping巡检\n")
    
    inspector = DeviceInspector(max_workers=5)
    
    # 测试设备列表（请替换为实际IP）
    test_hosts = [
        '192.168.85.253',
        '192.168.85.254',
        '8.8.8.8',  # 公网DNS（测试）
        '1.1.1.1',  # Cloudflare DNS（测试）
    ]
    
    results = inspector.batch_ping(test_hosts)
    
    # 生成报告
    report_results = {
        host: {'ping': result} 
        for host, result in results.items()
    }
    
    report_file = f"reports/ping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    inspector.generate_text_report(report_results, filename=report_file)


if __name__ == "__main__":
    print(Fore.YELLOW + Style.BRIGHT + """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║       网络设备巡检模块 - Device Inspector v2.0           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 运行演示
    demo_ping_inspection()
    
    print(Fore.CYAN + "\n提示: 要进行完整巡检（包含SSH采集），请使用 main_inspection.py\n")

