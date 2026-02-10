import sqlite3
import json
import os
from datetime import datetime

# 数据库文件路径 (会自动生成在 src/app/netops.db)
# 获取当前文件 (database.py) 的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'netops.db')

def init_db():
    """初始化数据库：如果表不存在，就创建它"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 创建巡检日志表
    # 字段说明:
    # id: 唯一编号
    # device_ip: 设备IP
    # command: 执行的命令
    # result_json: 结果数据 (存为文本)
    # status: 状态 (success/error)
    # timestamp: 时间 (自动生成)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_ip TEXT NOT NULL,
            command TEXT NOT NULL,
            result_json TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ [DB] 数据库已就绪: {DB_PATH}")

def save_log(device_ip, command, result, status="success"):
    """保存巡检结果到数据库"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 把列表/字典转换成 JSON 字符串存储
        # 数据库不能直接存列表，必须转成字符串
        if isinstance(result, (dict, list)):
            result_str = json.dumps(result, ensure_ascii=False)
        else:
            result_str = str(result)
        
        cursor.execute('''
            INSERT INTO inspection_logs (device_ip, command, result_json, status)
            VALUES (?, ?, ?, ?)
        ''', (device_ip, command, result_str, status))
        
        conn.commit()
        conn.close()
        print(f"💾 [DB] 已保存 {device_ip} 的巡检记录 (Status: {status})")
    except Exception as e:
        print(f"❌ [DB] 保存失败: {e}")

def get_history(limit=20):
    """获取最近的巡检记录 (给前端历史页面用)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row # 让结果可以用字段名访问 (row['id'])
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM inspection_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # 转成字典列表返回
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ [DB] 查询失败: {e}")
        return []