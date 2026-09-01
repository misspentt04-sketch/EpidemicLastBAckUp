from core.data.icons import (
    LabIco, InfectIco, CorpIco,
    OtherIco, PetIco, BagIco,
    DonateIco, EpidemicAdminsIco
)
from core.settings import settings

import textwrap as tw


# Constants
class Const:
    COMMENT = '💬 <b>Записка:</b> <i>⌜{}⌟</i>'
    COMMENT_RP = '💬 <b>Прошептав:</b> <i>⌜{}⌟</i>'
    HEARTS = ['🩷','❤','🧡','💛','💚','🩵','💙','💜','🤍','❣','💕','💞','💓','💗','💖','💘','💝']
    

tricks_biowar = {
    'lvlup_ru_to_en': {
        'патоген': 'pathogens',
        'пат': 'pathogens',
        'разработка': 'science',
        'квала': 'science',
        'заразность': 'infect',
        'зз': 'infect',
        'иммунитет': 'immunity',
        'иммун': 'immunity',
        'имун': 'immunity',
        'летальность': 'lethality',
        'летал': 'lethality',
        'безопасность': 'security_service',
        'сб': 'security_service',
        'биотоп': 'biotops_lab',
        'бт': 'biotops_lab',
        'биотоп чата': 'biotops_lab_chat',
        'бч': 'biotops_lab_chat',
    },
    
    'lvlup_en_to_ru': {
        'pathogens': 'патоген',
        'science': 'разработка',
        'infect': 'заразность',
        'immunity': 'иммунитет',
        'lethality': 'летальность',
        'security_service': 'безопасность',
        'biotops_lab': 'бт',
        'biotops_lab_chat': 'бч'
    },

    'price': {
        'skills': {
            'pathogens': 2,
            'science': 2.6,
            'infect': 2.5,
            'immunity': 2.45,
            'lethality': 1.95,
            'security_service': 2.1
        },
        'multiply': {
            'infect_fever_time': 10
        },
    },

    'max': {
        'skill': {
            'science': 60,
        },
        'skills_coefficient': {
            'infect_percent_claim': 0.15,
            'infect_percent_bonus': 0.50,
            
        },
        'time': {
            'infect_fever_time': 1 * 60 * 60,
            'victim_kd_expire': 2 * 60 * 60,
            'gave_victims_food': 12 * 60 * 60,
        },
        'elements': {
            'pathogen_name_len': 48,
            'lab_name_len': 48,
            'infect_claim_percent': 0.10,
            'infect_boost_percent_by_trailblazer': 0.015,
            'infect_claim_bonus_percent': 0.015
        },
        'corp_max_members': 50,
        'pet_happy_recover_percent': 60,
        'pet_happy_for_hour_percent': 1.5
    },
    
    'skills_lvl': {
        'pathogens': '<blockquote>%(complete_ico)s <b>Увеличение количества ячеек с патогеном на {} (до {})</b>\n%(bio_resource_ico)s <b>Стоимость:</b> {} био-ресурсов</blockquote>\n\n<b>Команда:</b> «<code>++патоген {}</code>» ' % \
            {'complete_ico': LabIco.calendar.value, 'bio_resource_ico': LabIco.bio_resource.value},
        'pathogens_complete': '%(calendar_ico)s Количество ячеек для производства патогенов увеличено на {} (до {})\n%(page_info)s Потрачено: %(bio_resource_ico)s {} био-ресурс' % \
            {'calendar_ico': OtherIco.complete, 'page_info': OtherIco.page_info, 'bio_resource_ico': LabIco.bio_resource.value},
        'science': '<blockquote>%(complete_ico)s Ускорение производства патогена на {} уровень (до {} мин.)\n%(bio_resource_ico)s <b>Стоимость:</b> {} био-ресурсов</blockquote>\n\n<b>Команда:</b> «<code>++разработка {}</code>» ' % \
            {'complete_ico': OtherIco.complete, 'bio_resource_ico': LabIco.bio_resource.value},
        'science_complete': '%(complete_ico)s Ускорение производства патогена на {} уровень (до {} мин.) выполнено\n%(page_info)s Потрачено: %(bio_resource_ico)s {} био-ресурсов' % \
            {'complete_ico': OtherIco.complete, 'page_info': OtherIco.page_info, 'bio_resource_ico': LabIco.bio_resource.value},
        'infect': '<blockquote>%(complete_ico)s Усиление заразности патогена на {} ур (до {})\n%(bio_resource_ico)s <b>Стоимость:</b> {} био-ресурсов</blockquote>\n\n<b>Команда:</b> «<code>++заразность {}</code>» ' % \
            {'complete_ico': OtherIco.complete, 'bio_resource_ico': LabIco.bio_resource.value},
        'infect_complete': '%(complete_ico)s Усиление заразности патогена на {} ур (до {}) выполнено\n%(page_info)s Потрачено: %(bio_resource_ico)s {} био-ресурсов' % \
            {'complete_ico': OtherIco.complete, 'page_info': OtherIco.page_info, 'bio_resource_ico': LabIco.bio_resource.value},
        'immunity': '<blockquote>%(complete_ico)s Укрепление иммунитета на {} ур (до {})\n%(bio_resource_ico)s <b>Стоимость:</b> {} био-ресурсов</blockquote>\n\n<b>Команда:</b> «<code>++иммунитет {}</code>» ' % \
            {'complete_ico': OtherIco.complete, 'bio_resource_ico': LabIco.bio_resource.value},
        'immunity_complete': '%(complete_ico)s Укрепление иммунитета на {} ур (до {}) выполнено\n%(page_info)s Потрачено: %(bio_resource_ico)s {} био-ресурса' % \
            {'complete_ico': OtherIco.complete, 'page_info': OtherIco.page_info, 'bio_resource_ico': LabIco.bio_resource.value},
        'lethality': '<blockquote>%(complete_ico)s Усиление летальности патогена на {} (до {})\n%(bio_resource_ico)s <b>Стоимость:</b> {} био-ресурса</blockquote>\n\n<b>Команда:</b> «<code>++летальность {}</code>» ' % \
            {'complete_ico': OtherIco.complete, 'bio_resource_ico': LabIco.bio_resource.value},
        'lethality_complete': '%(calendar_ico)s Усиление летальности патогена на {} (до {}) выполнено\n%(page_info)s Потрачено: %(bio_resource_ico)s {} био-ресурсов' % \
            {'calendar_ico': OtherIco.complete, 'page_info': OtherIco.page_info, 'bio_resource_ico': LabIco.bio_resource.value},
        'security_service': '<blockquote>%(complete_ico)s Укрепление службы безопасности на {} ур (до {})\n%(bio_resource_ico)s <b>Стоимость:</b> {} био-ресурсов</blockquote>\n\n<b>Команда:</b> «<code>++безопасность {}</code>» ' % \
            {'complete_ico': OtherIco.complete, 'bio_resource_ico': LabIco.bio_resource.value},
        'security_service_complete': '%(complete_ico)s Укрепление службы безопасности на {} ур (до {}) выполнено\n%(page_info)s Потрачено: %(bio_resource_ico)s {} био-ресурсов' % \
            {'complete_ico': OtherIco.complete, 'page_info': OtherIco.page_info, 'bio_resource_ico': LabIco.bio_resource.value}
    },
    
    'inline': {
        'not_your_button': ['Не для тебя моя кнопочка росла', 'Ты слишком горяч! Дай кнопке передохнуть(', 'Не насилуй кнопку, она итак даст']
    },

    'ping': {
        'мяу': 'мур',
        'мур': 'мяу',
        'бот': [
            '💚 Бот в деле!',
            '💚 Привет, я на связи',
            '💚 Бот готов к работе',
            '💚 Слышу тебя громко и чётко',
            '💚 Ваш бот на посту',
            '💚 А вот и я!',
            '💚 Бот активирован',
            '💚 Всегда рядом',
            '💚 Бот к вашим услугам',
            '💚 Пинг принят, бот отвечает'
        ]
    },
    
    'lab': {
        'fever': '😓 Ученый в состоянии горячки ещё {}',
        
        'max_level_up_limit': '‼️Навык <b>«{}»</b> достиг максимального уровня прокачки',
        
        'pathogen_name_change': '♻️ Новый идентификатор патогена изменён на <b>«{}»</b>',
        
        'pathogen_name_change_max_len': '%(memo_ico)s Название патогена не должно превышать более {} символов' % \
            {'memo_ico': OtherIco.memo},
        
        'show_lab_dossier': tw.dedent("""
            ❇️Внимание, лаборатория рассекречена, {}.
            <b>Лаборатория — видна.</b>
            """),
        
        'hide_lab_dossier': tw.dedent("""
            ‼️Внимание, лаборатория засекречена, {}.
            <b>Лаборатория — скрыта.</b>
            """),
        
        'lab_dossier_secret': tw.dedent("""
            %(memo_ico)s Объект засекретил досье о своей лаборатории

            %(conversation_ico)s Вы можете попросить его открыть досье командой "+лаб"
            """) % \
                {'memo_ico': OtherIco.memo, 'conversation_ico': OtherIco.conversation},
        
        'customization_emoji':'%(two_fly_hearts_ico)s Вы установили кастомное эмоджи, для вашей лабы {}' % \
            {'two_fly_hearts_ico': LabIco.two_fly_hearts.value},
        
        'remove_emoji_customization': '%(cancel_green_ico)s Эмоджи {} убрана из вашей лаборатории' % \
            {'cancel_green_ico': OtherIco.cancel_green},
        
        'wrong_emoji_customization': '%(memo_ico)s Предложенный вариант не является эмоджи' % \
            {'memo_ico': OtherIco.memo},
        
        'hasnt_emoji_customization': tw.dedent("""
            %(cancel_green_ico)s Вы не имеете кастомного эмоджи
            \n
            <i>Воспользуйтесь командой <code>лаб эмоджи (ваш эмоджи)</code> для установления эмоджи</i>
            """) % \
                {'cancel_green_ico': OtherIco.cancel_green},
        
        'pathogen_name_already_exists': '%(memo_ico)s Это имя патогена уже занято' % {'memo_ico': OtherIco.memo},
        'lab_name_already_exists': '%(memo_ico)s Это название лаборатории уже занято' % {'memo_ico': OtherIco.memo},
        'lab_name_max_len': '%(memo_ico)s Название лаборатории не должно превышать более {} символов' % {'memo_ico': OtherIco.memo},
        'change_lab_name': '%(complete_ico)s Название лаборатории изменено на <b><i>«{}»</i></b>' % {'complete_ico': OtherIco.complete},
        'remove_lab_name': '%(cancel_green_ico)s Название лаборатории изменено на <b><i>«{}»</i></b>' % {'cancel_green_ico': OtherIco.cancel_green},
        'delete_pathogen_name': '❌ Информация о названии патогена утеряна',
    },
    
    'infect': {
        
        'infect': tw.dedent("""
            %(virus_ico)s {} подверг заражению патогеном {} {}
            %(lethality_ico)s Горячка на {} минут
            %(infected_ico)s Заражение на {} дней
            %(bio_experience_ico)s +{} био-опыта{}
            
            {}
            """) % \
                {
                    'virus_ico': LabIco.virus.value, 'lethality_ico': InfectIco.lethality, 'infected_ico': LabIco.infected.value,
                    'bio_experience_ico': LabIco.bio_experience.value,
                },
        
        
        'victim_immunity_fail': f"{LabIco.immunity.value} Иммунитет объекта «{{0}}» оказался стойким к вашему патогену.\nАнтитела смогли справиться с заражением.\n{LabIco.pathogens.value} Осталось патогенов: {{1}}\n{{2}} Шкала пробития: {{3}}",
        
        'victim_ss_fail': tw.dedent("""
            %(explosion_ico)s Попытка заразить «{}⁬» провалилась...
            При подготовке к спецоперации ячейка с патогеном разбилась.
            %(pathogens_ico)s Осталось патогенов: {}
            {} Шкала пробития: {}
            """) % \
                {'explosion_ico': OtherIco.explosion, 'pathogens_ico': LabIco.pathogens.value},
        
        'impossible_to_infect_bot': '%(memo_ico)s Попробуйте заразить сущность умеющую дышать' % \
            {'memo_ico': OtherIco.memo},
        
        'impossible_to_touch_bot': '%(memo_ico)s Нельзя трогать бота' % \
            {'memo_ico': OtherIco.memo},
        
        'pathogens_over': tw.dedent("""
            %(memo_ico)s Недостаточно патогенов для заражения жертвы
            """) % \
                {'memo_ico': OtherIco.memo},
        
        'pathogen_count_limit': '%(memo_ico)s Для заражения необходимо не больше {} патогенных организмов' % \
            {'memo_ico': OtherIco.memo},
        
        'pathogen_count_zero': '%(memo_ico)s Для заражения жертвы, увы, 0 патогенов явно не хватит!' % \
            {'memo_ico': OtherIco.memo},
        
        'self_infect': tw.dedent("""
            %(memo_ico)s Вы стремились к эксперименту на пределе, допустимости, но ваш организм решил, что вместо этого будет заняться более увлекательными занятиями, такими как выживание, например.
            """) % \
                {'memo_ico': OtherIco.memo},
        
        'fever': tw.dedent("""
            %(infected_ico)s У вас горячка, вызванная {} Придётся отлежаться, пока не пройдёт
            Время выздоровления {}
            
            %(infect_ico)s Для быстрого выздоровления нужно купить вакцину: %(bio_experience_ico)s, команда «<code>!купить вакцину</code>»
            """) % \
                {'infected_ico': LabIco.infected.value, 'infect_ico': LabIco.infect.value, 'bio_experience_ico': LabIco.bio_experience.value},
        
        'have_not_fever': '<b>❤️‍🩹 Вы здоровы.</b> Нет горячки — нет нужды в вакцине.',
        
        'buy_vaccine_joke': [
        '🚬 Браво, вы скурили вакцину!',
        '🚬 Вакцина? Не, теперь пепел!',
        '🚬 Вылечиться? Не, лучше скурить!',
        '🚬 Вакцина ушла в дым — поздравляю!',
        '🚬 Отличный выбор, скурили спасение!',
        '🚬 Вакцина? Теперь просто дымок!',
        '🚬 Молодец, выкурил здоровье!',
        '🚬 Вакцина сгорела — шикарно!',
        '🚬 Курнул вакцину? Гениально!',
        '🚬 Прощай, вакцина, здравствуй дым}'
        ],
        
        'sb_virus_detect': tw.dedent("""
            %(security_service_ico)s Служба безопасности лаборатории {} докладывает:
            Былa произведена кaк минимyм {} попытка вашего заражения
            Организатор заражения: {}
            
            %(virus_ico)s {} подверг зaражению патогеном {} {}
            %(lethality_ico)s Горячка на {} минут
            %(infected_ico)s Заражение на {} дней
            %(bio_experience_ico)s +{} био-опыта
            
            {}
            """) % \
                {
                    'security_service_ico': LabIco.security_service.value, 'virus_ico': LabIco.virus.value,
                    'lethality_ico': InfectIco.lethality, 'infected_ico': LabIco.infected.value,
                    'bio_experience_ico': LabIco.bio_experience.value,
                },
        
        'sb_virus_not_detect_text': tw.dedent("""
            %(virus_ico)s Кто-то подверг заражению {}⁬ {}
            %(lethality_ico)s Горячка на {} минут
            %(infected_ico)s Заражение на {} дней
            """) % \
                {
                    'virus_ico': LabIco.virus.value, 'lethality_ico': InfectIco.lethality,
                    'infected_ico': LabIco.infected.value,
                },
        
        'sb_virus_detect_try_text': tw.dedent("""
            %(security_service_ico)s Служба безопасности лаборатории {} докладывает:
            Была произведена как минимум {} попытка Вашего заражения
            Организатор заражения: {}
            
            %(immunity_ico)s Иммунитет объекта «{}⁬» оказался стойким к вашему патогену.
            Антитела смогли справиться с заражением.
            """) % \
                {'security_service_ico': LabIco.security_service.value, 'immunity_ico': InfectIco.immunity},
        
        
        'add_virus_signal': '%(complete_ico)s Локация для уведомлений о вирусных атаках установлена' % \
            {'complete_ico': OtherIco.complete},
        
        'del_virus_signal': '%(cancel_green_ico)s Вы отключили оповещения вирусов от Эпидемик' % \
            {'cancel_green_ico': OtherIco.cancel_green},
        
        'victims_list': tw.dedent("""
            %(infect_ico)s Список больных вашим патогеном:
            {}
            
            %(statistics_ico)s Итого: {} заражённых и {} био-опыта
            %(bio_resource_ico)s Ежедневная премия: {} био-ресурсов
            """) % {'infect_ico': LabIco.infect.value, 'statistics_ico': LabIco.statistics.value, 'bio_resource_ico': LabIco.bio_resource.value},
        
        'illnesses_list': tw.dedent("""
            %(infected_ico)s Список ваших болезней:
            {}
            """) % {'infected_ico': LabIco.infected.value}, 
    },
    
    'corporation': {
        
        'get_corporation': tw.dedent("""
            🔆 КОРПОРАЦИЯ «{}» 
            <b>Руководитель:</b> {} ☣️ {} | {}
            <b>———[ СТАТИСТИКА ]———</b>
            «☣️» Био-опыт: {}
            «🤒» Заражённых: {}
            «🚸» Лабораторий: {}
            <b>——————————————</b>
            <b>Код вступления:</b> <code>{}</code>
            <b>Досье корпорации:</b> {}
            """),
        
        'get_corporation_members': tw.dedent("""
            %(main_corp_ico)s УЧАСТНИКИ КОРПОРАЦИИ «{}»
            {}
            """) % \
                {'main_corp_ico': CorpIco.main_corp},
        
        'get_corporation_invites': tw.dedent("""
            %(calendar_ico)s Список заявок в корпорацию «{}»
            {}
            """) % \
                {'calendar_ico': OtherIco.calendar},
        
        'create_corporation': tw.dedent("""
            ✅ Поздравляем! Ваша корпорация <b>«{}»</b> создана!
            
            <blockquote>— Желающие могут вступить, попросив владельца корпорации открыть <i>.корп</i> нажав на кнопку вступления</blockquote>
            <b>🧩 Либо, используя команду «<code>+корп {}</code>»</b>
            """),
        
        'delete_corporation': '❌ Корпорация <b>«{}»</b> прекращает своё существование.',
    
        'alredy_exists_corporation': tw.dedent("""
            %(memo_ico)s Вы уже создали свою Корпорацию.
            
            %(conversation_ico)s Руководители других Лабораторий могут вступать в неё командой "+корп {}"
            """) % \
                {'memo_ico': OtherIco.memo, 'conversation_ico': OtherIco.conversation},
        
        'alredy_exists_corporation_inline': tw.dedent("""
            %(memo_ico)s {} Вы уже создали свою Корпорацию.
            
            %(conversation_ico)s Руководители других Лабораторий могут вступать в неё командой "+корп {}"
            """) % \
                {'memo_ico': OtherIco.memo, 'conversation_ico': OtherIco.conversation},
        
        'corp_name_already_exists': '%(memo_ico)s Это имя корпорации уже занято' % {'memo_ico': OtherIco.memo},
        
        'lab_not_in_corp': '%(memo_ico)s Ваша Лаборатория не состоит ни в одной Корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'lab_not_in_your_corp': '%(memo_ico)s Лаборатория не состояла в вашей Корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'already_has_corp': '%(memo_ico)s Лаборатория уже находится в чужой Корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'you_has_no_corp': '%(memo_ico)s Вы не являетесь главой ни одной Корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'corporation_does_not_exists': '%(memo_ico)s Такой Корпорации не существует' % \
            {'memo_ico': OtherIco.memo},
        
        'corporation_does_not_exists_inline': '%(memo_ico)s {} Такой Корпорации не существует' % \
            {'memo_ico': OtherIco.memo},
        
        'invite_request_send_corp': '💚 {}, вы подали заявку на вступление в корпорацию <b>«{}»</b>!',
        
        'invite_request_send_corp_inline': '💚 {}, вы подали заявку на вступление в корпорацию <b>«{}»</b>!',
        
        'already_has_invite_request': '%(memo_ico)s Вы уже подавали заявку на вступление в эту Корпорацию' % \
            {'memo_ico': OtherIco.memo},
        
        'you_are_not_admin': '%(memo_ico)s Вы не являетесь главой или соучредителем ни одной корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'user_does_not_send_invite': '%(memo_ico)s Лаборатория не подавала заявку на вступление в вашу Корпорацию' % \
            {'memo_ico': OtherIco.memo},
        
        'leave_corp': '%(cancel_green_ico)s Ваша Лаборатория вышла из состава корпорации «{}»' % \
            {'cancel_green_ico': OtherIco.cancel_green},
        
        'owner_corp_self_kick': '%(memo_ico)s Основатель корпорации не способен исключить себя из состава – это, пожалуй, слишком радикальный шаг.' % \
            {'memo_ico': OtherIco.memo},
        
        'add_corp_admin': '%(complete_ico)s {} назначен соучредителем Корпорации' % \
            {'complete_ico': OtherIco.complete},
        
        'del_corp_admin': '%(cancel_green_ico)s {} разжалован из соучредителей корпорации' % \
            {'cancel_green_ico': OtherIco.cancel_green},
        
        'isnt_corp_admin': '%(memo_ico)s {} не являлся соучредителем корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'already_corp_admin': '%(memo_ico)s {} уже является соучредителем Корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'kick_from_corp': '%(cancel_green_ico)s Лаборатория «{}» исключена из корпорации «{}»' % \
            {'cancel_green_ico': OtherIco.cancel_green},
        
        'invite_request_reject': '%(cancel_green_ico)s Ваш талант слишком уникален для нашей скромной компании, извините."' % \
            {'cancel_green_ico': OtherIco.cancel_green},
        
        'invite_request_accept': '{} Принят в корпорацию, наши поздравления, мы будем гордиться иметь вас в нашей корпорации. Добро пожаловать! 😇🥰',
        
        'invite_reuqest_accept_pm_mention': 'Поздравляем, вашу заявку в корпорацию {} приняли. Добро пожаловать! 😇🥰',
        
        'change_corp_name': '%(complete_ico)s Название корпорации «{}» обновлено' % \
            {'complete_ico': OtherIco.complete},
        
        'show_corp_dossier': '%(complete_ico)s Информация о вашей Корпорации теперь доступна для просмотра всем' % \
            {'complete_ico': OtherIco.complete},
        
        'hide_corp_dossier': '%(cancel_green_ico)s Информация о вашей Корпорации засекречена' % \
            {'cancel_green_ico': OtherIco.cancel_green},
        
        'corp_info_secret': '%(memo_ico)s {} Информация о Корпорации засекречена' % \
            {'memo_ico': OtherIco.memo},
        
        'member_limit_reached': '%(memo_ico)s Достигнут максимальный лимит членов корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'list_corp_admins': tw.dedent("""
            %(calendar_ico)s Соучредители корпорации «{}»
            {}
            """) % \
                {'calendar_ico': OtherIco.calendar},

        'admin_kick_restricted': '%(memo_ico)s Нельзя исключить админа одинакового или выше вас рангом из корпорации' % \
            {'memo_ico': OtherIco.memo},
        
        'owner_cant_leave_from_own_corp': '<b>🔻 Вы — владелец.</b> Покинуть корпорацию невозможно.'
    },
    
    'biotops': {
        
        'lab': tw.dedent("""
            %(microscop_ico)s <b>Топ Лабораторий по био-опыту:</b>
            
            {}
            
            Суммарный био-опыт: {}
            """) % \
                {'microscop_ico': LabIco.microscop.value},
    
        'lab_chat': tw.dedent("""
            %(microscop_ico)s <b>Топ Лабораторий чата по Био-опыту:</b>
            
            {}
            
            Суммарный био-опыт: {}
            """) % \
                {'microscop_ico': LabIco.microscop.value},
        
        'corporations': tw.dedent("""
            %(microscop_ico)s <b>Топ Корпораций по заражениям:</b>
            
            {}
            """) % \
                {'microscop_ico': LabIco.microscop.value},
        
        'event': tw.dedent("""
            <b>🌸 Ивент:</b> <i>«Апрельный день»</i>
            <b>———————————>
            🌷 [ Шуточки: рейтинг апрелек ] 🌷
            ———  |🏆| — |🏆|—&gt</b>
            <blockquote>{}</blockquote>\
            <blockquote>{}</blockquote>\
            <blockquote>{}</blockquote>\
            <blockquote>{}</blockquote>\
            <blockquote>{}</blockquote>\
            
            <i>«Учёные создали бактерию, которая заставляет говорить правду. Первыми жертвами стали политики. Мир в панике.»</i>
            """)
    },
    
    'text': {
        'confirm_upgrade': 'Подтвердить улучшение',
        
        'not_enough_resources': f'{OtherIco.memo} У вас нет столько био-ресурсов',
        
        'max_reached_skill_lvl': '%(memo_ico)s За один раз можно произвести улучшение не более, чем на 50 уровней' % \
            {'memo_ico': OtherIco.memo},
        
        'victim_expire_yes': '%(infected_ico)s Недавно Вы уже подвергали заражению выбранный объект.\n%(stopwatch)s Следующая возможность появится через {}' % \
            {'infected_ico': LabIco.infected.value, 'stopwatch': OtherIco.stopwatch},
        
        'victim_new' :'%(vic_new)s<i> Жертва заражена новой мутацией вируса, это принесло вам ценные генетические данные и последующую прибыль от исследований <b>+{}</b> био-ресурса</i>' % \
            {'vic_new': InfectIco.vic_new},
        
        'buy_vaccine': tw.dedent("""
            <blockquote>%(infect_ico)s <b>Вы излечились от горячки.</b>
            %(bio_resource_ico)s <b>Затраты на лечение:</b> {} био-ресурсов</blockquote>
            
            {}
            """) % \
                {'infect_ico': LabIco.infect.value, 'bio_resource_ico': LabIco.bio_resource.value},
        
        'not_info_about_user': '%(memo_ico)s Данные о субъекте отсутствуют' % {'memo_ico': OtherIco.memo},
        'victim_not_found': '%(memo_ico)s Не удалось найти жертву, для заражения' % {'memo_ico': OtherIco.memo},
        'button_click_action': '%(memo_ico)s {} Активировал кнопку' % {'memo_ico': OtherIco.memo},
    },
    
    'pet': {
        'get_my_pet': tw.dedent("""
            {} <b>Ваш питомец:</b> {}
            {} <b>Стихия:</b> {}
            {} <b>Счастье:</b> {}%
            
            <b>Особенности</b>
            {}

            {}
            """),
        'get_my_pets': '%(two_heart_ico)s Ваши питомцы:' % {'two_heart_ico': PetIco.two_heart},
        'hasnt_pet': '%(memo_ico)s У вас нет питомца, напишите в лс боту <a href="https://t.me/%(bot_username)s?start=ls">нажав сюда</a>' % \
            {'memo_ico': OtherIco.memo, 'bot_username': settings.bots.bot_username},
        'pet_the_pet': tw.dedent("""
            {}
            
            <i>Вы получили <b>+{} %(primogem_ico)s</b></i>
            <i>Счастье вашего питомца повысилось до {}%% </i>😃
            {}
            """ % \
                {'primogem_ico': BagIco.primogem}
        ),
        'not_pet_the_pet_time': '%(stopwatch_ico)s Вы уже гладили ранее питомца, погладить ещё раз можно через {}.' % {'stopwatch_ico': OtherIco.stopwatch},
        'not_your_pet': '%(pet_stole_in_disgust_ico)s Питомец с отвращением отпрянул от вас и прихватил <b>{} примогемов</b> себе' % \
            {'pet_stole_in_disgust_ico': PetIco.pet_stole_in_disgust},
        'not_your_pet_not_enough_primogem': '%(pet_stole_in_disgust_ico)s Питомец с отвращением отпрянул от вас. Обыскал ваши карманы, но ничего не нашёл...' % \
            {'pet_stole_in_disgust_ico': PetIco.pet_stole_in_disgust},
        'pets_info': {
            'первопроходец': {
                'en': 'trailblazer',
                'element': 'гармония',
                'element_en': 'harmony',
                'emoji': '🍉',
                'element_emoji': '🦋',
                'skill': 'Дает 1.5% ежедневной премии от потенциального получаемого опыта с жертвы',
                'description': '«Я — Первопроходец. Готова исследовать самые далёкие уголки вселенной... но для начала стоит —перекусить! Арбуз делает любые путешествия более запоминающимися и самое главное ВКУСНЫМИ.»',
                'skill_val': 0.015
            },
            'аквелиа': {
                'en': 'akvaelia',
                'element': 'вода',
                'element_en': 'water',
                'emoji': '💚',
                'element_emoji': '🌊',
                'skill': 'Увеличивает на 100% больше максимальное кол-во получаемых примогемов',
                'description': 'Меня зовут Аквелия, и я — дитя воды. Я рождаюсь там, где лунный свет касается морских волн, наполняя их чистой энергией. Моё сердце — сияющий кристалл, в котором хранятся секреты глубин и сила приливов. Со мной ты станешь удачливее, ведь я способна удваивать дары судьбы.'
            },
            'байлу': {
                'en': 'bailu',
                'element': 'изобилие',
                'element_en': 'abundance',
                'emoji': '🥤',
                'element_emoji': '🌾',
                'skill': 'С шансом 40% излечивает игрока от горячки',
                'description': 'Я — Байлу, целительница из Комиссии по алхимии. Что с тобой, где болит?.. Голова болит?  Подойди поближе, дай мне взглянуть на тебя. Драконы Видьядхара хранят древние знания исцеления, и я с радостью поделюсь ими, чтобы облегчить твою боль. '
            },
            'лиуфэй': {
                'en': 'liufei',
                'element': 'огонь',
                'element_en': 'fire',
                'emoji': '🐉',
                'element_emoji': '🔥',
                'skill': 'Soon...',
                'description': 'Я — Лиуфэй, великий и ужасный дракон, чья мощь могла бы стереть вас с лица земли одним лишь взмахом хвоста. Но увы, судьба распорядилась иначе, и теперь я служу Вам, жалкому смертному. Служу вам не по доброте душевной, а лишь потому, что мне так угодно. Запомните это… и не испытывайте мое терпение.'
            },
            'фурина': {
                'en': 'furina',
                'element': 'гидро',
                'element_en': 'hydro',
                'emoji': '🩵',
                'element_emoji': '💦',
                'skill': 'Распределение и изменение первоэлемента в два состояния: пневма и усия. Пневма даёт шанс в 5% пробить иммунитет оппонента быстрее. Усия уменьшает шанс пробития вашего иммунитета на 5%. Шанс возникновение эффекта: 50%',
                'description': '«Что ты стоишь, разинув рот? Ах да, наверное, не можешь найти слов от ошеломления. Всё же это Я — звезда Фонтейна, Фурина. У меня плотный график, так что тебе повезло со мной встретиться.»',
                'skill_val': 0.05
            },
            'мимин': {
                'en': 'mimin',
                'element': 'любовь',
                'element_en': 'love',
                'emoji': '🌸',
                'element_emoji': '💞',
                'skill': 'Питомец излучает тепло, может исцелять разбитые сердца и дарить чудную ауру. Чудная аура — заключается в скидке 25% на исцеление, т.e при покупки вакцины',
                'description': 'Привет, мой дорогой друг. Мне звать — Мимин. Не надо лишних слов – я здесь, чтобы поддержать тебя, без  всяких условий и причин. Я готова залечить твои раны и душевные терзания, только скажи. Хорошо?',
                'skill_val': 0.25
            },
            'ам-ням': {
                'en': 'om-nom',
                'element': 'обжорство',
                'element_en': 'gluttony',
                'emoji': '🍭',
                'element_emoji': '🍏',
                'skill': 'При заражении жертвы, есть шанс в 5% получить «вкусность»(3% вместо 1.5%). Значение «вкусности» варьируется от био-опыта жертвы. Заражение — дает 1.5% ежедневной премии от потенциального получаемого опыта с жертвы.',
                'description': '«Я — Ам Ням, пожиратель без меры и края. Никакая пища не способна насытить меня, и любая сила не удержит меня от того, чтобы попробовать ещё кусочек… или весь мир целиком!»',
                'skill_val': 0.015
            }
            
        },
        'pet_skills_text': {
            'байлу': {
                'heal_fever': '<i>🥤 Ваш питомец <b>Байлу</b> позаботился о вашем состоянии и вылечил вас от горячки.</i>'
            }
        }
    },
    'bag': {
        'get_bag': (
            '%(BagIco_box)s <b>Ламинарный бокс</b> \n\n'

            '%(BagIco_stocks)s Запасы реагентов \n'
            '%(BagIco_stellar_jade)s звездного нефрита: {stellar_jade}\n' 
            '%(BagIco_primogem)s примогемов: {primogem} \n\n'
            
             '{link}, вы можете купить новых питомцев командой(<code>крутка</code>) или био-ресы(<code>нефритсвап 1</code>, <code>примосвап 1</code>). /donate - купить нефрит.' % \
            {"BagIco_stellar_jade": BagIco.stellar_jade, "BagIco_box": BagIco.box, "BagIco_stocks": BagIco.stocks, "BagIco_primogem": BagIco.primogem}
        ),
        'send_currency': tw.dedent("""
            %(stellar_jade)s Игроку <b>{}</b> звездным экспрессом было отправлено <b>{} нефрита</b>
            
            {}
            {}
            """) % {'stellar_jade': BagIco.stellar_jade},
        'get_currency': tw.dedent("""
            %(stellar_jade)s <b>{}</b> вам прислал звездным экспрессом <b>{} нефрита</b>
            <i>{}</i>
            """) % {'stellar_jade': BagIco.stellar_jade},
        'not_enough_stellar_jade': '%(box)s Ваш ламинарный бокс пуст или у вас недостаточно звездного нефрита или примогема\n\n{}' %
            {'box': BagIco.box},
        'you_cant_send_to_yourself': '✨✨✨ Себе <b>звездный нефрит</b> не подаришь, никто не подарит ✨✨✨',
        'convert_stellar_jade_to_primo': (
            '<b>Вы перевели {jade} %(stellar_jade_icon)s звездного нефрита в {primo} %(promogem_icon)s примогема(ов)!</b>'
        ) % {"stellar_jade_icon": BagIco.stellar_jade, "promogem_icon": BagIco.primogem},
        'convert_stellar_jade_to_bio_resource': (
            '<b>Вы перевели {jade} %(stellar_jade_icon)s звездного нефрита в {bio_resource} 🧬 био ресурса(ов)!</b>'
        ) % {"stellar_jade_icon": BagIco.stellar_jade},
        'convert_primogem_to_bio_resource': (
            '<b>Вы перевели {primogem} %(primogem_icon)s примогемов в {bio_resource} 🧬 био ресурса(ов)!</b>'
        ) % {"primogem_icon": BagIco.primogem},
        'convert_not_enough_stellar_jade': f"{BagIco.stellar_jade} Недостаточно звездного нефрита"
    },
    'donate': {
        'donate_list': tw.dedent("""
            %(bag)s <b>Магазин звездного нефрита</b>
            
            Здесь можно купить один из предложеных запасов звездного нефрита, ценных материалов в чрезвычайно опасном радиационном мире Эпидемии. 
            
            <b>Двойной бонус действителен только для первой покупки одного из набора звездного нефрита</b>
            
            <blockquote><b>Замечание: Мы рекомендуем покупать звездочки через Fragment,</b> из-за комиссий 40%% <a href='https://fragment.com/stars'>Fragment</a></blockquote>

            {} <i>пожалуйста, играйте умеренно и не тратьтесь сверх меры. <a href='https://telegra.ph/Terms-of-Service-for-Epidemic-donate-07-21'>ToS</a>, /donate</i>
            """) % {'bag': DonateIco.bag},
        'donate_list_crypto': tw.dedent("""
            %(bag)s <b>Магазин звездного нефрита</b>
            
            Здесь можно купить один из предложеных запасов звездного нефрита, ценных материалов в чрезвычайно опасном радиационном мире Эпидемии. Гайд на покупку <a href="https://telegra.ph/Donat-05-31">крипты</a>
            
            <b>Двойной бонус действителен только для первой покупки одного из набора звездного нефрита</b>
            
            {} <i>пожалуйста, играйте умеренно и не тратьтесь сверх меры. <a href='https://telegra.ph/Terms-of-Service-for-Epidemic-donate-07-21'>ToS</a>, /donate</i>
            """) % {'bag': DonateIco.bag},
        'donate_in_group': '%(bag)s <b>{}</b> для совершении доната и покупки <b>звездного нефрита</b> перейдите в лс бота' %
            {'bag': DonateIco.bag},
        'invoice_title': 'Эпидемик донат',
        'invoice_description': '%(stellar_jade)s {} звездных нефритов' % 
            {'stellar_jade': BagIco.stellar_jade},
        'payment_successful': tw.dedent("""
            <b>Донат успешен! Спасибо вам за покупку {} %(thanks_for_payment_heart)s</b>
            
            Вам выдано <b>{}</b> %(stellar_jade)s звездных нефритов
            
            <i>Жмякните на <b><a href="https://t.me/%(bot_username)s?text=Ламинарный+бокс">ламинарный бокс</a></b></i>
            """) % 
            {
                'thanks_for_payment_heart': DonateIco.thanks_for_payment_heart,
                'stellar_jade': BagIco.stellar_jade,
                'bot_username': settings.bots.bot_username
            },
        'payment_successful_sticker': 'CAACAgIAAxkBAAEajBxmm5Y5Ml4poF1wHufA15hdg9TKQgAC-k8AAneB4UgAAdqis3mjfBA1BA',
        'payment_unsuccessful': '%(bag)s Нам не получилось, получить подтверждение платежа. Попробуйте ещё раз /donate или свяжитесь с тех. поддержкой Эпидемик.' %
            {'bag': DonateIco.bag},
        'payment_unsuccessful_sticker': 'CAACAgIAAxkBAAEajoRmnSbx503O83XHHCLLt4JUCcu3aAACLVcAAnHg6EjaWFCZveqakDUE',
        'paysupport': tw.dedent("""
            Если вы хотите вернуть средства за покупку, воспользуйтесь командой /refund
            
            <i>Прочтите <a href='https://telegra.ph/Instrukciya-dlya-pokupki-Telegram-Stars-cherez-Fragment-07-21'>Terms of Service</a></i>
            """),
        'refund_no_code_provided': tw.dedent("""
            Введите команду <code>/refund КОД</code>, где КОД – айди транзакции.
            Его можно увидеть после выполнения платежа, а также в разделе «Звёзды» в приложении Telegram.
        """),
        'refund_successful': 'Возврат произведён успешно. Потраченные звёзды уже вернулись на ваш счёт в Telegram.',
        'refund_code_not_found': 'Такой код покупки не найден. Пожалуйста, проверьте вводимые данные и повторите ещё раз.',
        'refund_already_refunded': 'За эту покупку уже ранее был произведён возврат средств.',
        'redirect_to_cryptobot': tw.dedent("""
            <b>Инструкция по покупке:</b>
            
            1. Жмякните на кнопку внизу.
            2. Вы перейдете в бота, там выбираете криптовалюту для оплаты.
            <i>3. Жмякаете кнопку «Оплатить» и нажимаете самую первую кнопку с выбором сети TON.(необязательно)</i>
            4. Оплата успешна! 💚
            
            <i>Криптовалюту можно купить через банковскою карту <a href='https://t.me/CryptoBot?start=p2p'>здесь</a> или отправить с @wallet на @CryptoBot</i>
        """),
        'crypto_pay_hidden_message': '💚 Оплата прошла успешно, возвращайтесь в Эпидемик https://t.me/%(bot_username)s' %
            {'bot_username': settings.bots.bot_username},
    },
    'epidemic_admins': {
        'bio_muted': '%(warning_ico)s У вас мут на изменения игровых наименований на {} дней' % {
            'warning_ico': EpidemicAdminsIco.warning_ico
        }
    },
    'event': {
        'choose_character_gender': 'Выберите гендер вашего школьника',
        'show_character': tw.dedent("""
            <b>{}</b>
            Уровень: <i>{}</i>
            Репутация: <i>{}</i>
            {}
            """),
        'character_lvls': {
            'female': {
                1: 'CAACAgIAAxkBAAEbJL5m4JsdzeD-DdVcniSdppVR5dLCsQACWVoAAsbJCUuF0o4C6eTMcDYE',
                2: 'CAACAgIAAxkBAAEbJLxm4JsUbqIIEcjr0sCkoL_0HSBJVwACk2wAAiidCUs6ctQSO0_V4TYE',
                3: 'CAACAgIAAxkBAAEbJLpm4JrhRnSnzWKEjzS1ns5-92WtBQACHWAAAufpCEui5j9ZnkiRGzYE'
            },
            'male': {
                1: 'CAACAgIAAxkBAAEbJMRm4Js_Vb_elCWiP6ks-4bQ6IuDAwACHF4AAg0mAUvffInkZRNEhzYE',
                2: 'CAACAgIAAxkBAAEbJMJm4Js9eVFtyGXhaRM4ZrtC27PchwACc2UAAqiICUvXKfdVzBNW2TYE',
                3: 'CAACAgIAAxkBAAEbJMBm4JspIE7v5E3rfycp--4le3krRwACbF0AAo1NCUsic1eiPK_GDzYE'
            }
        },
        'character_lvls_price': {
            1: 0,
            2: 550,
            3: 1100
        },
        'character_lvls_reputation': {
            1: 100,
            2: 300,
            3: 500
        },
        'max_character_lvl': '%(memo_ico)s Максимальный уровень школьника достигнут!' % \
            {'memo_ico': OtherIco.memo},
        'lvlup_successful': '👜 Оо что это? Новая униформа вашего(ей) школьника(цы) куплена!\n\n<b>+{} репутации</b>',
        'not_enough_stellar_jade': '✨ Недостаточно звездного нефрита, для покупки новой униформы нужно иметь {} нефрита',
        'not_enough_currency_item': '{} Для улучшения школьного предмета «{}», вам нужно {}',
        'backpack': tw.dedent("""
            <b>🎒 Инвентарь вашего рюкзака</b>
            
            {} До нового предмета: <i>{}%</i>
            💠 Примогемы: <i>{}</i>
            
            <blockquote>{}, пожалуйста, умеренно распределяйте свои ресурсы для более быстрой прокачки</blockquote>
            
            Выберите отсек рюкзака
            """),
        'backpack_part': tw.dedent("""
            <b>🎒 Инвентарь вашего рюкзака</b>
            
            Предметы:
            <blockquote>
            {}
            </blockquote>
            
            {} Опыта до нового предмета: <i>{}%</i>
            {} Стоимость нового уровня предмета <b>{}</b>
            Отсек <b>{}</b>
            """),
        'backpack_items_emoji': {
            'pen': '🖊',
            'diary': '📜',
            'textbook': '📚',
            'notebook': '📔',
            'lunch': '🍔',

            'pencil': '✏️',
            'eraser': '🧽',
            'ruler': '📏',
            'felt_tip_pen': '🖍',
            'marker': '✒️',
            'satin': '🗺',

            'globe': '🌍',
            'compass': '🧭',
            'laptop': '💻',
            'school_key': '🗝',
        },
        'backpack_items_en2ru': {
            'pencil': 'карандаши',
            'diary': 'дневники',
            'textbook': 'книжки',
            'notebook': 'тетради',
            'lunch': 'обед',

            'pen': 'ручка',
            'eraser': 'ластик',
            'ruler': 'линейка',
            'felt_tip_pen': 'фломастеры',
            'marker': 'маркер',
            'satin': 'атлас',

            'globe': 'глобус',
            'compass': 'компас',
            'laptop': 'ноутбук',
            'school_key': 'ключи от школы',
        },
        'backpack_items_part': {
            1: ['pencil', 'diary', 'textbook', 'notebook', 'lunch'],
            2: ['pen', 'eraser', 'ruler', 'felt_tip_pen', 'marker', 'satin'],
            3: ['laptop', 'school_key', 'compass', 'globe']
        }
    },
    'promo_code': {
        'does_not_exist': '%(memo_ico)s К сожалению промокод <i><b>«{}»</b></i> уже активирован или недействителен' \
            % {'memo_ico': OtherIco.memo},
        'stellar_jade': tw.dedent("""
            %(gift_ico)s <b>Поздравляем!</b> Вы активировали промокод <i><b>«{}»</b></i>
            
            <blockquote>%(stellar_jade_ico)s Получено <b>+{} сияющих нефритов</b></blockquote>
            """) % {'gift_ico': OtherIco.gift, 'stellar_jade_ico': BagIco.stellar_jade},
        'primogem': tw.dedent("""
            %(gift_ico)s <b>Поздравляем!</b> Вы активировали промокод <i><b>«{}»</b></i>
            
            <blockquote>%(primogem_ico)s Получено <b>+{} небесных примогемов</b></blockquote>
            """) % {'gift_ico': OtherIco.gift, 'primogem_ico': BagIco.primogem},
        'show_promo_list': tw.dedent("""
            <b>%(gift_ico)s Список доступных промокодов</b>
            
            {}
            """) % {'gift_ico': OtherIco.gift},
        
        'already_use': '%(gift_ico)s Промокод можно активировать только один раз' % {'gift_ico': OtherIco.gift}
    },
    'missions': {
        'show_daily_list': tw.dedent("""
            <b>⭐️ Ежедневные задания</b>
            
            {}
            
            ⌈ {} ⌋
            """)
    }
}
