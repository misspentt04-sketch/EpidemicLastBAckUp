from aiogram.types import Message

from core.utils.db_api.repo_biowar import RequestsRepoBiowar

from core.data.tricks.tricks_biowar import tricks_biowar

async def show_daily_missions(msg: Message, repo_biowar: RequestsRepoBiowar):
    
    pass
    # mission_list = func.get_mission_list()
    
    # text = tricks_biowar['missions']['show_daily_list'].format(
    #     mission_list, mission_progress
    # )