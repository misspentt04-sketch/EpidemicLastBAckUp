from core.handlers.biowar.referrals import router as referrals_router
from core.handlers.biowar.labs.lab_text_upgrade import text_upgrade_router
from aiogram import Router

from .admin import admin_router, admin_router_global
from .admin.get_players import router as get_players_router
from .admin.epilab import router as epilab_router
from .corporations import corporation_router
from .labs import lab_router
from .event import event_router
from .donates import donate_router, promos_router
from .infects import infect_router, infect2_router
from .missions import missions_router

biowar_router = Router()
biowar_router2 = Router()
biowar_global_router = Router()

biowar_router.include_routers(
    referrals_router,
    text_upgrade_router, lab_router, corporation_router,
    infect_router,
    admin_router,
    epilab_router,
    event_router,
    missions_router,
    donate_router,
    promos_router
)

biowar_router2.include_routers(infect2_router, )
biowar_global_router.include_routers(admin_router_global)
