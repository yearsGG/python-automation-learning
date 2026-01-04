"""
网络设备自动化巡检主程序
整合Ping检测、SSH信息采集、报告生成和告警功能

作者：袁瑞
版本：v2.0
日期：2025-10-15
"""

import configparser
import os
from datetime import datetime
from colorama import Fore, Style, init
from my_visual_ssh import VisualSSH
from device_inspector import DeviceInspector, EmailAlerter

init(autoreset=True)


def load_inspection_config(filename='inspection_config.ini'):
    """
    读取巡检配置文件
    
    Returns:
        {
            'devices': [{'name': '', 'host': '', 'username': '', 'password': ''}],
            'thresholds': {'cpu': 80, 'memory': 70},
            'email': {...},
            'options': {...}
        }
    """
    print(Fore.YELLOW + "--- 正在加载巡检配置... ---")
    
    if not os.path.exists(filename):
        print(Fore.RED + f"配置文件不存在: {filename}")
        print(Fore.YELLOW + "将使用默认配置（从 config.ini 读取）")
        return load_default_config()
    
    parser = configparser.ConfigParser()
    parser.read(filename, encoding='utf-8')
    
    config = {
        'devices': [],
        'thresholds': {},
        'email': {},
        'options': {}
    }
    
    # 读取设备列表
    if parser.has_section('devices'):
        device_count = parser.getint('devices', 'count', fallback=1)
        for i in range(1, device_count + 1):
            device = {
                'name': parser.get('devices', f'device{i}_name', fallback=f'Device{i}'),
                'host': parser.get('devices', f'device{i}_host'),
                'port': parser.getint('devices', f'device{i}_port', fallback=22),
                'username': parser.get('devices', f'device{i}_username'),
                'password': parser.get('devices', f'device{i}_password'),
            }
            config['devices'].append(device)
    
    # 读取阈值配置
    if parser.has_section('thresholds'):
        config['thresholds'] = {
            'cpu': parser.getint('thresholds', 'cpu_threshold', fallback=80),
            'memory': parser.getint('thresholds', 'memory_threshold', fallback=70),
        }
    
    # 读取邮件配置
    if parser.has_section('email'):
        config['email'] = {
            'enabled': parser.getboolean('email', 'enabled', fallback=False),
            'smtp_server': parser.get('email', 'smtp_server', fallback=''),
            'smtp_port': parser.getint('email', 'smtp_port', fallback=587),
            'username': parser.get('email', 'username', fallback=''),
            'password': parser.get('email', 'password', fallback=''),
            'to_addrs': parser.get('email', 'to_addrs', fallback='').split(','),
        }
    
    # 读取选项
    if parser.has_section('options'):
        config['options'] = {
            'enable_ping': parser.getboolean('options', 'enable_ping', fallback=True),
            'enable_ssh': parser.getboolean('options', 'enable_ssh', fallback=True),
            'max_workers': parser.getint('options', 'max_workers', fallback=5),
            'save_report': parser.getboolean('options', 'save_report', fallback=True),
        }
    
    print(Fore.GREEN + f"✓ 配置加载成功！共 {len(config['devices'])} 台设备")
    return config


def load_default_config():
    """从默认config.ini加载单设备配置"""
    parser = configparser.ConfigParser()
    parser.read('config.ini', encoding='utf-8')
    
    config = {
        'devices': [{
            'name': 'DefaultDevice',
            'host': parser.get('device_info', 'host'),
            'port': parser.getint('device_info', 'port', fallback=22),
            'username': parser.get('device_info', 'username'),
            'password': parser.get('device_info', 'password'),
        }],
        'thresholds': {'cpu': 80, 'memory': 70},
        'email': {'enabled': False},
        'options': {
            'enable_ping': True,
            'enable_ssh': True,
            'max_workers': 3,
            'save_report': True,
        }
    }
    
    return config


def inspect_single_device_ssh(device: dict, thresholds: dict) -> dict:
    """
    对单台设备进行SSH巡检
    
    Args:
        device: 设备信息字典
        thresholds: 阈值配置
        
    Returns:
        巡检结果字典
    """
    result = {
        'name': device['name'],
        'host': device['host'],
        'info': {},
        'alerts': [],
        'error': None
    }
    
    ssh = None
    try:
        print(Fore.CYAN + f"\n{'='*60}")
        print(Fore.CYAN + f"开始SSH巡检: {device['name']} ({device['host']})")
        print(Fore.CYAN + f"{'='*60}")
        
        # 连接设备
        ssh = VisualSSH(
            host=device['host'],
            port=device.get('port', 22),
            username=device['username'],
            password=device['password'],
            timeout=10
        )
        
        # 等待用户提示符
        USER_PROMPT = b'>'
        SYSTEM_PROMPT = b']'
        
        ssh.read_until(USER_PROMPT)
        
        # 使用巡检器采集信息
        inspector = DeviceInspector()
        device_info = inspector.collect_device_info(
            ssh, 
            prompts={'user': USER_PROMPT, 'system': SYSTEM_PROMPT}
        )
        
        result['info'] = device_info
        
        # 检查阈值告警
        alerts = inspector.check_thresholds(
            device['name'], 
            device_info, 
            thresholds
        )
        result['alerts'] = alerts
        
        print(Fore.GREEN + f"✓ {device['name']} SSH巡检完成")
        
    except Exception as e:
        result['error'] = str(e)
        print(Fore.RED + f"✗ {device['name']} SSH巡检失败: {e}")
        
    finally:
        if ssh:
            ssh.close()
    
    return result


def run_full_inspection(config: dict):
    """
    执行完整巡检流程
    
    Args:
        config: 配置字典
    """
    print(Fore.MAGENTA + Style.BRIGHT + f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          网络设备自动化巡检系统 v2.0                     ║
    ║          开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    inspector = DeviceInspector(max_workers=config['options'].get('max_workers', 5))
    all_results = {}
    
    # ========== 第一步：批量Ping检测 ==========
    if config['options'].get('enable_ping', True):
        print(Fore.YELLOW + "\n【第一步】批量Ping连通性检测\n")
        
        hosts = [device['host'] for device in config['devices']]
        ping_results = inspector.batch_ping(hosts)
        
        # 保存Ping结果
        for device in config['devices']:
            device_name = device['name']
            all_results[device_name] = {
                'ping': ping_results.get(device['host'], {}),
                'info': {},
                'alerts': []
            }
    
    # ========== 第二步：SSH信息采集 ==========
    if config['options'].get('enable_ssh', True):
        print(Fore.YELLOW + "\n【第二步】SSH设备信息采集\n")
        
        for device in config['devices']:
            device_name = device['name']
            
            # 如果Ping不通，跳过SSH采集
            if not all_results[device_name]['ping'].get('reachable', False):
                print(Fore.YELLOW + f"⊗ {device_name} 不可达，跳过SSH采集")
                continue
            
            # 执行SSH巡检
            ssh_result = inspect_single_device_ssh(device, config['thresholds'])
            
            # 合并结果
            all_results[device_name]['info'] = ssh_result.get('info', {})
            all_results[device_name]['alerts'].extend(ssh_result.get('alerts', []))
            if ssh_result.get('error'):
                all_results[device_name]['ssh_error'] = ssh_result['error']
    
    # ========== 第三步：生成报告 ==========
    print(Fore.YELLOW + "\n【第三步】生成巡检报告\n")
    
    if config['options'].get('save_report', True):
        # 创建reports目录
        os.makedirs('reports', exist_ok=True)
        
        # 生成文本报告
        report_filename = f"reports/inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_text = inspector.generate_text_report(all_results, filename=report_filename)
        
        # 同时打印到屏幕
        print(Fore.WHITE + "\n" + "="*80)
        print(report_text)
        print("="*80 + "\n")
    
    # ========== 第四步：告警通知 ==========
    # 统计所有告警
    all_alerts = []
    for device_name, data in all_results.items():
        for alert in data.get('alerts', []):
            all_alerts.append(f"[{device_name}] {alert}")
    
    if all_alerts:
        print(Fore.YELLOW + f"\n【第四步】告警通知 - 共 {len(all_alerts)} 条告警\n")
        
        for alert in all_alerts:
            print(Fore.YELLOW + alert)
        
        # 发送邮件告警（如果启用）
        if config['email'].get('enabled', False):
            try:
                alerter = EmailAlerter(
                    smtp_server=config['email']['smtp_server'],
                    smtp_port=config['email']['smtp_port'],
                    username=config['email']['username'],
                    password=config['email']['password']
                )
                
                subject = f"⚠️  网络设备巡检告警 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                body = "\n".join(all_alerts)
                body += f"\n\n详细报告: {report_filename}"
                
                alerter.send_alert(
                    subject=subject,
                    body=body,
                    to_addrs=config['email']['to_addrs']
                )
            except Exception as e:
                print(Fore.RED + f"邮件告警发送失败: {e}")
    else:
        print(Fore.GREEN + "\n✓ 所有设备状态正常，无告警\n")
    
    # ========== 巡检结束 ==========
    print(Fore.MAGENTA + Style.BRIGHT + f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║          巡检完成！                                       ║
    ║          结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    # 加载配置
    inspection_config = load_inspection_config('inspection_config.ini')
    
    # 执行巡检
    run_full_inspection(inspection_config)

