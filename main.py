from my_visual_ssh import VisualSSH

# --- 设备连接信息 ---
# 注意：这里我们直连最终的设备，而不是跳板机
HOST = '192.168.85.253' 
USER = 'netconftest'     
PASSWORD = 'huaweiDC' 

# --- 设备提示符信息 ---
# 华为设备登录后是尖括号 >
USER_PROMPT = b'>'
# 进入system-view后是方括号 ]
SYSTEM_PROMPT = b']'

ssh = None
try:
    ssh = VisualSSH(HOST, username=USER, password=PASSWORD)
    ssh.read_until(USER_PROMPT)
    # 可以开始使用命令了，比如进入系统视图
    ssh.write(b"system-view")
    
    #  等待系统模式的提示符，并更新记忆
    ssh.read_until(SYSTEM_PROMPT)

    #  自动使用记忆中的']'作为结束符
    output1 = ssh.execute(b"display ip interface brief")
    print(output1)
    
    output2 = ssh.execute(b"display version")
    print(output2)

finally:
    # 确保无论成功还是失败，连接都会被关闭
    if ssh:
        ssh.close()