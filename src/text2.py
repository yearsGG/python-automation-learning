import os
import sys
import json

# ==========================================
# 1. 环境自动配置 (为了让脚本能找到你本地的 ntc-templates)
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# A. 添加 ntc-templates 库到 Python 搜索路径
# 这样 'from ntc_templates.parse import ...' 才能生效
lib_path = os.path.join(project_root, 'ntc-templates')
if os.path.exists(lib_path):
    sys.path.append(lib_path)

# B. 设置模板目录环境变量 (NTC_TEMPLATES_DIR)
# 自动寻找包含 'index' 文件的正确目录
potential_paths = [
    os.path.join(project_root, 'ntc-templates', 'templates', 'templates'), # 你的环境可能是这个双层结构
    os.path.join(project_root, 'ntc-templates', 'templates'),              # 标准结构
]

template_dir = None
for path in potential_paths:
    if os.path.exists(os.path.join(path, 'index')):
        template_dir = path
        break

if template_dir:
    os.environ["NTC_TEMPLATES_DIR"] = template_dir
    print(f"✅ 环境配置成功: NTC_TEMPLATES_DIR = {template_dir}")
else:
    print("❌ 警告: 未找到 templates/index 文件，解析可能会失败")

# ==========================================
# 2. 导入官方解析函数
# ==========================================
try:
    from ntc_templates.parse import parse_output
    print("✅ 成功导入 ntc_templates.parse.parse_output")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请检查 ntc-templates 文件夹是否完整")
    sys.exit(1)

# ==========================================
# 3. 执行测试 (你的 Cisco 用例)
# ==========================================
def test_static_cisco_vlan():
    print("\n--- 开始静态数据测试 (Cisco IOS: show vlan) ---")
    
    # 模拟的设备输出数据
    vlan_output = (
        "VLAN Name                             Status    Ports\n"
        "---- -------------------------------- --------- -------------------------------\n"
        "1    default                          active    Gi0/1\n"
        "10   Management                       active    \n"
        "50   VLan50                           active    Fa0/1, Fa0/2, Fa0/3, Fa0/4, Fa0/5,\n"
        "                                                Fa0/6, Fa0/7, Fa0/8\n"
    )
    
    try:
        # 调用 parse_output
        # platform="cisco_ios" 会让库去 index 文件查找 cisco_ios_show_vlan.textfsm
        vlan_parsed = parse_output(platform="cisco_ios", command="show vlan", data=vlan_output)
        
        # 打印结果
        print("解析结果 (JSON):")
        print(json.dumps(vlan_parsed, indent=4))
        
        # 简单的断言验证
        if len(vlan_parsed) == 3:
             print("\n✅ 测试通过！成功解析出 3 个 VLAN。")
        else:
             print("\n❌ 测试失败：解析出的条目数量不正确。")
             
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")

if __name__ == "__main__":
    test_static_cisco_vlan()