import os, re

# Восстанавливаем SQL-запросы в файлах к исходным
for root, dirs, files in os.walk('/home/ubuntu/epidemic'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Убираем жесткие условия WHERE из SQL
            cleaned = re.sub(r'AND id NOT IN \(8236324289, 7754333998, 7972320837\)', '', content)
            cleaned = re.sub(r'AND user_id NOT IN \(8236324289, 7754333998, 7972320837\)', '', cleaned)
            cleaned = re.sub(r'WHERE id NOT IN \(8236324289, 7754333998, 7972320837\)', '', cleaned)
            cleaned = re.sub(r'WHERE user_id NOT IN \(8236324289, 7754333998, 7972320837\)', '', cleaned)
            
            if cleaned != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(cleaned)

print("SQL-запросы очищены.")
