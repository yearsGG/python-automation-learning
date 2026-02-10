import logging
import json
import sys
import os

# 1. 确保能导入同级目录下的 VisualSSH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from my_visual_ssh import VisualSSH

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='ssh_test_route.log',
    filemode='w'
)
logger = logging.getLogger(__name__)

def test_route_parsing():
    # === 配置区域 ===
    device = {
        'host': '192.168.10.1',
        'username': 'admin',
        'password': 'Admin@123',  # 请确保密码正确
        'port': 22
    }

    print(f"正在连接到 {device['host']} 进行路由表测试...")

    ssh = VisualSSH(
        host=device['host'], 
        username=device['username'], 
        password=device['password'], 
        logger=logger
    )

    try:
        # 建立连接并进入系统视图
        ssh.read_until(b'>') 
        ssh.write(b'system-view\n')
        ssh.read_until(b']')

        # ==========================================
        # 测试点：使用官方接口解析路由表
        # ==========================================
        print("\n正在测试路由表解析 (display ip routing-table verbose)...")
        print("注意：该命令输出较长，VisualSSH 将自动处理翻页，请耐心等待...")
        
        # 【关键修改】不再需要 template_name，改为指定 platform
        # ntc-templates 会根据 'huawei_vrp' + 'display ip routing-table verbose' 自动找到那个文件
        target_command = 'display ip routing-table verbose'
        target_platform = 'huawei_vrp'
        
        # 执行命令
        routes = ssh.execute_and_parse(
            command=target_command,
            platform=target_platform  # <--- 这里改了
        )

        # 4. 验证结果
        if isinstance(routes, list) and len(routes) > 0:
            print(f"\n✅ 解析成功！一共找到了 {len(routes)} 条路由条目。")
            
            # 打印前 2 条数据供检查
            print("--- 数据预览 (前2条) ---")
            print(json.dumps(routes[:2], indent=2))
            
            # 简单校验字段 (TextFSM 模板里的字段通常是大写的)
            first_route = routes[0]
            # 注意：ntc-templates 解析出来的键通常是小写的，但也可能是大写，取决于模板
            # 这里的模板通常是大写的，我们打印一下看看
            print(f"\n第一条路由信息: {first_route}")
            
        else:
            print("\n❌ 解析失败或返回了原始文本。")
            print("返回类型:", type(routes))
            # 如果失败了，打印前 500 个字符看看是不是回显没切干净
            if isinstance(routes, str):
                print("--- 原始文本前 500 字符 ---")
                print(routes[:500])

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    test_route_parsing()