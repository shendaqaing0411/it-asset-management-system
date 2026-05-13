# 数据库模块：SQLite 连接管理、建表、初始种子数据
# 数据库文件存储在 backend/data/it_assets.db
# 使用 WAL 模式提升并发读写性能，开启外键约束

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "it_assets.db")


def get_db():
    """获取数据库连接，自动创建目录并配置连接参数"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")     # WAL 模式：读写不互斥
    conn.execute("PRAGMA foreign_keys=ON")       # 启用外键约束
    return conn


def init_db():
    """初始化数据库：建表 + 种子数据（仅首次运行）"""
    conn = get_db()
    cursor = conn.cursor()
    # 共 9 张业务表
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            real_name VARCHAR(50),
            role VARCHAR(20) DEFAULT 'user',
            status VARCHAR(20) DEFAULT 'active',
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            parent_id INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            parent_id INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(100),
            manager_id INTEGER,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            contact VARCHAR(50),
            phone VARCHAR(20),
            address VARCHAR(200),
            remark VARCHAR(500),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_no VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            category_id INTEGER NOT NULL,
            brand VARCHAR(50),
            model VARCHAR(100),
            serial_no VARCHAR(100),
            purchase_price DECIMAL(12,2) DEFAULT 0,
            purchase_date DATE,
            status VARCHAR(20) DEFAULT 'in_stock',
            dept_id INTEGER,
            user_id INTEGER,
            warehouse_id INTEGER,
            location VARCHAR(100),
            supplier_id INTEGER,
            warranty_date DATE,
            remark VARCHAR(500),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS stock_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            type VARCHAR(20) NOT NULL,
            quantity INTEGER DEFAULT 1,
            from_warehouse_id INTEGER,
            to_warehouse_id INTEGER,
            from_dept_id INTEGER,
            to_dept_id INTEGER,
            from_user_id INTEGER,
            to_user_id INTEGER,
            operator_id INTEGER,
            operate_date DATE,
            remark VARCHAR(500),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            fault_desc VARCHAR(500),
            repair_type VARCHAR(20),
            repair_cost DECIMAL(10,2) DEFAULT 0,
            repair_date DATE,
            finish_date DATE,
            status VARCHAR(20) DEFAULT 'pending',
            operator_id INTEGER,
            remark VARCHAR(500),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS stock_warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            min_stock INTEGER DEFAULT 5,
            max_stock INTEGER DEFAULT 100,
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            description VARCHAR(500),
            create_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    _seed_data(conn)
    conn.close()


def _seed_data(conn):
    import bcrypt
    cursor = conn.cursor()
    # 检查是否已有管理员
    row = cursor.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not row:
        pwd = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (username, password, real_name, role) VALUES (?, ?, ?, ?)",
            ("admin", pwd, "管理员", "admin")
        )
        # 默认分类
        for name in ["办公设备", "网络设备", "配件耗材", "软件授权"]:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        # 默认部门
        for name in ["技术部", "财务部", "行政部", "市场部"]:
            cursor.execute("INSERT INTO departments (name) VALUES (?)", (name,))
        # 默认仓库
        cursor.execute("INSERT INTO warehouses (name, location) VALUES (?, ?)", ("主仓库", "A栋1层"))
        conn.commit()
