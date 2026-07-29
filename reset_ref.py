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

    # 1. Удаляем всех рефералов у этого пользователя
    await cur.execute('DELETE FROM Referrals WHERE referrer_id = %s;', (REFERRER_ID,))
    deleted_count = cur.rowcount

    # 2. Обнуляем кейсы и epicoins в лаборатории (Lab)
    await cur.execute(
        'UPDATE Lab SET epicoins = 0, case1 = 0, case2 = 0 WHERE lab_id = %s;',
        (REFERRER_ID,)
    )

    # 3. Получаем текущее состояние после сброса
    await cur.execute('SELECT epicoins, case1, case2, bio_resource FROM Lab WHERE lab_id = %s;', (REFERRER_ID,))
    lab = await cur.fetchone() or {'epicoins': 0, 'case1': 0, 'case2': 0, 'bio_resource': 0}

    print("🧹 [СБРОС ЗАВЕРШЕН]")
    print(f"   • Удалено рефералов из базы: {deleted_count}")
    print(f"   • Текущие Epicoins: {lab['epicoins']}")
    print(f"   • Текущие кейсы: Обычные (case1) = {lab['case1']} | Донатные (case2) = {lab['case2']}")
    print(f"   • Био-ресурсы: {lab['bio_resource']}")

    await cur.close()
    conn.close()

if __name__ == '__main__':
    asyncio.run(main())
