#!/usr/bin/env python3
"""
FastAPI Application Entry Point

This script can be run directly for local development:
    python main.py

Or used with uvicorn:
    uvicorn main:app --reload
"""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    # 本地開發啟動配置
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )
