from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid

class Member(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    barcode_token = models.CharField(max_length=64, unique=True, editable=False)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

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
