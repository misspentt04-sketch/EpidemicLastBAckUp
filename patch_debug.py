import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

debug_middleware = '''
@dp.message()
async def global_debug_logger(msg):
    print(f"📩 [GLOBAL MSG] ID={msg.from_user.id} Text={repr(msg.text)} Chat={msg.chat.type}")
'''

if 'global_debug_logger' not in code:
    code = code + "\n" + debug_middleware

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print(" Debug logger added to app.py")
