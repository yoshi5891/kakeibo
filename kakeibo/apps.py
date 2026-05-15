from django.apps import AppConfig


class KakeiboConfig(AppConfig):
    name = "kakeibo"

def ready(self):
    import kakeibo.signals
