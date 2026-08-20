# 项目协作与测试管理 MVP

这是一个本地可运行的项目管理工具雏形，当前聚焦三类主要功能：

- 需求管理
- 测试计划管理
- 测试用例管理
- 用户管理
- 角色管理

## 启动

```bash
python3 backend/app.py
```

打开：

```text
http://127.0.0.1:8765
```

## 当前技术栈

- 后端：Python 标准库 `http.server`、`sqlite3`
- 数据库：SQLite，本地文件 `backend/project_management.db`
- 前端：原生 HTML/CSS/JavaScript

这个版本用于快速验证业务流程。功能稳定后，可以迁移为：

- FastAPI
- PostgreSQL
- SQLAlchemy / Alembic
- Redis / 后台任务队列
