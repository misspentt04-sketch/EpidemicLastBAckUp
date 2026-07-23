from aiogram import Router, F

from .tutorial import tutorial_router

story_router = Router()

story_router.include_routers(tutorial_router)