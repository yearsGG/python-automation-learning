# main.py
from my_visual_telnet import VisualTelnet 

all_devices = [
    {
        'host': '192.168.85.254',
        'username': 'admin',
        'password': 'Huawei@123',
    },
    {
        'host': '192.168.85.253',
        'username': 'admin',
        'password': 'Huawei@123',
    }
]

def process_single_device(device_info):
    HOST = device_info['host']
    USER = device_info['username']
    PASSWORD = device_info['password']
    USER_PROMPT = b'>'
    SYSTEM_PROMPT = b']'
    print(f"===== 正在处理设备: {HOST} =====")
    tn = None
    try:
        tn = VisualTelnet(HOST)
        tn.read_until(b"Username:")
        tn.write(USER.encode())
        tn.read_until(b"Password:")
        tn.write(PASSWORD.encode())
        tn.read_until(USER_PROMPT)
        # tn.write(b"system-view\n")
        tn.write(b"system-view")
        tn.read_until(SYSTEM_PROMPT)
        
        print("--- 接口IP信息 ---")
        output_brief = tn.execute(b"display ip interface brief")
        print(output_brief)
        
        print("\n--- 版本信息 ---")
        output_version = tn.execute(b"display version")
        print(output_version)
        
        print(f"===== 设备 {HOST} 处理完成! =====")

    except Exception as e:
        print(f"处理设备 {HOST} 时发生错误: {e}")
        
    finally:
        if tn:
            tn.close()
            print(f"连接 {HOST} 已关闭。\n")

if __name__ == "__main__":
    for device in all_devices:
        process_single_device(device)
    
    print("所有设备处理完毕！")