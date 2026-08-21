#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
DB_PATH = Path(__file__).resolve().parent / "project_management.db"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8765"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row else None


def rows_to_list(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


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
                priority TEXT NOT NULL DEFAULT 'P2',
                status TEXT NOT NULL DEFAULT '待评审',
                due_date TEXT NOT NULL DEFAULT '',
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

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT '测试工程师',
                department TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '启用',
                last_login TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS roles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '启用',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        existing = conn.execute("SELECT COUNT(*) AS count FROM requirements").fetchone()["count"]
        if existing == 0:
            seed_data(conn)

        existing_roles = conn.execute("SELECT COUNT(*) AS count FROM roles").fetchone()["count"]
        if existing_roles == 0:
            seed_roles(conn)

        existing_users = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        if existing_users == 0:
            seed_users(conn)
        normalize_user_roles(conn)


def seed_data(conn: sqlite3.Connection) -> None:
    created = now_iso()
    req_id = new_id("REQ")
    plan_id = new_id("TP")
    case_id = new_id("TC")
    conn.execute(
        """
        INSERT INTO requirements
        (id, title, description, owner, priority, status, due_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            req_id,
            "支持项目成员创建和跟踪测试任务",
            "团队需要围绕需求创建测试计划，并把测试用例挂接到计划中。",
            "产品负责人",
            "P1",
            "进行中",
            "2026-09-15",
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
            (id, name, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (new_id("ROLE"), name, description, status, created, created),
        )


class AppHandler(BaseHTTPRequestHandler):
    server_version = "ProjectMvp/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.handle_api_get(parsed.path, parse_qs(parsed.query))
            return
        self.serve_static(parsed.path)

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            self.send_response(405)
            self.end_headers()
            return
        self.serve_static(parsed.path, include_body=False)

    def do_POST(self) -> None:
        self.handle_mutation("POST")

    def do_PUT(self) -> None:
        self.handle_mutation("PUT")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 3 and parts[0] == "api":
            table = self.table_for(parts[1])
            if not table:
                self.send_error_json(404, "Unknown resource")
                return
            with connect() as conn:
                existing = conn.execute(f"SELECT id FROM {table} WHERE id = ?", (parts[2],)).fetchone()
                if not existing:
                    self.send_error_json(404, "Record not found")
                    return
                if table == "roles":
                    role = conn.execute("SELECT name FROM roles WHERE id = ?", (parts[2],)).fetchone()
                    assigned = conn.execute("SELECT COUNT(*) AS count FROM users WHERE role = ?", (role["name"],)).fetchone()
                    if assigned["count"] > 0:
                        self.send_error_json(409, "Role is assigned to users")
                        return
                conn.execute(f"DELETE FROM {table} WHERE id = ?", (parts[2],))
            self.send_json({"ok": True})
            return
        self.send_error_json(404, "Not found")

    def log_message(self, format: str, *args) -> None:
        print("[%s] %s" % (datetime.now().strftime("%H:%M:%S"), format % args))

    def serve_static(self, path: str, include_body: bool = True) -> None:
        target = "index.html" if path in ("", "/") else path.lstrip("/")
        file_path = (FRONTEND_DIR / target).resolve()
        if not str(file_path).startswith(str(FRONTEND_DIR.resolve())) or not file_path.exists():
            self.send_error(404)
            return

        content_type = "text/plain; charset=utf-8"
        if file_path.suffix == ".html":
            content_type = "text/html; charset=utf-8"
        elif file_path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        elif file_path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"

        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def handle_api_get(self, path: str, query: dict[str, list[str]]) -> None:
        if path == "/api/summary":
            self.send_json(self.summary())
            return

        collection = path.removeprefix("/api/")
        table = self.table_for(collection)
        if not table:
            self.send_error_json(404, "Unknown resource")
            return

        search = query.get("q", [""])[0].strip()
        with connect() as conn:
            if table == "requirements":
                sql = "SELECT * FROM requirements"
                params: list[str] = []
                if search:
                    sql += " WHERE title LIKE ? OR owner LIKE ? OR status LIKE ?"
                    params = [f"%{search}%"] * 3
                sql += " ORDER BY updated_at DESC"
                rows = conn.execute(sql, params).fetchall()
            elif table == "test_plans":
                rows = conn.execute(
                    """
                    SELECT p.*, r.title AS requirement_title
                    FROM test_plans p
                    LEFT JOIN requirements r ON r.id = p.requirement_id
                    WHERE (? = '' OR p.name LIKE ? OR p.owner LIKE ? OR p.status LIKE ?)
                    ORDER BY p.updated_at DESC
                    """,
                    (search, f"%{search}%", f"%{search}%", f"%{search}%"),
                ).fetchall()
            elif table == "test_cases":
                rows = conn.execute(
                    """
                    SELECT c.*, r.title AS requirement_title, p.name AS plan_name
                    FROM test_cases c
                    LEFT JOIN requirements r ON r.id = c.requirement_id
                    LEFT JOIN test_plans p ON p.id = c.plan_id
                    WHERE (? = '' OR c.title LIKE ? OR c.module LIKE ? OR c.assignee LIKE ? OR c.status LIKE ?)
                    ORDER BY c.updated_at DESC
                    """,
                    (search, f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"),
                ).fetchall()
            elif table == "users":
                rows = conn.execute(
                    """
                    SELECT *
                    FROM users
                    WHERE (? = '' OR name LIKE ? OR email LIKE ? OR role LIKE ? OR department LIKE ? OR status LIKE ?)
                    ORDER BY updated_at DESC
                    """,
                    (search, f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT r.*, COUNT(u.id) AS user_count
                    FROM roles r
                    LEFT JOIN users u ON u.role = r.name
                    WHERE (? = '' OR r.name LIKE ? OR r.description LIKE ? OR r.status LIKE ?)
                    GROUP BY r.id
                    ORDER BY r.updated_at DESC
                    """,
                    (search, f"%{search}%", f"%{search}%", f"%{search}%"),
                ).fetchall()
        self.send_json(rows_to_list(rows))

    def handle_mutation(self, method: str) -> None:
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) not in (2, 3) or parts[0] != "api":
            self.send_error_json(404, "Not found")
            return

        collection = parts[1]
        table = self.table_for(collection)
        if not table:
            self.send_error_json(404, "Unknown resource")
            return

        data = self.read_json()
        if data is None:
            return

        if method == "POST" and len(parts) == 2:
            self.create_record(table, data)
            return

        if method == "PUT" and len(parts) == 3:
            self.update_record(table, parts[2], data)
            return

        self.send_error_json(405, "Method not allowed")

    def create_record(self, table: str, data: dict) -> None:
        record = self.normalize_record(table, data, record_id=None)
        columns = list(record.keys())
        placeholders = ", ".join(["?"] * len(columns))
        with connect() as conn:
            try:
                conn.execute(
                    f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                    [record[column] for column in columns],
                )
            except sqlite3.IntegrityError:
                self.send_error_json(409, "Record conflicts with existing data")
                return
            saved = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record["id"],)).fetchone()
        self.send_json(row_to_dict(saved), status=201)

    def update_record(self, table: str, record_id: str, data: dict) -> None:
        with connect() as conn:
            existing = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
            if not existing:
                self.send_error_json(404, "Record not found")
                return
            data["created_at"] = existing["created_at"]
            record = self.normalize_record(table, data, record_id=record_id)
            assignments = ", ".join([f"{column} = ?" for column in record.keys() if column != "id"])
            values = [value for column, value in record.items() if column != "id"]
            values.append(record_id)
            try:
                conn.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", values)
            except sqlite3.IntegrityError:
                self.send_error_json(409, "Record conflicts with existing data")
                return
            saved = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
        self.send_json(row_to_dict(saved))

    def normalize_record(self, table: str, data: dict, record_id: str | None) -> dict:
        timestamp = now_iso()
        if table == "requirements":
            return {
                "id": record_id or new_id("REQ"),
                "title": clean(data.get("title")),
                "description": clean(data.get("description")),
                "owner": clean(data.get("owner")),
                "priority": clean(data.get("priority")) or "P2",
                "status": clean(data.get("status")) or "待评审",
                "due_date": clean(data.get("due_date")),
                "created_at": clean(data.get("created_at")) or timestamp,
                "updated_at": timestamp,
            }
        if table == "test_plans":
            return {
                "id": record_id or new_id("TP"),
                "name": clean(data.get("name")),
                "requirement_id": optional_id(data.get("requirement_id")),
                "owner": clean(data.get("owner")),
                "environment": clean(data.get("environment")) or "测试环境",
                "start_date": clean(data.get("start_date")),
                "end_date": clean(data.get("end_date")),
                "status": clean(data.get("status")) or "未开始",
                "goal": clean(data.get("goal")),
                "created_at": clean(data.get("created_at")) or timestamp,
                "updated_at": timestamp,
            }
        if table == "users":
            return {
                "id": record_id or new_id("USR"),
                "name": clean(data.get("name")),
                "email": clean(data.get("email")),
                "role": clean(data.get("role")) or "测试工程师",
                "department": clean(data.get("department")),
                "phone": clean(data.get("phone")),
                "status": clean(data.get("status")) or "启用",
                "last_login": clean(data.get("last_login")),
                "created_at": clean(data.get("created_at")) or timestamp,
                "updated_at": timestamp,
            }
        if table == "roles":
            return {
                "id": record_id or new_id("ROLE"),
                "name": clean(data.get("name")),
                "description": clean(data.get("description")),
                "status": clean(data.get("status")) or "启用",
                "created_at": clean(data.get("created_at")) or timestamp,
                "updated_at": timestamp,
            }
        return {
            "id": record_id or new_id("TC"),
            "title": clean(data.get("title")),
            "requirement_id": optional_id(data.get("requirement_id")),
            "plan_id": optional_id(data.get("plan_id")),
            "module": clean(data.get("module")),
            "priority": clean(data.get("priority")) or "P2",
            "type": clean(data.get("type")) or "功能",
            "status": clean(data.get("status")) or "草稿",
            "precondition": clean(data.get("precondition")),
            "steps": clean(data.get("steps")),
            "expected_result": clean(data.get("expected_result")),
            "assignee": clean(data.get("assignee")),
            "created_at": clean(data.get("created_at")) or timestamp,
            "updated_at": timestamp,
        }

    def summary(self) -> dict:
        with connect() as conn:
            req_count = conn.execute("SELECT COUNT(*) AS count FROM requirements").fetchone()["count"]
            plan_count = conn.execute("SELECT COUNT(*) AS count FROM test_plans").fetchone()["count"]
            case_count = conn.execute("SELECT COUNT(*) AS count FROM test_cases").fetchone()["count"]
            user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
            active_users = conn.execute("SELECT COUNT(*) AS count FROM users WHERE status = '启用'").fetchone()["count"]
            role_count = conn.execute("SELECT COUNT(*) AS count FROM roles").fetchone()["count"]
            active_roles = conn.execute("SELECT COUNT(*) AS count FROM roles WHERE status = '启用'").fetchone()["count"]
            open_req = conn.execute(
                "SELECT COUNT(*) AS count FROM requirements WHERE status NOT IN ('已完成', '已关闭')"
            ).fetchone()["count"]
            running_plans = conn.execute(
                "SELECT COUNT(*) AS count FROM test_plans WHERE status IN ('执行中', '阻塞')"
            ).fetchone()["count"]
            waiting_cases = conn.execute(
                "SELECT COUNT(*) AS count FROM test_cases WHERE status IN ('待执行', '草稿', '阻塞')"
            ).fetchone()["count"]
        return {
            "requirements": req_count,
            "test_plans": plan_count,
            "test_cases": case_count,
            "users": user_count,
            "active_users": active_users,
            "roles": role_count,
            "active_roles": active_roles,
            "open_requirements": open_req,
            "running_plans": running_plans,
            "waiting_cases": waiting_cases,
        }

    def read_json(self) -> dict | None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = self.rfile.read(length).decode("utf-8")
            data = json.loads(payload or "{}")
        except json.JSONDecodeError:
            self.send_error_json(400, "Invalid JSON")
            return None
        if not isinstance(data, dict):
            self.send_error_json(400, "JSON body must be an object")
            return None
        return data

    def send_json(self, data: object, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: int, message: str) -> None:
        self.send_json({"error": message}, status=status)

    @staticmethod
    def table_for(collection: str) -> str | None:
        return {
            "requirements": "requirements",
            "test-plans": "test_plans",
            "test-cases": "test_cases",
            "users": "users",
            "roles": "roles",
        }.get(collection)


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def optional_id(value: object) -> str | None:
    text = clean(value)
    return text or None


def main() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"服务已启动：http://{HOST}:{PORT}")
    print(f"数据库文件：{DB_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
