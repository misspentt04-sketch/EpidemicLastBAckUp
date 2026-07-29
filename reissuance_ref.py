import asyncio
import asyncmy

REFERRER_ID = 8236324289

async def main():
    conn = await asyncmy.connect(
        host='localhost',
        user='root',
        password='1603',
        database='epidemic',
        autocommit=True
    )
    cur = conn.cursor(asyncmy.cursors.DictCursor)

    # 1. Удаляем все реферальные связи данного игрока
    await cur.execute('DELETE FROM Referrals WHERE referrer_id = %s;', (REFERRER_ID,))
    deleted_refs = cur.rowcount
    print(f"🧹 Сброшено рефералов у игрока {REFERRER_ID}: {deleted_refs}")

    # 2. Пересоздаем 50 чистых рефералов и начисляем награды по правильной логике
    fake_start_id = 900000000
    total_epicoins = 0
    total_case1 = 0
    total_case2 = 0

    for i in range(1, 51):
        fake_id = fake_start_id + i
        
        # Создаем запись пользователя и реферала
        await cur.execute('INSERT IGNORE INTO Users (id, full_name, username) VALUES (%s, %s, %s);', (fake_id, f'RefUser_{i}', f'ref_{i}'))
        await cur.execute('INSERT IGNORE INTO Referrals (referrer_id, referred_id) VALUES (%s, %s);', (REFERRER_ID, fake_id))

        # Награда за реферала: +150 Epicoins
        total_epicoins += 150

        # Начисление кейсов по вехам
        if i in [5, 10, 35, 40]:
            total_case1 += 1
        elif i == 15:
            total_case1 += 2
        elif i in [30, 50]:
            total_case2 += 1

    # 3. Обновляем инвентарь игрока в таблице Lab
    await cur.execute(
        'UPDATE Lab SET epicoins = %s, case1 = %s, case2 = %s WHERE lab_id = %s;',
        (total_epicoins, total_case1, total_case2, REFERRER_ID)
    )

    # 4. Проверяем результаты в БД
    await cur.execute('SELECT COUNT(*) as cnt FROM Referrals WHERE referrer_id = %s;', (REFERRER_ID,))
    ref_count = (await cur.fetchone())['cnt']

    await cur.execute('SELECT epicoins, case1, case2, bio_resource FROM Lab WHERE lab_id = %s;', (REFERRER_ID,))
    lab = await cur.fetchone() or {'epicoins': 0, 'case1': 0, 'case2': 0, 'bio_resource': 0}

    print("\n✅ [УСПЕШНО ПЕРЕНАЧИСЛЕНО]")
    print(f"   • Игрок: {REFERRER_ID}")
    print(f"   • Итого рефералов: {ref_count}/50")
    print(f"   • Начислено Epicoins: {lab['epicoins']} (по 150 за каждого)")
    print(f"   • Выдано обычных кейсов (case1): {lab['case1']} шт. (за 5, 10, 15, 35, 40 реф.)")
    print(f"   • Выдано донатных кейсов (case2): {lab['case2']} шт. (за 30 и 50 реф.)")
    print(f"   • Био-ресурсы: {lab['bio_resource']} (не начислялись)")

    await cur.close()
    conn.close()

if __name__ == '__main__':
    asyncio.run(main())
