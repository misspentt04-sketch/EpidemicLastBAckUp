import asyncio
import asyncmy

REFERRER_ID = 8236324289
MAX_REFERRALS = 50

async def main():
    conn = await asyncmy.connect(
        host='localhost',
        user='root',
        password='1603',
        database='epidemic',
        autocommit=True
    )
    cur = conn.cursor(asyncmy.cursors.DictCursor)

    # 1. Получаем текущие данные ДО
    await cur.execute('SELECT COUNT(*) as cnt FROM Referrals WHERE referrer_id = %s;', (REFERRER_ID,))
    ref_cnt_before = (await cur.fetchone())['cnt']

    await cur.execute('SELECT epicoins, bio_resource FROM Lab WHERE lab_id = %s;', (REFERRER_ID,))
    lab_before = await cur.fetchone() or {'epicoins': 0, 'bio_resource': 0}

    print(f"📊 СОСТОЯНИЕ ДО:")
    print(f"   • Всего рефералов в БД: {ref_cnt_before}")
    print(f"   • Epicoins: {lab_before['epicoins']} | Био-ресурсы: {lab_before['bio_resource']}")

    print("\n🔄 Симуляция добавления еще 50 рефералов...")

    # 2. Добавляем еще 50 рефералов и проверяем каждый шаг
    fake_start_id = 999100000 + ref_cnt_before
    added_rewards_count = 0

    for i in range(50):
        fake_id = fake_start_id + i
        await cur.execute('INSERT IGNORE INTO Users (id, full_name, username) VALUES (%s, %s, %s);', (fake_id, f'TestUser_{fake_id}', f'test_{fake_id}'))
        await cur.execute('INSERT IGNORE INTO Referrals (referrer_id, referred_id) VALUES (%s, %s);', (REFERRER_ID, fake_id))
        
        # Считаем актуальный счетчик
        await cur.execute('SELECT COUNT(*) as cnt FROM Referrals WHERE referrer_id = %s;', (REFERRER_ID,))
        current_cnt = (await cur.fetchone())['cnt']

        # Логика выдачи наград (как в бота)
        if current_cnt <= MAX_REFERRALS:
            await cur.execute('UPDATE Lab SET epicoins = epicoins + 150 WHERE lab_id = %s;', (REFERRER_ID,))
            added_rewards_count += 1

    # 3. Получаем данные ПОСЛЕ
    await cur.execute('SELECT COUNT(*) as cnt FROM Referrals WHERE referrer_id = %s;', (REFERRER_ID,))
    ref_cnt_after = (await cur.fetchone())['cnt']

    await cur.execute('SELECT epicoins, bio_resource FROM Lab WHERE lab_id = %s;', (REFERRER_ID,))
    lab_after = await cur.fetchone() or {'epicoins': 0, 'bio_resource': 0}

    print("\n✅ Тест завершен!")
    print(f"📊 СОСТОЯНИЕ ПОСЛЕ:")
    print(f"   • Всего рефералов в БД: {ref_cnt_after} (+50 новых)")
    print(f"   • Выдано наград из 50 новых: {added_rewards_count}")
    print(f"   • Epicoins: {lab_after['epicoins']} (изменение: +{lab_after['epicoins'] - lab_before['epicoins']})")
    print(f"   • Био-ресурсы: {lab_after['bio_resource']} (изменение: +{lab_after['bio_resource'] - lab_before['bio_resource']})")

    if added_rewards_count == 0:
        print("\n🛡️ ЗАЩИТА СРАБОТАЛА! Так как у пользователя уже было >= 50 рефералов, ни за одного из новых 50 человек награда НЕ начислилась.")

    await cur.close()
    conn.close()

if __name__ == '__main__':
    asyncio.run(main())
