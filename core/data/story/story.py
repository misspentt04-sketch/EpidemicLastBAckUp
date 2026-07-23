from core.data.icons import LabIco, InfectIco, CorpIco, OtherIco

import textwrap as tw
import yaml

with open('core/data/story/story.yml', 'r', encoding='utf-8') as f:
    story = yaml.safe_load(f)

pets = {
    'флаери': {
        'en': 'fiery',
        'element': 'огонь',
        'element_en': 'fire'
    }
}


tricks_story = {
    'start_action': story['begin']['start_action'],
    'tutorial_continue': story['begin']['tutorial_continue'],
    'tutorial_discontinue': story['begin']['tutorial_discontinue'],
    'tutorial_2': story['begin']['tutorial_2'],
    'tutorial_3': story['begin']['tutorial_3'],
    'tutorial_4': story['begin']['tutorial_4'],
    'tutorial_5': story['begin']['tutorial_5'],
    'tutorial_6': story['begin']['tutorial_6'],
    'tutorial_7': story['begin']['tutorial_7'],
    # 'give_starter_pet': story['begin']['give_starter_pet'] % {'pet_name': 'Первопроходец'}
}