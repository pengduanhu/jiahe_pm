#!/usr/bin/env python3
from __future__ import annotations

from http.server import ThreadingHTTPServer

from config import DB_PATH, HOST, PORT
from db import init_db
from handlers import AppHandler


def main() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"服务已启动：http://{HOST}:{PORT}")
    print(f"数据库文件：{DB_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    main()
