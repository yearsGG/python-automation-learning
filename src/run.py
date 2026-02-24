from flask import Flask, render_template, jsonify, request
import sys
import os
import json
from datetime import datetime

# 引入数据库模块
from app.database import init_db, save_log, get_history, get_logs_by_device

# 确保能导入 core 模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.ssh_client import NetworkDevice

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# 设备配置存储（生产环境中应该存储在数据库中）
devices = [
    {
        'id': 1,
        'name': '核心交换机',
        'host': '192.168.10.1',
        'port': 22,
        'username': 'admin',
        'password': 'Admin@123',
        'device_type': 'huawei_vrp',
        'status': 'online'
    }
]

# 模板路径
TEMPLATE_PATH = "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_ip_interface_brief.textfsm"

def get_device_by_id(device_id):
    """根据ID获取设备配置"""
    for device in devices:
        if device['id'] == device_id:
            return device
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/devices')
def get_devices():
    """获取设备列表"""
    return jsonify({"status": "success", "data": devices})

@app.route('/api/devices', methods=['POST'])
def add_device():
    """添加新设备"""
    data = request.get_json()

    new_device = {
        'id': len(devices) + 1,
        'name': data.get('name', ''),
        'host': data.get('host', ''),
        'port': data.get('port', 22),
        'username': data.get('username', ''),
        'password': data.get('password', ''),
        'device_type': data.get('device_type', 'huawei_vrp'),
        'status': 'unknown'
    }

    devices.append(new_device)
    return jsonify({"status": "success", "data": new_device})

@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备配置"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    data = request.get_json()
    for key in ['name', 'host', 'port', 'username', 'password', 'device_type']:
        if key in data:
            device[key] = data[key]

    return jsonify({"status": "success", "data": device})

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    global devices
    devices = [d for d in devices if d['id'] != device_id]
    return jsonify({"status": "success", "message": "Device deleted"})

@app.route('/api/devices/<int:device_id>/connect', methods=['POST'])
def test_connection(device_id):
    """测试设备连接"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    try:
        with NetworkDevice(**{k: v for k, v in device.items() if k in ['host', 'username', 'password', 'port', 'device_type']}) as dev:
            # 尝试执行简单命令测试连接
            result = dev.execute_command("display version", expect_prompt=b']')
            device['status'] = 'online'
            return jsonify({"status": "success", "message": "Connection successful", "data": result})
    except Exception as e:
        device['status'] = 'offline'
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/scan/interfaces')
def scan_interfaces():
    """执行接口巡检"""
    device_id = request.args.get('device_id', default=1, type=int)

    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    command = "display ip interface brief"  # 定义命令变量方便存库

    try:
        with NetworkDevice(**{k: v for k, v in device.items() if k in ['host', 'username', 'password', 'port', 'device_type']}) as dev:
            # 进系统视图
            dev.execute_command("system-view", expect_prompt=b']')

            # 执行巡检
            data = dev.get_output_with_template(command, TEMPLATE_PATH)

            # 检查是否出错 (如果返回字典且包含 error Key)
            if isinstance(data, dict) and "error" in data:
                 # ❌ 记录失败日志
                 save_log(device['host'], command, data, status="error")
                 return jsonify({"status": "error", "message": data["error"]})

            # ✅ 记录成功日志
            save_log(device['host'], command, data, status="success")

            return jsonify({"status": "success", "data": data})

    except Exception as e:
        # 打印报错方便调试
        import traceback
        traceback.print_exc()

        # ❌ 记录异常日志
        save_log(device['host'], command, str(e), status="exception")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/scan/device/<int:device_id>')
def scan_device_interfaces(device_id):
    """针对特定设备执行接口巡检"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    command = "display ip interface brief"

    try:
        with NetworkDevice(**{k: v for k, v in device.items() if k in ['host', 'username', 'password', 'port', 'device_type']}) as dev:
            # 进系统视图
            dev.execute_command("system-view", expect_prompt=b']')

            # 执行巡检
            data = dev.get_output_with_template(command, TEMPLATE_PATH)

            # 检查是否出错
            if isinstance(data, dict) and "error" in data:
                 save_log(device['host'], command, data, status="error")
                 return jsonify({"status": "error", "message": data["error"]})

            save_log(device['host'], command, data, status="success")

            return jsonify({"status": "success", "data": data, "device": device})

    except Exception as e:
        import traceback
        traceback.print_exc()

        save_log(device['host'], command, str(e), status="exception")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/ping-all', methods=['POST'])
def ping_all_devices():
    """对所有设备执行ping测试"""
    results = []
    for device in devices:
        try:
            # 这里应该实现ping功能，暂时模拟
            import subprocess
            result = subprocess.run(['ping', '-c', '1', '-W', '3', device['host']],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            is_reachable = result.returncode == 0
            device['status'] = 'online' if is_reachable else 'offline'
            results.append({
                'device_id': device['id'],
                'host': device['host'],
                'reachable': is_reachable
            })
        except Exception as e:
            device['status'] = 'offline'
            results.append({
                'device_id': device['id'],
                'host': device['host'],
                'reachable': False,
                'error': str(e)
            })

    return jsonify({"status": "success", "data": results})

@app.route('/api/history')
def api_history():
    """获取历史记录"""
    logs = get_history()
    return jsonify({"status": "success", "data": logs})

@app.route('/api/history/device/<int:device_id>')
def api_history_by_device(device_id):
    """获取特定设备的历史记录"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    logs = get_logs_by_device(device['host'])
    return jsonify({"status": "success", "data": logs})

@app.route('/api/dashboard/stats')
def get_dashboard_stats():
    """获取仪表板统计信息"""
    total_devices = len(devices)
    online_devices = len([d for d in devices if d.get('status') == 'online'])
    offline_devices = len([d for d in devices if d.get('status') == 'offline'])

    # 获取最近的巡检记录
    recent_logs = get_history(limit=5)
    last_scan = recent_logs[0]['timestamp'] if recent_logs else '-'

    return jsonify({
        "status": "success",
        "data": {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": offline_devices,
            "last_scan": last_scan
        }
    })

if __name__ == '__main__':
    # 启动应用前，先初始化数据库 (建表)
    init_db()

    # 启动Flask应用
    app.run(host='0.0.0.0', port=5001, debug=True)