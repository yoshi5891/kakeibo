import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime

class Command(BaseCommand):
    help = "Backup SQLite database"

    def handle(self, *args, **kwargs):
        db_path = settings.BASE_DIR / "db.sqlite3"
        backup_dir = settings.BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"db_backup_{timestamp}.sqlite3"

        shutil.copy(db_path, backup_file)

        self.stdout.write(self.style.SUCCESS(f"Backup created: {backup_file}"))
