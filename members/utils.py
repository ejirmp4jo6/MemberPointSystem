from functools import lru_cache
from .models import LoyaltyConfig

@lru_cache(maxsize=1)
def get_loyalty_config():
    obj = LoyaltyConfig.objects.first()
    if not obj:
        obj = LoyaltyConfig.objects.create()  # 建預設：100→1、1點=1元
    return obj