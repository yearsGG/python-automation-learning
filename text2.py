from my_visual_telnet import VisualTelnet
HOST = '192.168.85.254'
USER = 'admin'
PASSWORD = 'Huawei@123'
USER_PROMPT = b'>'
SYSTEM_PROMPT = b']'

tn = None
try:
    tn = VisualTelnet(HOST)
    tn.read_until(b"Username:")
    tn.write(USER.encode())
    tn.read_until(b"Password:")
    tn.write(PASSWORD.encode())
    tn.read_until(USER_PROMPT)  # <--- 在这里，工具记住了 '>'
    tn.write(b"system-view")
    tn.read_until(SYSTEM_PROMPT) # <--- 在这里，工具的记忆自动更新为 ']'
    print(tn.execute(b"display ip interface brief"))
    print(tn.execute(b"dis ?"))

finally:
    if tn:
        tn.close()