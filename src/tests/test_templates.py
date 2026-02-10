import sys
import os
import json

# 1. 路径修正：确保能导入 core 模块 (和你 text1.py 一模一样)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.ssh_client import NetworkDevice

# 2. 设备配置 (请确保 IP 是你的 AR1000v 或 S9850)
DEVICE_CONFIG = {
    'host': '192.168.10.1',    # <--- 如果连不上，请改为你拓扑图中正确的 IP
    'username': 'admin',
    'password': 'Admin@123', 
    'port': 22,
    'device_type': 'huawei_vrp' # 关键：这会告诉 NTC 使用 huawei_vrp_ 开头的模板
}

# 3. 根据你提供的 grep 列表，整理出的“必测命令清单”
# 只有这些命令在你的库里有模板，其他的命令跑了也解析不出来
COMMANDS_TO_TEST = [
    # ==============================
    # 1. 核心资产与系统信息
    # ==============================
    "display version",                  # 设备型号、版本、运行时间
    "display startup",                  # 启动文件检查
    "display snmp-agent community read",# SNMP 配置检查

    # ==============================
    # 2. 接口状态 (网络自动化的基石)
    # ==============================
    "display interface brief",          # 接口物理/协议状态概览 (最常用)
    "display interface",                # 详细接口统计 (流量、错误包、MAC地址)
    "display eth-trunk",                # 链路聚合状态

    # 注意：下面这个命令，只有在你按上一轮教程新建了 
    # huawei_vrp_display_ip_interface_brief.textfsm 模板后才能跑通
    "display ip interface brief",       # 接口 IP 地址概览

    # ==============================
    # 3. 三层路由与转发
    # ==============================
    "display ip routing-table verbose", # 路由表详情
    "display arp all",                  # ARP 表 (IP <-> MAC 映射)
    
    # ==============================
    # 4. 二层交换与 VLAN
    # ==============================
    "display vlan",                     # VLAN 详细信息
    "display vlan brief",               # VLAN 简要信息

    # ==============================
    # 5. 安全与策略
    # ==============================
    "display acl all",                  # 访问控制列表
    
    # ==============================
    # 6. 预留的高级功能 (目前为空但解析成功，以后配了BGP/NAT能用到)
    # ==============================
    "display nat server",               # NAT 映射
    "display bgp peer",                 # BGP 邻居
    "display traffic-filter applied-record" # 流量过滤记录
]

def run_template_scan():
    print("=== 🚀 开始 NTC 模板可用性扫描 ===")
    
    # 使用 with 语句自动管理连接 (和你 text1.py 的做法一致)
    try:
        with NetworkDevice(**DEVICE_CONFIG) as device:
            # 这里的 expect_prompt=b']' 假设你是系统视图，或者你可以不传让它自动猜
            device.execute_command("system-view", expect_prompt=b']')

            success_count = 0
            
            for cmd in COMMANDS_TO_TEST:
                print(f"\n------------------------------------------------")
                print(f"Testing Command: [ {cmd} ]")
                
                # 获取解析结果
                result = device.get_parsed_output(cmd)

                # 判断逻辑：如果返回的是 List，说明解析成功；如果是 String，说明失败返回了原始文本
                if isinstance(result, list):
                    count = len(result)
                    print(f"✅ 解析成功！抓取到 {count} 条记录")
                    if count > 0:
                        # 打印第一条数据来看看字段名 (Keys)
                        first_record = result[0]
                        print(f"   字段预览: {list(first_record.keys())}")
                    success_count += 1
                else:
                    # 如果返回的是字符串，或者空列表(视情况)，通常意味着匹配失败
                    print(f"❌ 解析失败 (返回了原始文本)")
            
            print(f"\n================================================")
            print(f"📊 扫描总结: 共测试 {len(COMMANDS_TO_TEST)} 个命令，成功 {success_count} 个")

    except Exception as e:
        print(f"\n!!! 连接发生错误: {e}")

if __name__ == "__main__":
    run_template_scan()