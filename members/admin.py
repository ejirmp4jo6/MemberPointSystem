from django.contrib import admin
from .models import Member, PointTransaction, LoyaltyConfig

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id','user','display_name','phone','points','barcode_token','created_at')
    search_fields = ('user__username','display_name','phone','barcode_token')

@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('id','member','txn_type','amount','note','created_at','staff')
    search_fields = ('member__user__username','note')

@admin.register(LoyaltyConfig)
class LoyaltyConfigAdmin(admin.ModelAdmin):
    list_display = ("earn_spend_unit", "earn_points_per_unit", "redeem_value_per_point", "updated_at")