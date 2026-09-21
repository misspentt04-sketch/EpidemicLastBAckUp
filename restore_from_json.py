import json

OWNER_ID = 7972320837
JSON_PATH = "/home/ubuntu/epidemic/victims_7972320837.json"
OUT_SQL = "/home/ubuntu/epidemic/restore_7972320837.sql"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

lines = [
    "USE epidemic;",
    "START TRANSACTION;",
    f"DELETE FROM Victims WHERE victims_owner_id = {OWNER_ID};",
]

for victim_id, v in data.items():
    exp = int(v.get("exp", 0))
    date = int(v.get("date", 0))
    until = int(v.get("until", 0))
    kd = until
    lines.append(
        "INSERT INTO Victims "
        "(victims_owner_id, victim_id, victim_expire, infect_date, victim_expire_kd, "
        "victim_bio_resource_earn, pathogen_name, ss_detect, last_earn_exp) VALUES "
        f"({OWNER_ID}, {victim_id}, {until}, {date}, {kd}, {exp}, '', 0, 0);"
    )

lines.append("COMMIT;")

with open(OUT_SQL, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"OK: {len(data)} victims -> {OUT_SQL}")
