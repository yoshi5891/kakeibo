#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kakeibo_project.settings")

    # --- migrate を自動実行 ---
    from django.core.management import call_command
    try:
        call_command('migrate')
        print("✅ Migration executed successfully.")
    except Exception as e:
        print("⚠️ Migration error:", e)

    # --- Django コマンド実行 ---
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
