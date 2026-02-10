import sys
import os
import json

# 1. 路径修正：确保能导入 core 和 utils
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.ssh_client import NetworkDevice

# 设备配置信息
DEVICE_CONFIG = {
    'host': '192.168.10.1',
    'username': 'admin',
    'password': 'Admin@123', 
    'port': 22,
    'device_type': 'huawei_vrp'
}

def verify_ntc_feasibility(device):
    """验证 NTC-Templates 可行性 (display version)"""
    print(f"\n--- [1] 验证 NTC-Templates 可行性 ---")
    target_command = "display version"
    
    print(f"执行命令: {target_command} ...")
    result = device.get_parsed_output(target_command)

    if isinstance(result, list) and len(result) > 0:
        data = result[0]
        print("\n✅ 验证成功！")
        print(f"VRP 版本  : {data.get('vrp_version', data.get('version', 'N/A'))}")
        print(f"运行时间  : {data.get('uptime', 'N/A')}")
        print(f"设备型号  : {data.get('model', 'N/A')}")
    else:
        print("\n❌ 验证失败")

def run_automation_task():
    print("=== 启动网络自动化巡检任务 ===")
    
    with NetworkDevice(**DEVICE_CONFIG) as device:
        # 1. 进入系统视图
        device.execute_command("system-view", expect_prompt=b']')

        # 2. 基础验证
        # verify_ntc_feasibility(device)
        
        # ----------------------------------------------------
        # 3. 获取接口信息并打印 (这是你刚才成功但没看到结果的部分)
        # ----------------------------------------------------
        print("\n--- [2] 获取接口状态 (display interface brief) ---")
        command = "display interface brief"
        
        # 获取解析后的数据 (这是一个 List[Dict])
        interfaces = device.get_parsed_output(command)
        
        if isinstance(interfaces, list):
             print(f"✅ 成功获取 {len(interfaces)} 个接口信息。")
             
             # 【方法 1】使用 json.dumps 美化打印所有数据 (调试神器)
             print("\n[详细数据 - JSON格式]:")
             print(json.dumps(interfaces, indent=2, ensure_ascii=False))
            

if __name__ == "__main__":
    run_automation_task()