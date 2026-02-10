from flask import Flask, render_template, jsonify
import sys
import os

# 1. 引入刚才写的数据库模块
# 注意：确保 src/app/ 目录下有 __init__.py 文件（如果没有，创建一个空文件即可）
from app.database import init_db, save_log, get_history

# 确保能导入 core 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ssh_client import NetworkDevice

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# 设备配置
DEVICE_CONFIG = {
    'host': '192.168.10.1',
    'username': 'admin',
    'password': 'Admin@123',
    'device_type': 'huawei_vrp'
}

# 模板路径 (保持不变)
TEMPLATE_PATH = "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_ip_interface_brief.textfsm"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan/interfaces')
def scan_interfaces():
    command = "display ip interface brief"  # 定义命令变量方便存库
    try:
        with NetworkDevice(**DEVICE_CONFIG) as device:
            # 1. 进系统视图
            device.execute_command("system-view") 
            
            # 2. 执行巡检
            data = device.get_output_with_template(command, TEMPLATE_PATH)
            
            # 3. 检查是否出错 (如果返回字典且包含 error Key)
            if isinstance(data, dict) and "error" in data:
                 # ❌ 记录失败日志
                 save_log(DEVICE_CONFIG['host'], command, data, status="error")
                 return jsonify({"status": "error", "message": data["error"]})

            # ✅ 记录成功日志 (核心改动在这里！)
            save_log(DEVICE_CONFIG['host'], command, data, status="success")
            
            return jsonify({"status": "success", "data": data})

    except Exception as e:
        # 打印报错方便调试
        import traceback
        traceback.print_exc()
        
        # ❌ 记录异常日志
        save_log(DEVICE_CONFIG['host'], command, str(e), status="exception")
        return jsonify({"status": "error", "message": str(e)})

# --- 新增路由: 获取历史记录 API (为下一步前端做准备) ---
@app.route('/api/history')
def api_history():
    logs = get_history()
    return jsonify({"status": "success", "data": logs})

if __name__ == '__main__':
    # 4. 启动应用前，先初始化数据库 (建表)
    init_db()
    
    # 保持使用 5001 端口
    app.run(host='0.0.0.0', port=5001, debug=True)