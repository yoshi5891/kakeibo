import os
import shutil
from datetime import datetime

# DBファイル
DB_FILE = "db.sqlite3"

# バックアップ保存先
BACKUP_DIR = "backups"

os.makedirs(BACKUP_DIR, exist_ok=True)

# 日時付きファイル名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_file = os.path.join(
    BACKUP_DIR,
    f"db_backup_{timestamp}.sqlite3"
)

# コピー
shutil.copy2(DB_FILE, backup_file)

print(f"Backup created: {backup_file}")