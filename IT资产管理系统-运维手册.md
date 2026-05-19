# IT 资产管理系统 — 运维手册

## 1. 服务器信息

| 项目 | 详情 |
|------|------|
| IP 地址 | `172.16.11.99` |
| 系统版本 | CentOS 8（EOL，yum 源已迁移至 vault） |
| Python | 3.9.19（源码编译，路径 `/usr/local/bin/python3.9`） |
| 磁盘 | 50GB 总量，已用 6.2GB（13%），阈值告警 90% |
| SELinux | Enforcing |
| 防火墙 | firewalld，端口 8000/tcp 已放行 |
| 系统服务 | cockpit.socket 已禁用 |

### 访问地址

| 地址 | 用途 |
|------|------|
| `http://172.16.11.99:8000` | 前端页面 |
| `http://172.16.11.99:8000/docs` | API 文档（Swagger UI） |

### 系统账号

| 用户名 | 姓名 | 密码 | 角色 |
|--------|------|------|------|
| admin | 管理员 | `admin123456` | 管理员 |
| 郑涵 | 郑涵 | — | 管理员 |
| 洪超 | 洪超 | — | 管理员 |

### 部署路径

```
/opt/it-asset-management/
├── backend/                  # FastAPI 后端
│   ├── main.py               # 入口
│   ├── database.py           # 数据库初始化
│   ├── auth.py               # JWT + bcrypt 认证
│   ├── schemas.py            # Pydantic 数据模型
│   ├── routers/              # API 路由
│   ├── data/
│   │   └── it_assets.db      # SQLite 数据库（单文件）
│   ├── requirements.txt      # Python 依赖
│   └── venv/                 # Python 虚拟环境
├── frontend/                 # Vue 3 前端（源码）
│   └── dist/                 # 构建产物（后端自动托管）
├── backups/                  # 数据库备份（自动管理）
├── logs/                     # 守护与服务日志
│   ├── daemon.log            # 守护脚本日志
│   ├── cron.log              # crontab 调用日志
│   ├── server.log            # 服务运行日志（被 start.sh 覆盖）
│   └── .last_checkpoint      # WAL 检查点时间戳
├── start.sh                  # 启动脚本
├── stop.sh                   # 停止脚本
├── daemon.sh                 # 综合守护脚本
├── deploy.sh                 # 一键部署脚本
├── .server.pid               # 服务进程 PID
└── server.log                # 服务 stdout/stderr
```

---

## 2. 启动 / 停止 / 重启

### 启动服务

```bash
cd /opt/it-asset-management && bash start.sh
```

验证：

```bash
kill -0 $(cat /opt/it-asset-management/.server.pid) && echo "运行中" || echo "已停止"
```

### 停止服务

```bash
cd /opt/it-asset-management && bash stop.sh
```

### 重启服务

```bash
cd /opt/it-asset-management && bash stop.sh && bash start.sh
```

### 查看实时日志

```bash
tail -f /opt/it-asset-management/logs/daemon.log       # 守护日志
tail -f /opt/it-asset-management/server.log            # 服务日志
```

### 检查服务状态（一行命令）

```bash
curl -sf -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123456"}' \
  && echo "服务正常" || echo "服务异常"
```

---

## 3. 自动守护机制

### 工作原理

`daemon.sh` 由 crontab 每分钟触发一次，执行以下流程：

```
crontab 每分钟
  └→ daemon.sh
       ├→ 日志轮转（超过 5000 行自动截断）
       ├→ 磁盘空间检查（>90% 告警）
       ├→ venv 完整性检查（缺失自动修复）
       ├→ 数据库完整性检查（损坏自动从备份恢复）
       ├→ 健康检查（两级）
       │   ├── 一级：端口 8000 是否可达（curl /docs）
       │   └── 二级：登录 API 全链路（DB 读写 + bcrypt + JWT）
       ├── 服务健康 → 执行维护
       │   ├── 数据库每日在线备份
       │   └── WAL 检查点（每 6 小时 TRUNCATE）
       └── 服务不健康 → 自动拉起
           ├── 清理残留 uvicorn 僵尸进程
           ├── 释放被占用端口
           ├── 重新启动服务（15 秒等待）
           └── 启动后立即备份数据
```

### 守护覆盖的故障场景

| 场景 | 检测方式 | 自动恢复 |
|------|----------|----------|
| 进程崩溃 | 端口不可达 | 清理残留 → 重新启动 |
| 端口冲突 | lsof 端口被陌生进程占用 | kill 旧进程 → 恢复端口 |
| DB 损坏 | `PRAGMA integrity_check` | 从最近备份恢复，损坏文件保留 `.corrupted` 后缀 |
| DB 文件丢失 | 文件不存在 | 从最近备份恢复 |
| 磁盘满 | `df -P` > 90% | 告警（需人工清理） |
| venv 损坏 | import 测试失败 | `pip install -r requirements.txt` 修复 |
| WAL 膨胀 | 每 6 小时触发 | `PRAGMA wal_checkpoint(TRUNCATE)` |
| 僵尸 uvicorn | PID 文件记录与进程不一致 | kill + 端口清理 |

### 查看守护状态

```bash
# 查看当前 crontab
crontab -l

# 查看最近守护日志
tail -50 /opt/it-asset-management/logs/daemon.log

# 查看 crontab 调用历史
tail -20 /opt/it-asset-management/logs/cron.log
```

### 手动触发守护检查

```bash
cd /opt/it-asset-management && bash daemon.sh
```

### 停止守护（临时）

```bash
crontab -r   # 清空 crontab（守护停止）
```

### 重新安装守护

如果守护配置丢失，在服务器上执行：

```bash
cd /opt/it-asset-management
# 修复 daemon.sh 密码配置（如需要）
sed -i 's/"admin[0-9]*"/"admin123456"/' daemon.sh
# 配置 crontab
echo "*/1 * * * * /bin/bash /opt/it-asset-management/daemon.sh >> /opt/it-asset-management/logs/cron.log 2>&1" > /tmp/cron_entry
crontab /tmp/cron_entry
# 首次执行
bash daemon.sh
```

---

## 4. 数据备份与恢复

### 自动备份

- daemon.sh 每日自动备份（仅首次检查触发）
- 备份路径：`/opt/it-asset-management/backups/it_assets_YYYYMMDD.db`
- 使用 `sqlite3 .backup` 命令，保证事务一致性
- 保留最近 7 天，超期自动删除

### 手动备份

```bash
# 在线备份（无需停止服务）
sqlite3 /opt/it-asset-management/backend/data/it_assets.db \
  ".backup '/opt/it-asset-management/backups/it_assets_$(date +%Y%m%d).db'"

# 验证备份完整性
sqlite3 /opt/it-asset-management/backups/it_assets_20260516.db "PRAGMA integrity_check;"
```

### 从备份恢复

```bash
# 1. 停止服务
cd /opt/it-asset-management && bash stop.sh

# 2. 保留损坏文件
cp /opt/it-asset-management/backend/data/it_assets.db \
   /opt/it-asset-management/backend/data/it_assets.db.corrupted.$(date +%Y%m%d%H%M%S)

# 3. 从备份恢复
cp /opt/it-asset-management/backups/it_assets_20260516.db \
   /opt/it-asset-management/backend/data/it_assets.db

# 4. 重启服务
bash start.sh

# 5. 验证
curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123456"}'
```

---

## 5. 数据库维护

### SQLite 版本

```bash
sqlite3 --version
```

### 数据库文件信息

```bash
ls -lh /opt/it-asset-management/backend/data/it_assets.db*
```

### 直接操作数据库

```bash
# 进入 SQLite
sqlite3 /opt/it-asset-management/backend/data/it_assets.db

# 查看所有表
.tables

# 统计资产数量
SELECT COUNT(*) FROM assets;

# 查看用户
SELECT username, real_name, role FROM users;

# 退出
.quit
```

### 重置数据库（清除所有业务数据）

```bash
cd /opt/it-asset-management && bash stop.sh
rm -f /opt/it-asset-management/backend/data/it_assets.db
bash start.sh
# 启动时自动初始化空库，保留 admin 账号
```

### 查看 WAL 文件大小

```bash
ls -lh /opt/it-asset-management/backend/data/it_assets.db-wal /opt/it-asset-management/backend/data/it_assets.db-shm 2>/dev/null
```

### 手动 WAL 检查点

```bash
sqlite3 /opt/it-asset-management/backend/data/it_assets.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

---

## 6. 用户与密码管理

### 重置 admin 密码

```bash
cd /opt/it-asset-management/backend && source venv/bin/activate && python3.9 -c "
from auth import hash_password
import sqlite3
conn = sqlite3.connect('data/it_assets.db')
conn.execute('UPDATE users SET password = ? WHERE username = ?', (hash_password('新密码'), 'admin'))
conn.commit()
conn.close()
print('密码已重置')
"
```

### 新增管理员

在系统前端登录 → 系统管理 → 用户管理 → 新增用户。

### 更新 daemon.sh 健康检查密码

如果 admin 密码修改了，必须同步更新 daemon.sh 中的健康检查密码：

```bash
sed -i 's/"admin[a-zA-Z0-9]*"/"新密码"/' /opt/it-asset-management/daemon.sh
# 验证修改
grep 'password' /opt/it-asset-management/daemon.sh
```

---

## 7. 防火墙与网络

### 查看防火墙状态

```bash
firewall-cmd --state
firewall-cmd --list-ports
```

### 放行端口（如需要）

```bash
firewall-cmd --add-port=8000/tcp --permanent
firewall-cmd --reload
```

### SELinux 注意事项

SELinux 当前为 Enforcing 模式，服务在 8000 端口运行正常，无需额外配置。如果遇到端口拒绝问题：

```bash
# 检查 SELinux 审计日志
ausearch -m avc -ts recent | grep 8000

# 临时切换到 Permissive 测试（不推荐长期）
setenforce 0

# 恢复 Enforcing
setenforce 1
```

---

## 8. 故障排查

### 服务无法访问

```bash
# 1. 检查进程
kill -0 $(cat /opt/it-asset-management/.server.pid) && echo "运行中" || echo "已停止"

# 2. 检查端口
ss -tlnp | grep 8000

# 3. 检查防火墙
firewall-cmd --list-ports | grep 8000

# 4. 检查日志
tail -50 /opt/it-asset-management/server.log
tail -50 /opt/it-asset-management/logs/daemon.log

# 5. 手动重启
cd /opt/it-asset-management && bash stop.sh && bash start.sh
```

### 前端页面 404

前端由后端 `/static/` 托管。如果没有 `backend/static/` 目录，需重新构建：

```bash
cd /opt/it-asset-management/frontend
npm install
npm run build
# 产物自动复制到 ../backend/static/
cd /opt/it-asset-management && bash stop.sh && bash start.sh
```

### 数据库锁定

SQLite WAL 模式下极少锁定。如遇到：

```bash
# 查看是否有挂起的写操作
ls -la /opt/it-asset-management/backend/data/it_assets.db-wal

# 强制检查点
sqlite3 /opt/it-asset-management/backend/data/it_assets.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 仍不行则重启服务
cd /opt/it-asset-management && bash stop.sh && bash start.sh
```

### 守护脚本反复重启服务

查看守护日志确认原因：

```bash
grep "服务不健康" /opt/it-asset-management/logs/daemon.log
grep "启动失败" /opt/it-asset-management/logs/daemon.log
```

常见原因：
- admin 密码已修改但 daemon.sh 未同步 → 更新 daemon.sh 中的密码
- venv 依赖缺失 → 手动 `cd /opt/it-asset-management/backend && source venv/bin/activate && pip install -r requirements.txt`
- 端口被非 uvicorn 进程占用 → 手动 `fuser -k 8000/tcp`

### Python 版本问题

服务器 Python 3.9.19 位于 `/usr/local/bin/python3.9`，启动脚本已使用该路径。系统中 `python3` 命令可能不可用，所有脚本均使用 `python3.9`。

---

## 9. 版本更新与部署

### 从 Mac 同步最新代码到服务器

```bash
# 全量同步（排除 .git、venv、node_modules）
rsync -avz ~/it资产管理/ root@172.16.11.99:/opt/it-asset-management/ \
  --exclude '.git' --exclude '__pycache__' --exclude 'venv' \
  --exclude 'node_modules' --exclude '.DS_Store' --exclude '.server.pid' \
  --exclude 'server.log' --exclude 'logs' --exclude 'backups' \
  --exclude 'backend/data/it_assets.db'
```

### 单独更新前端

```bash
# 本地构建
cd ~/it资产管理/frontend && npm run build

# 同步到服务器
rsync -avz ~/it资产管理/frontend/dist/ root@172.16.11.99:/opt/it-asset-management/backend/static/

# 重启服务（前端静态文件无需重启，刷新页面即可）
```

### 单独更新后端

```bash
rsync -avz ~/it资产管理/backend/ root@172.16.11.99:/opt/it-asset-management/backend/ \
  --exclude '__pycache__' --exclude 'venv' --exclude 'data/it_assets.db'

# 重启服务
ssh root@172.16.11.99 'cd /opt/it-asset-management && bash stop.sh && bash start.sh'
```

### 单独更新配置

```bash
# 更新 daemon.sh 或 start.sh 等脚本
scp ~/it资产管理/daemon.sh root@172.16.11.99:/opt/it-asset-management/
```


## 10. 开发环境（Mac）

```bash
# 后端
cd ~/it资产管理/backend
pip install -r requirements.txt
python main.py

# 前端（新终端）
cd ~/it资产管理/frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 项目源码路径

`~/it资产管理/`（此前位于 `~/Desktop/it资产管理`，已移动）

---

## 11. 修改历史

| 日期 | 变更 |
|------|------|
| 2026-05-16 | 配置 crontab 守护、修复 daemon.sh 密码、添加 fix_server.sh |
| 2026-05-14 | 初次部署到 172.16.11.99 |
| 2026-05-13 | 系统初始开发 |
