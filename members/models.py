from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator

carrier_validator = RegexValidator(
    regex=r'^/[A-Z0-9.+\-]{7}$',   # 允許前綴「\」或「/」，後面 7 碼英數或 . + -
    message='發票載具號碼格式需為 \\XXXXXXX（前置反斜線加 7 碼英數）。'
)

class Member(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    barcode_token = models.CharField(max_length=64, unique=True, editable=False)
    points = models.IntegerField(default=0)
    birthday = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    carrier_code = models.CharField(
        max_length=8,               # 1 個斜線 + 7 碼
        blank=True,
        validators=[carrier_validator],
        help_text='格式：\\XXXXXXX 或 /XXXXXXX'
    )

    # 預留給 LINE Login
    line_user_id = models.CharField(max_length=64, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        if not self.barcode_token:
            self.barcode_token = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} ({self.points} pt)'

class PointTransaction(models.Model):
    EARN = 'EARN'
    ADJUST = 'ADJUST'
    TYPES = [(EARN, 'Earn'), (ADJUST, 'Adjust')]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='txns')
    txn_type = models.CharField(max_length=10, choices=TYPES)
    amount = models.IntegerField()   # 正數加點、負數扣點
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.txn_type} {self.amount} to {self.member_id} @ {self.created_at}'

    @property
    def formatted_note(self) -> str:
        # 避免循環 import：放在方法內
        from .utils import get_loyalty_config
        cfg = get_loyalty_config()

        if self.amount >= 0:
            # 反推概算消費金額（以目前規則估算）
            if cfg.earn_points_per_unit > 0:
                money = (self.amount // cfg.earn_points_per_unit) * cfg.earn_spend_unit
            else:
                money = 0
            return f"消費{money}元"
        else:
            return f"折抵{abs(self.amount) * cfg.redeem_value_per_point}元"

class LoyaltyConfig(models.Model):
    # 每 earn_spend_unit 元 可得 earn_points_per_unit 點（預設：100 元 = 1 點）
    earn_spend_unit = models.PositiveIntegerField(default=100)
    earn_points_per_unit = models.PositiveIntegerField(default=1)

    # 1 點可以折抵多少元（預設：1 點 = 1 元）
    redeem_value_per_point = models.PositiveIntegerField(default=1)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "點數規則設定"
        verbose_name_plural = "點數規則設定"

    def __str__(self):
        return f"每 {self.earn_spend_unit} 元 → {self.earn_points_per_unit} 點；1 點 = {self.redeem_value_per_point} 元"

@receiver(post_save, sender=LoyaltyConfig)
def _clear_loyalty_cache(sender, **kwargs):
    from .utils import get_loyalty_config  # ← 放在函式裡
    get_loyalty_config.cache_clear()