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

    # 创建设备表（用于存储设备配置）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER DEFAULT 22,
            username TEXT NOT NULL,
            password TEXT,
            device_type TEXT DEFAULT 'huawei_vrp',
            status TEXT DEFAULT 'unknown',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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

def get_logs_by_device(device_ip, limit=20):
    """获取特定设备的巡检记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM inspection_logs
            WHERE device_ip = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (device_ip, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ [DB] 查询失败: {e}")
        return []

def get_logs_by_status(status, limit=20):
    """获取特定状态的巡检记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM inspection_logs
            WHERE status = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (status, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ [DB] 查询失败: {e}")
        return []

def get_logs_by_date_range(start_date, end_date, limit=100):
    """获取指定日期范围内的巡检记录"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM inspection_logs
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (start_date, end_date, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ [DB] 查询失败: {e}")
        return []

def get_statistics():
    """获取巡检统计信息"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 总记录数
        cursor.execute('SELECT COUNT(*) as total FROM inspection_logs')
        total = cursor.fetchone()['total']

        # 按状态统计
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM inspection_logs
            GROUP BY status
        ''')
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

        # 最近记录时间
        cursor.execute('SELECT MAX(timestamp) as last_record FROM inspection_logs')
        last_record = cursor.fetchone()['last_record']

        conn.close()

        return {
            'total_logs': total,
            'status_counts': status_counts,
            'last_record': last_record
        }
    except Exception as e:
        print(f"❌ [DB] 统计查询失败: {e}")
        return {}

def add_device(name, host, port=22, username='', password='', device_type='huawei_vrp'):
    """添加设备到数据库"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO devices (name, host, port, username, password, device_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, host, port, username, password, device_type))

        device_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"💾 [DB] 已添加设备: {name} ({host})")
        return device_id
    except Exception as e:
        print(f"❌ [DB] 添加设备失败: {e}")
        return None

def get_all_devices():
    """获取所有设备"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM devices ORDER BY id')
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ [DB] 查询设备失败: {e}")
        return []

def get_device_by_id(device_id):
    """根据ID获取设备"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None
    except Exception as e:
        print(f"❌ [DB] 查询设备失败: {e}")
        return None

def update_device(device_id, name=None, host=None, port=None, username=None, password=None, device_type=None, status=None):
    """更新设备信息"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 构建更新语句
        updates = []
        params = []

        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if host is not None:
            updates.append('host = ?')
            params.append(host)
        if port is not None:
            updates.append('port = ?')
            params.append(port)
        if username is not None:
            updates.append('username = ?')
            params.append(username)
        if password is not None:
            updates.append('password = ?')
            params.append(password)
        if device_type is not None:
            updates.append('device_type = ?')
            params.append(device_type)
        if status is not None:
            updates.append('status = ?')
            params.append(status)

        # 添加更新时间
        updates.append('updated_at = CURRENT_TIMESTAMP')

        if updates:
            sql = f"UPDATE devices SET {', '.join(updates)} WHERE id = ?"
            params.append(device_id)

            cursor.execute(sql, params)
            conn.commit()

        conn.close()
        print(f"💾 [DB] 已更新设备: {device_id}")
        return True
    except Exception as e:
        print(f"❌ [DB] 更新设备失败: {e}")
        return False

def delete_device(device_id):
    """删除设备"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
        conn.commit()
        conn.close()

        print(f"🗑️ [DB] 已删除设备: {device_id}")
        return True
    except Exception as e:
        print(f"❌ [DB] 删除设备失败: {e}")
        return False