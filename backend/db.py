from __future__ import annotations

import json
import os
import sqlite3

from auth import hash_password
from config import DB_PATH, DEFAULT_ROLE_PERMISSIONS
from utils import new_id, now_iso


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL DEFAULT '',
                process_type TEXT NOT NULL DEFAULT '标准产品流程',
                business_line TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'P2',
                status TEXT NOT NULL DEFAULT '待评审',
                due_date TEXT NOT NULL DEFAULT '',
                requirement_doc TEXT NOT NULL DEFAULT '',
                need_tech_review TEXT NOT NULL DEFAULT '否',
                participants TEXT NOT NULL DEFAULT '[]',
                launch_country TEXT NOT NULL DEFAULT '',
                followers TEXT NOT NULL DEFAULT '',
                current_step TEXT NOT NULL DEFAULT '需求提出',
                node_owner TEXT NOT NULL DEFAULT '',
                node_score TEXT NOT NULL DEFAULT '',
                node_schedule TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS test_plans (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                requirement_id TEXT,
                owner TEXT NOT NULL DEFAULT '',
                environment TEXT NOT NULL DEFAULT '测试环境',
                start_date TEXT NOT NULL DEFAULT '',
                end_date TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '未开始',
                goal TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(requirement_id) REFERENCES requirements(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS test_cases (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                requirement_id TEXT,
                plan_id TEXT,
                module TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL DEFAULT 'P2',
                type TEXT NOT NULL DEFAULT '功能',
                status TEXT NOT NULL DEFAULT '草稿',
                precondition TEXT NOT NULL DEFAULT '',
                steps TEXT NOT NULL DEFAULT '',
                expected_result TEXT NOT NULL DEFAULT '',
                assignee TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(requirement_id) REFERENCES requirements(id) ON DELETE SET NULL,
                FOREIGN KEY(plan_id) REFERENCES test_plans(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS defects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                requirement_id TEXT,
                severity TEXT NOT NULL DEFAULT 'S2',
                priority TEXT NOT NULL DEFAULT 'P2',
                status TEXT NOT NULL DEFAULT '新建',
                reporter TEXT NOT NULL DEFAULT '',
                assignee TEXT NOT NULL DEFAULT '',
                environment TEXT NOT NULL DEFAULT '',
                steps TEXT NOT NULL DEFAULT '',
                actual_result TEXT NOT NULL DEFAULT '',
                expected_result TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(requirement_id) REFERENCES requirements(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT '测试工程师',
                department TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '启用',
                last_login TEXT NOT NULL DEFAULT '',
                password_salt TEXT,
                password_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                permissions TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT '启用',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS auth_sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        ensure_requirement_columns(conn)
        ensure_user_auth_columns(conn)
        ensure_role_permission_column(conn)

        if conn.execute("SELECT COUNT(*) AS count FROM requirements").fetchone()["count"] == 0:
            seed_data(conn)

        if conn.execute("SELECT COUNT(*) AS count FROM roles").fetchone()["count"] == 0:
            seed_roles(conn)

        if conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"] == 0:
            seed_users(conn)
        normalize_user_roles(conn)
        seed_role_permissions(conn)
        seed_default_admin_password(conn)


def ensure_user_auth_columns(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "password_salt" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN password_salt TEXT")
    if "password_hash" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")


def ensure_requirement_columns(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(requirements)").fetchall()}
    column_defaults = {
        "process_type": "TEXT NOT NULL DEFAULT '标准产品流程'",
        "business_line": "TEXT NOT NULL DEFAULT ''",
        "requirement_doc": "TEXT NOT NULL DEFAULT ''",
        "need_tech_review": "TEXT NOT NULL DEFAULT '否'",
        "participants": "TEXT NOT NULL DEFAULT '[]'",
        "launch_country": "TEXT NOT NULL DEFAULT ''",
        "followers": "TEXT NOT NULL DEFAULT ''",
        "current_step": "TEXT NOT NULL DEFAULT '需求提出'",
        "node_owner": "TEXT NOT NULL DEFAULT ''",
        "node_score": "TEXT NOT NULL DEFAULT ''",
        "node_schedule": "TEXT NOT NULL DEFAULT ''",
    }
    for column, definition in column_defaults.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE requirements ADD COLUMN {column} {definition}")


def ensure_role_permission_column(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(roles)").fetchall()}
    if "permissions" not in columns:
        conn.execute("ALTER TABLE roles ADD COLUMN permissions TEXT NOT NULL DEFAULT '[]'")


def seed_data(conn: sqlite3.Connection) -> None:
    created = now_iso()
    req_id = new_id("REQ")
    plan_id = new_id("TP")
    case_id = new_id("TC")
    conn.execute(
        """
        INSERT INTO requirements
        (id, title, description, owner, process_type, business_line, priority, status, due_date,
         requirement_doc, need_tech_review, participants, launch_country, followers,
         current_step, node_owner, node_score, node_schedule, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            req_id,
            "支持项目成员创建和跟踪测试任务",
            "团队需要围绕需求创建测试计划，并把测试用例挂接到计划中。",
            "产品负责人",
            "标准产品流程",
            "项目管理",
            "P1",
            "进行中",
            "2026-09-15",
            "",
            "否",
            json.dumps([{"role": "产品经理", "user": "产品负责人"}, {"role": "业务方", "user": ""}], ensure_ascii=False),
            "中国",
            "",
            "后端开发",
            "测试负责人",
            "",
            "",
            created,
            created,
        ),
    )
    conn.execute(
        """
        INSERT INTO test_plans
        (id, name, requirement_id, owner, environment, start_date, end_date, status, goal, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plan_id,
            "项目管理 MVP 第一轮系统测试",
            req_id,
            "测试负责人",
            "本地测试环境",
            "2026-08-20",
            "2026-08-30",
            "执行中",
            "验证需求、计划、用例三条核心流程是否闭环。",
            created,
            created,
        ),
    )
    conn.execute(
        """
        INSERT INTO test_cases
        (id, title, requirement_id, plan_id, module, priority, type, status, precondition, steps, expected_result, assignee, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            "创建测试用例并关联需求与测试计划",
            req_id,
            plan_id,
            "测试用例管理",
            "P1",
            "功能",
            "待执行",
            "已存在一个需求和一个测试计划。",
            "1. 打开测试用例管理\n2. 新建用例\n3. 选择关联需求和测试计划\n4. 保存",
            "用例创建成功，并能在列表中看到关联信息。",
            "测试工程师",
            created,
            created,
        ),
    )


def seed_users(conn: sqlite3.Connection) -> None:
    created = now_iso()
    users = [
        ("项目管理员", "admin@example.com", "管理员", "项目管理办公室", "13800000001", "启用", "2026-08-20"),
        ("产品负责人", "po@example.com", "产品经理", "产品部", "13800000002", "启用", "2026-08-19"),
        ("测试负责人", "qa-lead@example.com", "测试", "质量保障部", "13800000003", "启用", "2026-08-18"),
        ("测试工程师", "qa@example.com", "测试", "质量保障部", "13800000004", "停用", ""),
    ]
    for name, email, role, department, phone, status, last_login in users:
        conn.execute(
            """
            INSERT INTO users
            (id, name, email, role, department, phone, status, last_login, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (new_id("USR"), name, email, role, department, phone, status, last_login, created, created),
        )


def normalize_user_roles(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE users SET role = '测试' WHERE role IN ('测试负责人', '测试工程师')")


def seed_default_admin_password(conn: sqlite3.Connection) -> None:
    admin = conn.execute(
        "SELECT id, password_hash FROM users WHERE email = ? LIMIT 1",
        ("admin@example.com",),
    ).fetchone()
    if not admin or admin["password_hash"]:
        return
    salt, password_hash = hash_password(os.environ.get("ADMIN_PASSWORD", "admin123456"))
    conn.execute(
        "UPDATE users SET password_salt = ?, password_hash = ? WHERE id = ?",
        (salt, password_hash, admin["id"]),
    )


def seed_roles(conn: sqlite3.Connection) -> None:
    created = now_iso()
    roles = [
        ("管理员", "拥有系统配置、用户和角色维护权限。", "启用"),
        ("业务方", "提出业务需求，参与需求确认和验收。", "启用"),
        ("产品经理", "维护产品需求、优先级和交付节奏。", "启用"),
        ("开发（web端）", "负责 Web 前端功能开发和联调。", "启用"),
        ("开发（移动端）", "负责移动端功能开发和联调。", "启用"),
        ("开发（后端）", "负责后端服务、接口和数据逻辑开发。", "启用"),
        ("测试", "负责测试计划、测试用例和执行结果跟踪。", "启用"),
    ]
    for name, description, status in roles:
        conn.execute(
            """
            INSERT INTO roles
            (id, name, description, permissions, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id("ROLE"),
                name,
                description,
                json.dumps(DEFAULT_ROLE_PERMISSIONS.get(name, []), ensure_ascii=False),
                status,
                created,
                created,
            ),
        )


def seed_role_permissions(conn: sqlite3.Connection) -> None:
    for name, permissions in DEFAULT_ROLE_PERMISSIONS.items():
        existing = conn.execute("SELECT permissions FROM roles WHERE name = ?", (name,)).fetchone()
        current = []
        if existing:
            try:
                parsed = json.loads(existing["permissions"] or "[]")
                current = parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                current = []
        merged = list(dict.fromkeys([*current, *permissions]))
        conn.execute(
            "UPDATE roles SET permissions = ? WHERE name = ?",
            (json.dumps(merged, ensure_ascii=False), name),
        )
