from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
DB_PATH = Path(__file__).resolve().parent / "project_management.db"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8765"))

DEFAULT_ROLE_PERMISSIONS = {
    "管理员": ["requirements", "plans", "cases", "defects", "users", "roles"],
    "业务方": ["requirements", "defects"],
    "产品经理": ["requirements", "plans"],
    "开发（web端）": ["requirements", "cases"],
    "开发（移动端）": ["requirements", "cases"],
    "开发（后端）": ["requirements", "cases"],
    "测试": ["plans", "cases", "defects"],
}
