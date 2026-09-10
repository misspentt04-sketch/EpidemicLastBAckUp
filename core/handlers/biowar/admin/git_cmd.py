import subprocess
from aiogram import Router, F
from aiogram.types import Message

router = Router()

YOUR_ID = 7972320837
REPO_PATH = "/home/ubuntu/epidemic"

@router.message(F.text.lower() == "/git")
async def cmd_git(msg: Message):
    if msg.from_user.id != YOUR_ID:
        return
    
    try:
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=REPO_PATH
        )
        
        changed = status.stdout.strip()
        
        if not changed:
            await msg.reply("✅ Нет изменений для коммита!")
            return
        
        files = []
        for line in changed.split("\n"):
            if line.strip():
                filename = line.strip().split(maxsplit=1)[-1]
                files.append(filename)
        
        git_commands = "git add " + " ".join(files) + "\n"
        git_commands += 'git commit -m "update: auto commit"\n'
        git_commands += "git push origin main"
        
        await msg.reply(
            f"📦 <b>Изменённые файлы:</b>\n"
            f"<blockquote>{changed}</blockquote>\n\n"
            f"📋 <b>Команды:</b>\n"
            f"<blockquote>{git_commands}</blockquote>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await msg.reply(f"❌ Ошибка: {e}")


@router.message(F.text.lower() == "/git push")
async def cmd_git_push(msg: Message):
    if msg.from_user.id != YOUR_ID:
        return

    try:
        subprocess.run(["git", "add", "."], capture_output=True, text=True, cwd=REPO_PATH)

        commit = subprocess.run(
            ["git", "commit", "-m", "update: auto commit"],
            capture_output=True, text=True, cwd=REPO_PATH
        )

        push = subprocess.run(
            ["git", "push", "origin", "main"],
            capture_output=True, text=True, cwd=REPO_PATH
        )

        result = f"Commit:\n{commit.stdout}\n\nPush:\n{push.stdout or push.stderr}"

        await msg.reply(
            f"✅ <b>Git push выполнен!</b>\n\n"
            f"<blockquote>{result[-1000:]}</blockquote>",
            parse_mode="HTML"
        )

    except Exception as e:
        await msg.reply(f"❌ Ошибка: {e}")
