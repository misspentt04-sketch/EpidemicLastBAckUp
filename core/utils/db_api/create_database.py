from asyncmy import Pool
from asyncmy.cursors import DictCursor

from core.settings import settings

async def db_settings_up(pool: Pool):
    
    ### Main ###
    
    users_table = (
        'CREATE TABLE IF NOT EXISTS Users('
        ' id BIGINT(16) NOT NULL PRIMARY KEY,'
        ' full_name VARCHAR(128) NOT NULL,'
        ' username VARCHAR(32) DEFAULT NULL,'
        ' INDEX (id)'
        ');'
    )
    
    chats_table = (
        'CREATE TABLE IF NOT EXISTS Chat('
        ' id BIGINT NOT NULL AUTO_INCREMENT,'
        ' chat_id BIGINT(16) NOT NULL,'
        ' title VARCHAR(128) NOT NULL,'
        ' user_id BIGINT(16) NOT NULL,'
        ' is_private TINYINT(1) NOT NULL DEFAULT 0,'
        ' PRIMARY KEY (id),'
        # ' FOREIGN KEY (user_id) REFERENCES Users(id),'
        ' INDEX (chat_id, user_id)'
        ');'
    )
    
    ### BioWar ###
    
    lab_table = (
        'CREATE TABLE IF NOT EXISTS Lab('
        ' lab_id BIGINT(16) NOT NULL,'
        ' lab_name VARCHAR(128) NULL,'
        ' lab_time_created BIGINT(10) NOT NULL,'
        ' customization_emoji VARCHAR(20) NULL,'
        ' pathogen_name VARCHAR(48) NULL,'
        ' pathogens INT(4) NOT NULL DEFAULT 4,'
        ' ready_pathogens INT(4) NOT NULL DEFAULT 4,'
        ' science TINYINT(4) NOT NULL DEFAULT 1,'
        ' science_time BIGINT(10) DEFAULT NULL,'
        ' infect INT(4) NOT NULL DEFAULT 1,'
        ' immunity INT(4) NOT NULL DEFAULT 1,'
        ' lethality INT(4) NOT NULL DEFAULT 1,'
        ' security_service INT(4) NOT NULL DEFAULT 1,'
        ' bio_experience BIGINT(14) NOT NULL DEFAULT 0,'
        ' bio_resource BIGINT(14) NOT NULL DEFAULT 0,'
        ' fever BIGINT(10) DEFAULT NULL,'
        ' fever_pathogen_name VARCHAR(48) NULL,'
        ' victims_food BIGINT(32) NOT NULL DEFAULT 0,'
        ' chat_setup_virus BIGINT(16) NULL,'
        ' lab_dossier TINYINT(1) NOT NULL DEFAULT 1,'
        ' pet_boost_exp BIGINT(14) NOT NULL DEFAULT 0,'
        ' PRIMARY KEY (lab_id),'
        ' FOREIGN KEY (lab_id) REFERENCES Users(id),'
        # ' FOREIGN KEY (lab_id) REFERENCES Chat(user_id),'
        ' INDEX (lab_id)'
        ');'
    )
    
    pets_table = (
        'CREATE TABLE IF NOT EXISTS Pets('
        ' id BIGINT(16) NOT NULL AUTO_INCREMENT,'
        ' owner_pet_id BIGINT(16) NOT NULL,'
        ' pet_name VARCHAR(32) NOT NULL,'
        ' element VARCHAR(32) NOT NULL,'
        ' pet_the_pet_time BIGINT(10) NOT NULL DEFAULT 0,'
        ' current_pet VARCHAR(120) NOT NULL DEFAULT "первопроходец",'
        ' happy TINYINT(3) NOT NULL DEFAULT 100,'
        ' PRIMARY KEY (id),'
        ' FOREIGN KEY (owner_pet_id) REFERENCES Lab(lab_id)'
        ');'
    )
    
    corporations_table = (
        'CREATE TABLE IF NOT EXISTS Corporation('
        ' leader_id BIGINT(16) NOT NULL,'
        ' name VARCHAR(128) NOT NULL,'
        ' members TINYINT(3) NOT NULL,'
        ' invite_list BIGINT(16) NOT NULL DEFAULT 0,'
        ' bio_experience BIGINT(24) NOT NULL,'
        ' infected BIGINT(16) NOT NULL,'
        ' invitation_code VARCHAR(6) NOT NULL,'
        ' corporation_dossier TINYINT(1) NOT NULL DEFAULT 1,'
        ' PRIMARY KEY (leader_id, invitation_code),'
        ' FOREIGN KEY (leader_id) REFERENCES Users(id),'
        ' INDEX (invitation_code)'
        ');'
    )
    
    corporation_members_table = (
        'CREATE TABLE IF NOT EXISTS CorporationMembers('
        ' id BIGINT NOT NULL AUTO_INCREMENT,'
        ' corporation_code VARCHAR(6) NOT NULL,'
        ' member_id BIGINT(16) NOT NULL,'
        ' name VARCHAR(128) NOT NULL,'
        ' bio_experience BIGINT(14) NOT NULL,'
        ' infected INT(9) NOT NULL,'
        ' is_admin TINYINT(1) DEFAULT 0,'
        ' PRIMARY KEY (id, corporation_code),'
        ' FOREIGN KEY (corporation_code) REFERENCES Corporation(invitation_code),'
        ' INDEX (member_id, corporation_code)'
        ');'
    )
    
    corporation_invite_list_table = (
        'CREATE TABLE IF NOT EXISTS CorporationInviteList('
        ' id BIGINT NOT NULL AUTO_INCREMENT,'
        ' invite_user_id BIGINT(16) NOT NULL,'
        ' corporation_code VARCHAR(6) NOT NULL,'
        ' name VARCHAR(128) NOT NULL,'
        ' bio_experience BIGINT(14) NOT NULL,'
        ' PRIMARY KEY (id, corporation_code),'
        ' FOREIGN KEY (corporation_code) REFERENCES Corporation(invitation_code),'
        ' INDEX (corporation_code, invite_user_id)'
        ');'
    )
    
    victims_table = (
        'CREATE TABLE IF NOT EXISTS Victims('
        ' id BIGINT NOT NULL AUTO_INCREMENT,'
        ' victims_owner_id BIGINT(16) NOT NULL,'
        ' victim_id BIGINT(16) NOT NULL,'
        ' victim_expire BIGINT(10) NOT NULL,'
        ' infect_date BIGINT(10) NOT NULL,'
        ' victim_expire_kd BIGINT(10) NOT NULL,'
        ' victim_bio_resource_earn BIGINT(14) NOT NULL,'
        ' pathogen_name VARCHAR(48) NOT NULL,'
        ' ss_detect TINYINT(1) NOT NULL,'
        ' UNIQUE(victims_owner_id, victim_id),'
        ' PRIMARY KEY (id),'
        ' FOREIGN KEY (victims_owner_id) REFERENCES Users(id),'
        ' INDEX (victims_owner_id, victim_id)'
        ');'
    )
    
    bag_table = (
        'CREATE TABLE IF NOT EXISTS Bag('
        ' id BIGINT(16) NOT NULL,'
        ' primogem BIGINT(16) NOT NULL DEFAULT 0,'
        ' stellar_jade BIGINT(16) NOT NULL DEFAULT 0,'
        ' PRIMARY KEY (id),'
        ' FOREIGN KEY (id) REFERENCES Lab(lab_id)'
        ');'
    )
    
    donate_table = (
        'CREATE TABLE IF NOT EXISTS Donate('
        ' id BIGINT NOT NULL AUTO_INCREMENT,'
        ' user_id BIGINT(16) NOT NULL,'
        ' counts SMALLINT(4) NOT NULL DEFAULT 0,'
        ' kit1 TINYINT(1) NOT NULL DEFAULT 0,'
        ' kit2 TINYINT(1) NOT NULL DEFAULT 0,'
        ' kit3 TINYINT(1) NOT NULL DEFAULT 0,'
        ' kit4 TINYINT(1) NOT NULL DEFAULT 0,'
        ' kit5 TINYINT(1) NOT NULL DEFAULT 0,'
        ' kit6 TINYINT(1) NOT NULL DEFAULT 0,'
        ' UNIQUE(user_id),'
        ' PRIMARY KEY (id),'
        ' FOREIGN KEY (user_id) REFERENCES Bag(id)'
        ');'
    )
    
    event_table = (
        'CREATE TABLE IF NOT EXISTS Event('
        ' id BIGINT(16) NOT NULL,'
        ' pathogens_used INT(4) NOT NULL DEFAULT 0,'
        ' infected INT(9) NOT NULL DEFAULT 0,'
        ' PRIMARY KEY (id),'
        ' FOREIGN KEY (id) REFERENCES Lab(lab_id)'
        ')'
    )

    event_character_table = ("""
        CREATE TABLE IF NOT EXISTS event_character(
            user_id BIGINT(16) NOT NULL,
            lvl TINYINT(1) NOT NULL,
            gender ENUM('female', 'male') NOT NULL,
            PRIMARY KEY (user_id),
            FOREIGN KEY (user_id) REFERENCES Users(id)
        );
    """)

    event_valentin_table = ("""
        CREATE TABLE IF NOT EXISTS event_valentin(
            user_id BIGINT(16) NOT NULL,
            valentin_have_count INT DEFAULT 0,
            valentin_gift_count INT DEFAULT 0,
            epilove_use_count INT DEFAULT 0,
            PRIMARY KEY (user_id),
            FOREIGN KEY (user_id) REFERENCES Users(id)
        );
    """)
    
    event_aprelki = ("""
        CREATE TABLE IF NOT EXISTS event_aprelki(
            user_id BIGINT(16) NOT NULL PRIMARY KEY,
            aprelki INT NOT NULL DEFAULT 0,
            aprelki_next_time BIGINT(10) NULL
        );
    """)

    bio_mute = (
        'CREATE TABLE IF NOT EXISTS BioMute('
        ' user_id BIGINT(16) NOT NULL,'
        ' time_expire BIGINT(10) NOT NULL,'
        ' admin BIGINT(16) NOT NULL,'
        ' reason TEXT NOT NULL,'
        ' PRIMARY KEY (user_id)'
        ');'
    )
    
    game_mute = (
        'CREATE TABLE IF NOT EXISTS GameMute('
        ' user_id BIGINT(16) NOT NULL,'
        ' time_expire BIGINT(20) NOT NULL,'
        ' admin BIGINT(16) NOT NULL,'
        ' reason TEXT NOT NULL,'
        ' PRIMARY KEY (user_id)'
        ');'
    )

    reputation_table = ("""
        CREATE TABLE IF NOT EXISTS reputation(
            user_id BIGINT(16) NOT NULL,
            score INT(5) NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id)
        );
    """)

    promocode_table = ("""
        CREATE TABLE IF NOT EXISTS promo_code(
            id BIGINT NOT NULL AUTO_INCREMENT,
            promo_code VARCHAR(60) NOT NULL,
            type VARCHAR(50) NOT NULL,
            val_count BIGINT(16) NOT NULL DEFAULT 1,
            PRIMARY KEY (id)
        );
    """)
    
    promocode_user_table = ("""
        CREATE TABLE IF NOT EXISTS promo_code_user(
            id BIGINT NOT NULL AUTO_INCREMENT,
            user_id BIGINT(16) NOT NULL,
            promo_code VARCHAR(60) NOT NULL,
            PRIMARY KEY (id)
        );
    """)

    krutki_garant_table = ("""
        CREATE TABLE IF NOT EXISTS krutki_garant(
            user_id BIGINT(16) NOT NULL,
            krutki_count INT NOT NULL DEFAULT 0,
            pet_garant_name VARCHAR(120) DEFAULT "байлу",
            PRIMARY KEY (user_id)
        );
    """)


    ### Chat Managemnt ###
    
    notes_table = (
        'CREATE TABLE IF NOT EXISTS Notes('
        ' id BIGINT NOT NULL AUTO_INCREMENT,'
        ' chat_id BIGINT(16) NOT NULL,'
        ' note_id SMALLINT NOT NULL,'
        ' title VARCHAR(64) NOT NULL,'
        ' text TEXT NOT NULL,'
        ' PRIMARY KEY (id),'
        # ' FOREIGN KEY fk_chat_id (chat_id) REFERENCES Chat(chat_id),'
        ' INDEX (chat_id, note_id, title)'
        ');'
    )

    rules_table = (
        'CREATE TABLE IF NOT EXISTS Rules('
        ' id BIGINT NOT NULL AUTO_INCREMENT,'
        ' chat_id BIGINT(16) NOT NULL,'
        ' text TEXT NOT NULL,'
        ' PRIMARY KEY (id),'
        # ' FOREIGN KEY fk_chat_id (chat_id) REFERENCES Chat(chat_id),'
        ' INDEX (chat_id),'
        ' UNIQUE (chat_id)'
        ');'
    )

    marriages_table = (
        'CREATE TABLE IF NOT EXISTS Marriages('
        ' id BIGINT(16) NOT NULL AUTO_INCREMENT,'
        ' chat_id BIGINT(16),'
        ' marry_id BIGINT(16) DEFAULT 0,'
        ' husband_id BIGINT(16),'
        ' wife_id BIGINT(16),'
        ' time_created BIGINT(10),'
        ' description VARCHAR(140),'
        ' sms_in_marriage BIGINT(18) DEFAULT 0,'
        ' marry_sticker VARCHAR(200) NOT NULL DEFAULT "CAACAgIAAxkBAAEdKpBnsPltPbpbfWK14Ju_ViL9Bg5NzAAC4V4AAj8weUmyVw5JpDtWrjYE",'
        ' PRIMARY KEY (id),'
        # ' FOREIGN KEY fk_chat_id (chat_id) REFERENCES Chat(chat_id),'
        ' INDEX (chat_id, marry_id)'
        ');'
    )

    marriges_backups_table = (
        'CREATE TABLE IF NOT EXISTS MarrigesBackups('
        ' chat_id BIGINT(16),'
        ' husband_id BIGINT(16),'
        ' wife_id BIGINT(16),'
        ' time_created BIGINT(10),'
        ' delete_add BIGINT(10),'
        ' sms_in_marriage BIGINT(18),'
        ' marry_sticker VARCHAR(200),'
        ' PRIMARY KEY (husband_id, wife_id),'
        ' INDEX (husband_id, wife_id, chat_id)'
        ');'
    )

    ship_table = (
        'CREATE TABLE IF NOT EXISTS Ship('
        ' chat_id BIGINT(16),'
        ' partner1_id BIGINT(16),'
        ' partner2_id BIGINT(16),'
        ' time_shiped BIGINT(10) NOT NULL DEFAULT 0,'
        ' PRIMARY KEY (chat_id),'
        # ' FOREIGN KEY fk_chat_id (chat_id) REFERENCES Chat(chat_id),'
        ' INDEX (chat_id)'
        ');'
    )

    admin_table = (
        'CREATE TABLE IF NOT EXISTS Admins('
        ' admin_id BIGINT(16) NOT NULL,'
        ' chat_id BIGINT(16) NOT NULL,'
        ' admin_name TEXT,'
        # ' FOREIGN KEY fk_chat_id (chat_id) REFERENCES Chat(chat_id),'
        ' INDEX (chat_id, admin_id),'
        ' UNIQUE (chat_id, admin_id)'
        ');'
    )

    chat_member_notify_table = (
        'CREATE TABLE IF NOT EXISTS ChatMemNotifications('
        'id BIGINT(6) NOT NULL AUTO_INCREMENT,'
        'chat_id BIGINT(16) NOT NULL,'
        'new_chat_member BIGINT(2),'
        'leave_chat_member BIGINT(2),'
        'up_to_admin BIGINT(2),'
        'PRIMARY KEY (id),'
        # 'FOREIGN KEY fk_chat_id (chat_id) REFERENCES Chat(chat_id),'
        'INDEX (chat_id),'
        'UNIQUE (chat_id)'
        ');'
    )

    user_chat_messages_table = ("""
        CREATE TABLE IF NOT EXISTS user_chat_messages(
            user_id BIGINT(16) NOT NULL,
            chat_id BIGINT(16) NOT NULL,
            last_message_id INT NOT NULL,
            last_message_text TEXT NULL,
            PRIMARY KEY (user_id)
        );
    """)
    
    user_nickname = ("""
        CREATE TABLE IF NOT EXISTS user_nickname(
            user_id BIGINT(16) NOT NULL,
            nickname VARCHAR(64),
            PRIMARY KEY (user_id)
        )
    """)

    
    
    tutorial_table = ("""
        CREATE TABLE IF NOT EXISTS tutorial(
            user_id BIGINT(16) NOT NULL PRIMARY KEY,
            is_tutorial_complete TINYINT(1) NOT NULL DEFAULT 0
        );
    """)

    suggestions_table = (
        'CREATE TABLE IF NOT EXISTS suggestions ('
        'id INT AUTO_INCREMENT,'
        'user_id BIGINT NOT NULL,'
        'category VARCHAR(32) NOT NULL,'
        'text TEXT NOT NULL,'
        'created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,'
        'PRIMARY KEY (id)'
        ');'
    )

    admin_status_table = (
        """
        CREATE TABLE IF NOT EXISTS admin_status(
            user_id BIGINT(16) NOT NULL PRIMARY KEY,
            last_seen BIGINT(10) NOT NULL DEFAULT 0
        );
        """
    )

    referrals_table = ('CREATE TABLE IF NOT EXISTS Referrals(id INT NOT NULL AUTO_INCREMENT, referrer_id BIGINT(16) NOT NULL, invited_id BIGINT(16) NOT NULL, PRIMARY KEY (id), UNIQUE (invited_id), INDEX (referrer_id));')

    # Service

    service_table = (
        'CREATE TABLE IF NOT EXISTS Service('
        ' id INT NOT NULL AUTO_INCREMENT,'
        ' time_give_food BIGINT(10) NOT NULL DEFAULT 0,'
        ' PRIMARY KEY (id)'
        ');'
    )
    
    tasks = [
        # BioWar
        users_table,
        chats_table,
        lab_table,
        pets_table,
        corporations_table,
        corporation_members_table,
        corporation_invite_list_table,
        victims_table,
        bag_table,
        donate_table,
        bio_mute,
        game_mute,
        reputation_table,
        event_valentin_table,
        promocode_table,
        promocode_user_table,
        krutki_garant_table,
        # Chat Managemnt
        notes_table,
        marriages_table,
        marriges_backups_table,
        rules_table,
        ship_table,
        chat_member_notify_table,
        admin_table,
        user_chat_messages_table,
        user_nickname,
        # Event
        event_table,
        event_character_table,
        event_aprelki,
        # Story
    tutorial_table,
    suggestions_table,
    admin_status_table,

        # Service
    referrals_table,
    service_table,

    ]

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            for ex in tasks:
                await cur.execute(ex)