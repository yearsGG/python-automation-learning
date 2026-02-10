import sys
import os
import json

# 1. 路径修正：确保能导入 core 和 utils
# 将 src 目录加入 Python 搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.ssh_client import NetworkDevice

# 设备配置信息（未来这部分可以从 MySQL 数据库读取）
DEVICE_CONFIG = {
    'host': '192.168.10.1',
    'username': 'admin',
    'password': 'Admin@123', # 你的新密码
    'port': 22,
    'device_type': 'huawei_vrp'
}

def run_automation_task():
    print("=== 启动网络自动化巡检任务 ===")
    
    # 使用 with 语法，自动管理连接的打开和关闭
    with NetworkDevice(**DEVICE_CONFIG) as device:
        
        # 1. 进入系统视图 (通常需要先进入 system-view 才能执行大部分 display 命令不报错，或者保持用户视图也行)
        # 这里演示先进入 system-view
        device.execute_command("system-view", expect_prompt=b']')

        # ----------------------------------------------------
        # 任务 A: 获取并解析版本信息
        # ----------------------------------------------------
        version_info = device.get_parsed_output("display version")
        print(json.dumps(version_info, indent=2))
        
        # ----------------------------------------------------
        # 任务 B: 获取并解析路由表
        # ----------------------------------------------------
        print("\n正在获取路由表...")
        routes = device.get_parsed_output("display ip routing-table verbose")
        
        if isinstance(routes, list):
             print(f"当前设备共有 {len(routes)} 条路由条目。")
        
        # ----------------------------------------------------
        # 任务 C: 自动下发配置 (创建一个测试接口)
        # ----------------------------------------------------
        config_list = [
            "interface Loopback888",
            "ip address 8.8.8.8 32",
            "description Created_by_Automation_Core"
        ]
        device.configure(config_list)
        
        # ----------------------------------------------------
        # 任务 D: 验证配置是否生效
        # ----------------------------------------------------
        print("\n验证 Loopback888 是否创建成功...")
        interfaces = device.get_parsed_output("display interface brief")
        
        found = False
        for iface in interfaces:
            # 华为模板出来的 key 可能是 'INTERFACE' 或 'interface'
            name = iface.get('INTERFACE', iface.get('interface', ''))
            if 'Loopback888' in name:
                print(f"✅ 验证通过！接口 {name} 状态: {iface.get('PHY', 'N/A')}")
                found = True
                break
        
        if not found:
            print("❌ 验证失败：未找到接口。")

if __name__ == "__main__":
    run_automation_task()