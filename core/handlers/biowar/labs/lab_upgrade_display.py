from core import func
from core.data.tricks.tricks_biowar import tricks_biowar

def get_upgrade_display(lab_info: dict, skill: str) -> str:
    """Возвращает строку с доступным количеством прокачки"""
    try:
        from_lvl = lab_info[skill]
        bio_res = lab_info["bio_resource"]
        rebirth_lvl = lab_info.get("rebirth_level", 0) or 0
        discount = min(rebirth_lvl * 0.025, 0.10)
        max_lvl = 0
        total_price = 0
        for i in range(1, 51):
            to_lvl = from_lvl + i
            if skill == "science" and to_lvl > 60:
                break
            price = int(func.lvl_up_calc(skill, from_lvl, to_lvl) * (1 - discount))
            if total_price + price <= bio_res:
                total_price += price
                max_lvl = i
            else:
                break
        if max_lvl > 0:
            return f" (+{max_lvl})"
        return ""
    except Exception:
        return ""
