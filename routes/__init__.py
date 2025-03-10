"""
路由模組包
"""
from fastapi import APIRouter

# 創建主路由器
api_router = APIRouter()

# 導入並包含所有路由
from routes.health_routes import router as health_router
from routes.report_routes import router as report_router
from routes.web_routes import router as web_router

# 包含所有路由
api_router.include_router(health_router, tags=["health"])
api_router.include_router(report_router, tags=["reports"])
api_router.include_router(web_router, tags=["web"]) 