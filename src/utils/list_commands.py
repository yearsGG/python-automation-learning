import os
import sys
import csv

# 定义我们关注的平台
TARGET_PLATFORM = 'huawei_vrp'

def find_ntc_index():
    """
    自动寻找 ntc-templates 的 index 文件路径
    """
    # 获取当前脚本所在路径: src/utils/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 项目根目录 (假设结构为 project_root/src/utils/list_commands.py)
    # dirname(src/utils) -> src
    # dirname(src) -> project_root
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    print(f"🔍 [调试] 推断的项目根目录: {project_root}")

    # 可能的路径 (兼容你的双层目录结构)
    potential_paths = [
        os.path.join(project_root, 'ntc-templates', 'templates', 'index'),
        os.path.join(project_root, 'ntc-templates', 'templates', 'templates', 'index'),
    ]
    
    # 1. 优先查找本地目录
    for path in potential_paths:
        if os.path.exists(path):
            return path
        else:
            print(f"   [跳过] 本地路径不存在: {path}")

    # 2. 备选：尝试查找 pip 安装的 ntc_templates 库位置
    try:
        import ntc_templates
        # 获取库的安装路径
        lib_path = os.path.dirname(ntc_templates.__file__)
        package_index = os.path.join(lib_path, 'templates', 'index')
        if os.path.exists(package_index):
            print(f"   [提示] 找到 pip 安装版: {package_index}")
            return package_index
        else:
            print(f"   [跳过] pip 包路径不存在: {package_index}")
    except ImportError:
        pass
    
    return None

def list_supported_commands():
    index_path = find_ntc_index()
    if not index_path:
        print("\n❌ 严重错误：在上述路径中均未找到 index 文件。")
        print("建议排查：")
        print("1. 确认 ntc-templates 文件夹是否在项目根目录下。")
        print("2. 确认 ntc-templates/templates/ 目录下是否有 'index' 文件。")
        return

    print(f"\n✅ 最终使用索引文件: {index_path}")
    print(f"🔍 正在筛选平台 [{TARGET_PLATFORM}] 支持的命令...\n")
    
    supported_commands = []

    # 解析 index 文件 (它本质上是一个 CSV)
    # 格式通常是: Template, Hostname, Platform, Command
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            # 跳过前面的注释行，直到读到表头或数据
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            reader = csv.reader(lines)
            for row in reader:
                if len(row) >= 4:
                    template_file = row[0].strip()
                    platform = row[2].strip()
                    command_regex = row[3].strip()
                    
                    if platform == TARGET_PLATFORM:
                        supported_commands.append({
                            'command': command_regex,
                            'file': template_file
                        })
    except Exception as e:
        print(f"❌ 解析索引文件失败: {e}")
        return

    # 打印结果
    print(f"{'命令 (支持正则匹配)':<50} | {'对应的模板文件名'}")
    print("-" * 90)
    
    # 排序后打印
    supported_commands.sort(key=lambda x: x['command'])
    
    for item in supported_commands:
        # 去除 regex 的一些复杂符号，让它看起来更像人话
        # 比如 '^display version$' -> 'display version'
        cmd_display = item['command'].replace('^', '').replace('$', '').strip()
        print(f"{cmd_display:<50} | {item['file']}")

    print("-" * 90)
    print(f"📊 总计: {TARGET_PLATFORM} 平台共支持 {len(supported_commands)} 条命令解析。")
    print("💡 提示: 在 main.py 中调用 get_parsed_output('命令') 即可直接使用。")

if __name__ == "__main__":
    list_supported_commands()