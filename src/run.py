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

@app.route('/api/ping/direct/<int:device_id>', methods=['POST'])
def ping_direct(device_id):
    """直接从服务器ping目标设备"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    try:
        data = request.get_json() or {}
        target_ip = data.get('target_ip', device['host'])  # 如果没有指定目标IP，则ping设备本身
        count = data.get('count', 5)
        timeout = data.get('timeout', 5)

        import subprocess
        result = subprocess.run(['ping', '-c', str(count), '-W', str(timeout), target_ip],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        is_reachable = result.returncode == 0

        # 解析ping结果
        ping_stats = {"target_ip": target_ip, "reachable": is_reachable}

        if is_reachable:
            # 解析输出获取详细统计信息
            output = result.stdout
            lines = output.split('\n')
            for line in lines:
                if "packets transmitted" in line:
                    # Example: "2 packets transmitted, 2 received, 0% packet loss"
                    import re
                    match = re.search(r'(\d+) packets transmitted, (\d+) received, ([\d.]+)% packet loss', line)
                    if match:
                        ping_stats.update({
                            "packets_transmitted": int(match.group(1)),
                            "packets_received": int(match.group(2)),
                            "packet_loss": float(match.group(3))
                        })
                elif "rtt" in line:
                    # Example: "rtt min/avg/max/mdev = 1.123/1.456/1.789/0.123 ms"
                    import re
                    match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/', line)
                    if match:
                        ping_stats.update({
                            "rtt_min": float(match.group(1)),
                            "rtt_avg": float(match.group(2)),
                            "rtt_max": float(match.group(3))
                        })

        return jsonify({
            "status": "success",
            "data": ping_stats
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": {"target_ip": target_ip, "reachable": False}
        })

@app.route('/api/ping/via-ssh/<int:device_id>', methods=['POST'])
def ping_via_ssh(device_id):
    """通过SSH连接在设备上执行ping测试"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    try:
        data = request.get_json() or {}
        target_ip = data.get('target_ip')
        if not target_ip:
            return jsonify({"status": "error", "message": "Target IP is required"}), 400

        count = data.get('count', 5)
        timeout = data.get('timeout', 5)
        size = data.get('size', None)

        with NetworkDevice(**{k: v for k, v in device.items() if k in ['host', 'username', 'password', 'port', 'device_type']}) as dev:
            # 执行ping测试
            ping_result = dev.ping_test(target_ip, count=count, timeout=timeout, size=size)

            # 检查是否出错
            if isinstance(ping_result, dict) and "error" in ping_result:
                return jsonify({
                    "status": "error",
                    "message": ping_result["error"],
                    "data": {"target_ip": target_ip, "reachable": False}
                })

            # 如果ping_result是空列表，说明没有解析到数据，但命令可能执行了
            if not ping_result and isinstance(ping_result, list):
                # 尝试返回原始输出
                return jsonify({
                    "status": "partial_success",
                    "message": "Ping executed but no structured data parsed",
                    "data": {"target_ip": target_ip, "reachable": False}
                })

            return jsonify({
                "status": "success",
                "data": {
                    "target_ip": target_ip,
                    "results": ping_result
                }
            })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": {"target_ip": target_ip, "reachable": False}
        })

@app.route('/api/ping/batch', methods=['POST'])
def ping_batch():
    """批量ping测试"""
    try:
        data = request.get_json() or {}
        targets = data.get('targets', [])
        ping_method = data.get('method', 'direct')  # 'direct' or 'ssh'
        device_id = data.get('device_id', None)  # Required for SSH method

        if ping_method == 'ssh' and not device_id:
            return jsonify({"status": "error", "message": "Device ID is required for SSH ping method"}), 400

        results = []

        for target in targets:
            target_ip = target if isinstance(target, str) else target.get('ip', '')
            target_name = target.get('name', target_ip) if isinstance(target, dict) else target_ip

            if not target_ip:
                results.append({
                    'target': target_name,
                    'target_ip': target_ip,
                    'reachable': False,
                    'error': 'Invalid target IP'
                })
                continue

            if ping_method == 'direct':
                # Direct ping from server
                import subprocess
                try:
                    result = subprocess.run(['ping', '-c', '3', '-W', '5', target_ip],
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                    is_reachable = result.returncode == 0
                    results.append({
                        'target': target_name,
                        'target_ip': target_ip,
                        'reachable': is_reachable
                    })
                except Exception as e:
                    results.append({
                        'target': target_name,
                        'target_ip': target_ip,
                        'reachable': False,
                        'error': str(e)
                    })
            elif ping_method == 'ssh' and device_id:
                # SSH ping through device
                device = get_device_by_id(device_id)
                if not device:
                    results.append({
                        'target': target_name,
                        'target_ip': target_ip,
                        'reachable': False,
                        'error': 'Device not found'
                    })
                    continue

                try:
                    with NetworkDevice(**{k: v for k, v in device.items() if k in ['host', 'username', 'password', 'port', 'device_type']}) as dev:
                        ping_result = dev.ping_test(target_ip, count=3, timeout=5)

                        if isinstance(ping_result, dict) and "error" in ping_result:
                            results.append({
                                'target': target_name,
                                'target_ip': target_ip,
                                'reachable': False,
                                'error': ping_result.get('error', 'SSH ping failed')
                            })
                        else:
                            is_reachable = len(ping_result) > 0 and float(ping_result[0].get('packet_loss', 100)) < 100  # Assume less than 100% loss means reachable
                            results.append({
                                'target': target_name,
                                'target_ip': target_ip,
                                'reachable': is_reachable,
                                'rtt_min': ping_result[0].get('rtt_min') if ping_result else None,
                                'rtt_avg': ping_result[0].get('rtt_avg') if ping_result else None,
                                'rtt_max': ping_result[0].get('rtt_max') if ping_result else None
                            })
                except Exception as e:
                    results.append({
                        'target': target_name,
                        'target_ip': target_ip,
                        'reachable': False,
                        'error': str(e)
                    })

        return jsonify({
            "status": "success",
            "data": results
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": []
        })


# 模板映射，将命令映射到对应的TextFSM模板（针对EVE-NG环境优化）
COMMAND_TEMPLATE_MAPPING = {
    "display ip interface brief": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_ip_interface_brief.textfsm",
    "display version": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_version.textfsm",
    "display device": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_device.textfsm",
    "display interface": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_interface.textfsm",
    "display interface brief": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_interface_brief.textfsm",
    "display interface description": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_interface_description.textfsm",
    "display vlan": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_vlan.textfsm",
    "display vlan brief": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_vlan_brief.textfsm",
    "display arp": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_arp_all.textfsm",
    "display arp brief": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_arp_brief.textfsm",
    "display mac-address": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_mac-address.textfsm",
    "display lldp neighbor": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_lldp_neighbor.textfsm",
    "display stp brief": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_stp_brief.textfsm",
    "display users": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_users.textfsm",
    "display clock": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_clock.textfsm",
    "display memory": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_memory.textfsm",
    "display cpu-usage": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_cpu-usage.textfsm",
    "display ip routing-table": "/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_display_ip_routing-table.textfsm"
}


@app.route('/api/commands', methods=['GET'])
def get_available_commands():
    """获取系统支持的命令列表"""
    commands = list(COMMAND_TEMPLATE_MAPPING.keys())
    return jsonify({
        "status": "success",
        "data": {
            "commands": commands,
            "total": len(commands)
        }
    })


@app.route('/api/execute-command/<int:device_id>', methods=['POST'])
def execute_device_command(device_id):
    """在设备上执行指定命令并返回解析结果"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    try:
        data = request.get_json() or {}
        command = data.get('command', '').strip()

        if not command:
            return jsonify({"status": "error", "message": "Command is required"}), 400

        # 检查是否有对应的模板（精确匹配优先，然后是包含匹配）
        template_path = None

        # 首先尝试精确匹配
        if command.lower() in COMMAND_TEMPLATE_MAPPING:
            template_path = COMMAND_TEMPLATE_MAPPING[command.lower()]
        else:
            # 如果没有精确匹配，尝试包含匹配（按长度倒序排列，优先匹配更长的命令）
            sorted_patterns = sorted(COMMAND_TEMPLATE_MAPPING.keys(), key=len, reverse=True)
            for cmd_pattern in sorted_patterns:
                if cmd_pattern in command.lower():
                    template_path = COMMAND_TEMPLATE_MAPPING[cmd_pattern]
                    break

        if not template_path:
            return jsonify({
                "status": "error",
                "message": f"No template found for command: {command}",
                "supported_commands": list(COMMAND_TEMPLATE_MAPPING.keys())
            }), 400

        with NetworkDevice(**{k: v for k, v in device.items() if k in ['host', 'username', 'password', 'port', 'device_type']}) as dev:
            try:
                # 进入系统视图
                dev.enter_system_view()

                # 执行命令
                raw_output = dev.execute_command(command)

                # 检查原始输出中是否包含错误信息
                if "Error:" in raw_output or "error:" in raw_output or "Invalid input" in raw_output or "Unrecognized command" in raw_output:
                    # 命令执行失败，记录错误日志
                    save_log(device['host'], command, raw_output, status="error")
                    return jsonify({
                        "status": "error",
                        "message": f"Command execution failed: {raw_output}",
                        "raw_output": raw_output
                    })

                # 使用对应的TextFSM模板解析结果
                if not os.path.exists(template_path):
                    return jsonify({
                        "status": "error",
                        "message": f"Template not found: {template_path}"
                    }), 500

                try:
                    import textfsm
                    with open(template_path, 'r', encoding='utf-8') as f:
                        re_table = textfsm.TextFSM(f)
                        result = re_table.ParseText(raw_output)
                        headers = re_table.header

                        # 强制转小写 (方便前端调用)
                        headers_lower = [h.lower() for h in headers]

                        # 组合成字典
                        parsed_data = [dict(zip(headers_lower, row)) for row in result]

                    # 记录成功日志
                    save_log(device['host'], command, parsed_data, status="success")

                    return jsonify({
                        "status": "success",
                        "data": {
                            "command": command,
                            "parsed_result": parsed_data,
                            "raw_output": raw_output,
                            "template_used": os.path.basename(template_path)
                        }
                    })

                except Exception as e:
                    # 解析失败，但仍返回原始输出，标记为部分成功
                    save_log(device['host'], command, str(e), status="warning")
                    return jsonify({
                        "status": "partial_success",
                        "message": f"Command executed but TextFSM parsing failed: {str(e)}",
                        "raw_output": raw_output,
                        "parsed_result": None,  # No structured data
                        "template_used": os.path.basename(template_path)
                    })

            except Exception as e:
                # 连接或执行失败，记录错误日志
                save_log(device['host'], command, str(e), status="exception")
                return jsonify({
                    "status": "error",
                    "message": f"Command execution failed: {str(e)}"
                })

    except Exception as e:
        # 执行命令失败，记录错误日志
        save_log(device['host'], command, str(e), status="exception")
        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route('/api/batch-commands/<int:device_id>', methods=['POST'])
def execute_batch_commands(device_id):
    """批量执行命令"""
    device = get_device_by_id(device_id)
    if not device:
        return jsonify({"status": "error", "message": "Device not found"}), 404

    try:
        data = request.get_json() or {}
        commands = data.get('commands', [])

        if not commands:
            return jsonify({"status": "error", "message": "Commands list is required"}), 400

        results = []

        with NetworkDevice(**{k: v for k, v in device.items() if k in ['host', 'username', 'password', 'port', 'device_type']}) as dev:
            # 进入系统视图
            dev.enter_system_view()

            for command in commands:
                command = command.strip()
                if not command:
                    continue

                # 检查是否有对应的模板（精确匹配优先，然后是包含匹配）
                template_path = None

                # 首先尝试精确匹配
                if command.lower() in COMMAND_TEMPLATE_MAPPING:
                    template_path = COMMAND_TEMPLATE_MAPPING[command.lower()]
                else:
                    # 如果没有精确匹配，尝试包含匹配（按长度倒序排列，优先匹配更长的命令）
                    sorted_patterns = sorted(COMMAND_TEMPLATE_MAPPING.keys(), key=len, reverse=True)
                    for cmd_pattern in sorted_patterns:
                        if cmd_pattern in command.lower():
                            template_path = COMMAND_TEMPLATE_MAPPING[cmd_pattern]
                            break

                command_result = {
                    "command": command,
                    "status": "success",
                    "parsed_result": [],
                    "raw_output": "",
                    "error": None
                }

                try:
                    # 执行命令
                    raw_output = dev.execute_command(command)
                    command_result["raw_output"] = raw_output

                    # 检查原始输出中是否包含错误信息
                    if "Error:" in raw_output or "error:" in raw_output or "Invalid input" in raw_output or "Unrecognized command" in raw_output:
                        command_result["status"] = "error"
                        command_result["error"] = f"Command execution failed: {raw_output}"
                        results.append(command_result)
                        continue

                    # 如果有对应模板，则尝试解析
                    if template_path and os.path.exists(template_path):
                        import textfsm
                        with open(template_path, 'r', encoding='utf-8') as f:
                            re_table = textfsm.TextFSM(f)
                            result = re_table.ParseText(raw_output)
                            headers = re_table.header

                            # 强制转小写 (方便前端调用)
                            headers_lower = [h.lower() for h in headers]

                            # 组合成字典
                            parsed_data = [dict(zip(headers_lower, row)) for row in result]

                        command_result["parsed_result"] = parsed_data
                        command_result["template_used"] = os.path.basename(template_path)
                    else:
                        # 没有对应模板，只返回原始输出
                        command_result["parsed_result"] = None
                        command_result["message"] = "No template available for this command, returning raw output"

                    results.append(command_result)

                except Exception as e:
                    command_result["status"] = "error"
                    command_result["error"] = str(e)
                    results.append(command_result)

        return jsonify({
            "status": "success",
            "data": {
                "device_id": device_id,
                "results": results
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

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
    app.run(host='0.0.0.0', port=5002, debug=True)