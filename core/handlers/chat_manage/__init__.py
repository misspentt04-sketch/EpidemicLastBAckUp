from aiogram import Router, F

from .chat_addions import addions_router
from .admin import admin_router

chat_manage_router = Router()

chat_manage_router.include_routers(
    admin_router
)