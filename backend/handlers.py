from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from auth import create_session, hash_password, public_user, verify_password
from config import FRONTEND_DIR
from db import connect
from utils import (
    clean,
    new_id,
    normalize_participants,
    normalize_permissions,
    now_iso,
    optional_id,
    participant_owner,
    row_to_dict,
    rows_to_list,
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
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/auth/"):
            self.handle_auth_post(parsed.path)
            return
        self.handle_mutation("POST")

    def do_PUT(self) -> None:
        self.handle_mutation("PUT")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/auth/logout":
            self.handle_logout()
            return
        if not self.require_auth():
            return
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
        if path == "/api/auth/me":
            user = self.require_auth()
            if user:
                self.send_json({"user": public_user(user)})
            return

        if not self.require_auth():
            return

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
                    sql += """
                    WHERE title LIKE ? OR owner LIKE ? OR status LIKE ? OR process_type LIKE ?
                       OR business_line LIKE ? OR launch_country LIKE ? OR followers LIKE ?
                    """
                    params = [f"%{search}%"] * 7
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
            elif table == "defects":
                rows = conn.execute(
                    """
                    SELECT d.*, r.title AS requirement_title
                    FROM defects d
                    LEFT JOIN requirements r ON r.id = d.requirement_id
                    WHERE (? = '' OR d.title LIKE ? OR d.status LIKE ? OR d.severity LIKE ?
                           OR d.assignee LIKE ? OR d.reporter LIKE ? OR r.title LIKE ?)
                    ORDER BY d.updated_at DESC
                    """,
                    (search, f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"),
                ).fetchall()
            elif table == "users":
                rows = conn.execute(
                    """
                    SELECT u.id, u.name, u.email, u.role, u.phone, u.status, u.last_login,
                           u.created_at, u.updated_at, r.permissions AS role_permissions
                    FROM users u
                    LEFT JOIN roles r ON r.name = u.role
                    WHERE (? = '' OR u.name LIKE ? OR u.email LIKE ? OR u.role LIKE ? OR u.phone LIKE ? OR u.status LIKE ?)
                    ORDER BY u.updated_at DESC
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
        current_user = self.require_auth()
        if not current_user:
            return

        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) not in (2, 3) or parts[0] != "api":
            self.send_error_json(404, "Not found")
            return

        table = self.table_for(parts[1])
        if not table:
            self.send_error_json(404, "Unknown resource")
            return

        data = self.read_json()
        if data is None:
            return

        if method == "POST" and len(parts) == 2:
            self.create_record(table, data, current_user)
            return

        if method == "PUT" and len(parts) == 3:
            self.update_record(table, parts[2], data, current_user)
            return

        self.send_error_json(405, "Method not allowed")

    def handle_auth_post(self, path: str) -> None:
        if path == "/api/auth/register":
            self.register()
            return
        if path == "/api/auth/login":
            self.login()
            return
        self.send_error_json(404, "Not found")

    def register(self) -> None:
        data = self.read_json()
        if data is None:
            return

        name = clean(data.get("name"))
        email = clean(data.get("email")).lower()
        password = str(data.get("password") or "")
        if not name or not email or not password:
            self.send_error_json(400, "Name, email and password are required")
            return
        if len(password) < 6:
            self.send_error_json(400, "Password must be at least 6 characters")
            return

        timestamp = now_iso()
        user_id = new_id("USR")
        salt, password_hash = hash_password(password)
        with connect() as conn:
            existing = conn.execute("SELECT id FROM users WHERE lower(email) = ?", (email,)).fetchone()
            if existing:
                self.send_error_json(409, "Email is already registered")
                return
            conn.execute(
                """
                INSERT INTO users
                (id, name, email, role, department, phone, status, last_login, password_salt, password_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, email, "测试", "", "", "启用", datetime.now().date().isoformat(), salt, password_hash, timestamp, timestamp),
            )
            token = create_session(conn, user_id)
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        self.send_json({"token": token, "user": public_user(user)}, status=201)

    def login(self) -> None:
        data = self.read_json()
        if data is None:
            return

        email = clean(data.get("email")).lower()
        password = str(data.get("password") or "")
        with connect() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE lower(email) = ? AND status = '启用'",
                (email,),
            ).fetchone()
            if not user or not user["password_salt"] or not user["password_hash"]:
                self.send_error_json(401, "Invalid email or password")
                return
            if not verify_password(password, user["password_salt"], user["password_hash"]):
                self.send_error_json(401, "Invalid email or password")
                return
            conn.execute(
                "UPDATE users SET last_login = ?, updated_at = ? WHERE id = ?",
                (datetime.now().date().isoformat(), now_iso(), user["id"]),
            )
            token = create_session(conn, user["id"])
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        self.send_json({"token": token, "user": public_user(user)})

    def handle_logout(self) -> None:
        token = self.auth_token()
        if token:
            with connect() as conn:
                conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
        self.send_json({"ok": True})

    def auth_token(self) -> str:
        header = self.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            return header.removeprefix("Bearer ").strip()
        return self.headers.get("X-Auth-Token", "").strip()

    def require_auth(self) -> sqlite3.Row | None:
        token = self.auth_token()
        if not token:
            self.send_error_json(401, "Authentication required")
            return None
        with connect() as conn:
            user = conn.execute(
                """
                SELECT u.*, r.permissions AS role_permissions
                FROM auth_sessions s
                JOIN users u ON u.id = s.user_id
                LEFT JOIN roles r ON r.name = u.role
                WHERE s.token = ? AND u.status = '启用'
                """,
                (token,),
            ).fetchone()
        if not user:
            self.send_error_json(401, "Authentication required")
            return None
        return user

    def create_record(self, table: str, data: dict, current_user: sqlite3.Row) -> None:
        if not self.validate_record(table, data):
            return
        record = self.normalize_record(table, data, record_id=None, current_user=current_user)
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
        self.send_json(record_response(table, saved), status=201)

    def update_record(self, table: str, record_id: str, data: dict, current_user: sqlite3.Row) -> None:
        with connect() as conn:
            existing = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
            if not existing:
                self.send_error_json(404, "Record not found")
                return
            data["created_at"] = existing["created_at"]
            if table == "defects":
                data["reporter"] = existing["reporter"] or current_user["name"]
            if not self.validate_record(table, data):
                return
            record = self.normalize_record(table, data, record_id=record_id, current_user=current_user)
            assignments = ", ".join([f"{column} = ?" for column in record.keys() if column != "id"])
            values = [value for column, value in record.items() if column != "id"]
            values.append(record_id)
            try:
                conn.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", values)
            except sqlite3.IntegrityError:
                self.send_error_json(409, "Record conflicts with existing data")
                return
            saved = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,)).fetchone()
        self.send_json(record_response(table, saved))

    def validate_record(self, table: str, data: dict) -> bool:
        if table == "requirements":
            required_fields = [
                ("title", "需求名称"),
                ("process_type", "流程类型"),
                ("business_line", "业务线"),
            ]
            for field, label in required_fields:
                if not clean(data.get(field)):
                    self.send_error_json(400, f"{label}不能为空")
                    return False
        return True

    def normalize_record(
        self,
        table: str,
        data: dict,
        record_id: str | None,
        current_user: sqlite3.Row | None = None,
    ) -> dict:
        timestamp = now_iso()
        if table == "requirements":
            participants = normalize_participants(data.get("participants"))
            return {
                "id": record_id or new_id("REQ"),
                "title": clean(data.get("title") or data.get("name")),
                "description": clean(data.get("description")),
                "owner": clean(data.get("owner")) or participant_owner(participants),
                "process_type": clean(data.get("process_type")) or "标准产品流程",
                "business_line": clean(data.get("business_line")),
                "priority": clean(data.get("priority")) or "P2",
                "status": clean(data.get("status")) or "待评审",
                "due_date": clean(data.get("due_date")),
                "requirement_doc": clean(data.get("requirement_doc")),
                "need_tech_review": clean(data.get("need_tech_review")) or "否",
                "participants": participants,
                "launch_country": clean(data.get("launch_country")),
                "followers": clean(data.get("followers")),
                "current_step": clean(data.get("current_step")) or "需求提出",
                "node_owner": clean(data.get("node_owner")),
                "node_score": clean(data.get("node_score")),
                "node_schedule": clean(data.get("node_schedule")),
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
                "role": clean(data.get("role")) or "测试",
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
                "permissions": normalize_permissions(data.get("permissions")),
                "status": clean(data.get("status")) or "启用",
                "created_at": clean(data.get("created_at")) or timestamp,
                "updated_at": timestamp,
            }
        if table == "defects":
            reporter = clean(data.get("reporter")) or clean(current_user["name"] if current_user else "") if record_id else clean(current_user["name"] if current_user else "")
            return {
                "id": record_id or new_id("BUG"),
                "title": clean(data.get("title")),
                "requirement_id": optional_id(data.get("requirement_id")),
                "severity": clean(data.get("severity")) or "S2",
                "priority": clean(data.get("priority")) or "P2",
                "status": clean(data.get("status")) or "新建",
                "reporter": reporter,
                "assignee": clean(data.get("assignee")),
                "environment": clean(data.get("environment")),
                "steps": clean(data.get("steps")),
                "actual_result": clean(data.get("actual_result")),
                "expected_result": clean(data.get("expected_result")),
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
            defect_count = conn.execute("SELECT COUNT(*) AS count FROM defects").fetchone()["count"]
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
            open_defects = conn.execute(
                "SELECT COUNT(*) AS count FROM defects WHERE status NOT IN ('已验证', '已关闭', '已拒绝')"
            ).fetchone()["count"]
        return {
            "requirements": req_count,
            "test_plans": plan_count,
            "test_cases": case_count,
            "defects": defect_count,
            "users": user_count,
            "active_users": active_users,
            "roles": role_count,
            "active_roles": active_roles,
            "open_requirements": open_req,
            "running_plans": running_plans,
            "waiting_cases": waiting_cases,
            "open_defects": open_defects,
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
            "defects": "defects",
            "users": "users",
            "roles": "roles",
        }.get(collection)


def record_response(table: str, row: sqlite3.Row | None) -> dict | None:
    if table == "users":
        return public_user(row)
    return row_to_dict(row)
