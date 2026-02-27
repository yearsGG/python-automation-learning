#!/usr/bin/env python3
"""
测试EVE-NG环境中可用的华为命令及其解析
"""

import sys
import os
import requests
import json
import time

# 添加项目路径
sys.path.append('/root/github/python-automation-learning/src')
from core.ssh_client import NetworkDevice

def test_command_execution(host, username, password, port=22):
    """测试各种华为命令的执行和TextFSM解析"""

    # 设备连接参数
    device_params = {
        'host': host,
        'username': username,
        'password': password,
        'port': port,
        'device_type': 'huawei_vrp'
    }

    # 要测试的命令列表（针对EVE-NG环境）
    commands_to_test = [
        'display version',
        'display device',
        'display interface',
        'display interface brief',
        'display ip interface brief',
        'display current-configuration',
        'display saved-configuration',
        'display arp',
        'display vlan',
        'display mac-address',
        'display users',
        'display memory',
        'display lldp neighbor',
        'display stp brief',
        'display ip routing-table',
        'display this',
        'display history',
        'display clock',  # 即使可能不可用也测试一下
        'display fan',    # 即使可能不可用也测试一下
        'display power'   # 即使可能不可用也测试一下
    ]

    print("开始测试EVE-NG环境中华为命令的执行...")
    print("=" * 60)

    results = {}

    try:
        with NetworkDevice(**device_params) as dev:
            # 进入系统视图
            dev.enter_system_view()

            for command in commands_to_test:
                print(f"\n正在测试命令: {command}")

                try:
                    # 执行命令
                    raw_output = dev.execute_command(command)

                    # 检查是否有错误
                    if "Error:" in raw_output or "error:" in raw_output or "Invalid input" in raw_output or "Unrecognized command" in raw_output:
                        print(f"  ❌ 命令执行失败: {raw_output.strip()}")
                        results[command] = {
                            'success': False,
                            'error': 'Command execution failed',
                            'raw_output': raw_output
                        }
                        continue

                    print(f"  ✅ 命令执行成功")

                    # 尝试用TextFSM解析（如果有的话）
                    try:
                        # 这里我们简单测试使用TextFSM解析
                        import textfsm
                        # 尝试找到可能的模板路径
                        template_path = f"/root/github/python-automation-learning/venv/lib/python3.10/site-packages/ntc_templates/templates/huawei_vrp_{command.replace(' ', '_')}.textfsm"

                        if os.path.exists(template_path):
                            with open(template_path, 'r', encoding='utf-8') as f:
                                re_table = textfsm.TextFSM(f)
                                result = re_table.ParseText(raw_output)

                                if result:
                                    print(f"  ✅ TextFSM解析成功，解析到 {len(result)} 条记录")
                                    results[command] = {
                                        'success': True,
                                        'parsed_count': len(result),
                                        'raw_output': raw_output,
                                        'template_used': template_path
                                    }
                                else:
                                    print(f"  ⚠️  TextFSM解析成功但未解析到数据")
                                    results[command] = {
                                        'success': True,  # 执行成功，但解析无数据
                                        'parsed_count': 0,
                                        'message': 'Command executed but no data parsed',
                                        'raw_output': raw_output,
                                        'template_used': template_path
                                    }
                        else:
                            print(f"  ℹ️  未找到对应模板: {template_path}")
                            results[command] = {
                                'success': True,  # 执行成功，但无模板
                                'message': 'Command executed but no template available',
                                'raw_output': raw_output
                            }

                    except Exception as e:
                        print(f"  ⚠️  TextFSM解析失败: {str(e)}")
                        results[command] = {
                            'success': True,  # 执行成功，但解析失败
                            'error': f'TextFSM parsing failed: {str(e)}',
                            'raw_output': raw_output
                        }

                except Exception as e:
                    print(f"  ❌ 命令执行异常: {str(e)}")
                    results[command] = {
                        'success': False,
                        'error': str(e),
                        'raw_output': None
                    }

                # 短暂延迟，避免命令执行过快
                time.sleep(1)

    except Exception as e:
        print(f"连接设备失败: {str(e)}")
        return None

    return results

def main():
    # 设备连接参数 - 使用默认值
    host = "192.168.10.1"  # 根据run.py中的默认设备配置
    username = "admin"
    password = "Admin@123"
    port = 22

    print(f"开始测试 {host}:{port} 的可用命令...")
    print("注意: 使用默认设备配置，如需修改请编辑脚本")

    results = test_command_execution(host, username, password, port)

    if results:
        print("\n" + "=" * 60)
        print("测试结果总结:")
        print("=" * 60)

        successful_commands = []
        failed_commands = []

        for command, result in results.items():
            if result['success']:
                successful_commands.append(command)
            else:
                failed_commands.append(command)

        print(f"\n✅ 成功执行的命令 ({len(successful_commands)}):")
        for cmd in successful_commands:
            result = results[cmd]
            if result.get('parsed_count', None) is not None:
                if result['parsed_count'] > 0:
                    print(f"  - {cmd} (解析到 {result['parsed_count']} 条数据)")
                else:
                    print(f"  - {cmd} (执行成功但无结构化数据)")
            else:
                print(f"  - {cmd} (执行成功)")

        print(f"\n❌ 执行失败的命令 ({len(failed_commands)}):")
        for cmd in failed_commands:
            result = results[cmd]
            error_msg = result.get('error', 'Unknown error')
            print(f"  - {cmd}: {error_msg}")

        # 保存详细结果到文件
        with open('/root/github/python-automation-learning/command_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n详细结果已保存到: /root/github/python-automation-learning/command_test_results.json")

        # 生成推荐的命令列表
        recommended_commands = [cmd for cmd, result in results.items() if result['success'] and result.get('parsed_count', 0) > 0]
        print(f"\n📋 推荐用于生产环境的命令列表 ({len(recommended_commands)}):")
        for cmd in recommended_commands:
            print(f"  - {cmd}")

if __name__ == "__main__":
    main()