from aiogram.filters.callback_data import CallbackData

class Lab(CallbackData, prefix = 'lab_'):
    skill: str
    lvl_up: int
    id: int
    is_my_lab: bool

class LabLvlUpConfirm(CallbackData, prefix = 'lab_confirm_'):
    skill: str
    lvl_up: int
    id: int


class LabLvlUpConfirmExtend(CallbackData, prefix = 'lab_extend_confirm'):
    action: str = 'lvlup_extend'
    skill: str
    lvl_up: int
    user_id: int

class Corporation(CallbackData, prefix = 'corp_'):
    id: int
    action: str
    corp_code: str

class accept_marriage_data(CallbackData, prefix = 'accept_marriage_'):
    skill: str
    ask_id: int
    get_id: int

class reject_marriage_data(CallbackData, prefix = 'reject_marriage_'):
    skill: str
    ask_id: int
    get_id: int

class about_marriage_data(CallbackData, prefix = 'about_marriage_'):
    skill: str
    husband_id: int
    wife_id: int

class accept_MarriageDevorce_data(CallbackData, prefix = 'accept_devorce_'):
    skill: str
    husband_id: int
    wife_id: int
    id: int

class reject_MarriageDevorce_data(CallbackData, prefix = 'reject_devorce_'):
    skill: str
    husband_id: int
    wife_id: int
    id: int

class accept_restore_marrige_data(CallbackData, prefix = 'accept_restore_'):
    skill: str
    ask_id: int
    get_id: int

class reject_restore_marrige_data(CallbackData, prefix = 'reject_restore_'):
    skill: str
    ask_id: int
    get_id: int

class close_marriage_data(CallbackData, prefix = 'close_mar_action_'):
    skill: str
    id: int

class top_exp_data(CallbackData, prefix = 'top_exp_'):
    skill: str
    status: int
    id: int

class top_sms_data(CallbackData, prefix = 'top_sms_'):
    skill: str
    status: int
    id: int

class top_marriages_data(CallbackData, prefix = 'top_marriages_'):
    skill: str
    status: int
    id: int

class DonateList(CallbackData, prefix = 'donate'):
    action: str = 'donate'
    stars_count: int
    kit: int

class DonateListCrypto(CallbackData, prefix = 'donate_crypto'):
    action: str = 'donate_crypto'
    stars_count: int
    kit: int

class PetsListChoose(CallbackData, prefix = 'pet_choose'):
    action: str = 'pet_choose'
    pet: str
    user_id: int


class PetsGlobalListChoose(CallbackData, prefix = 'g_pet_choose'):
    action: str = 'g_pet_choose'
    pet: str
    user_id: int

class prev_marriage_data(CallbackData, prefix = 'prev_marriage_data'):
    skill: str
    id: int
    num: int

class lsit_marriage_data(CallbackData, prefix = 'list_marriage_data'):
    skill: str
    id: int
    status: int
    num: int

class marriages_chat_data(CallbackData, prefix = 'marriages_chat_data'):
    skill: str
    id: int
    status: int

class MyMarriageInfo(CallbackData, prefix = 'my_marriage_info'):
    id: int
    action: str

class MarriageHeart(CallbackData, prefix = 'marriage_heart'):
    action: str = 'heart'

class Tutorial(CallbackData, prefix = 'tutorial'):
    action: str = 'continue'
    lvl: int = 0

