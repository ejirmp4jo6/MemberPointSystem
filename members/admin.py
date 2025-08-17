from django.contrib import admin
from .models import Member, PointTransaction

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id','user','display_name','phone','points','barcode_token','created_at')
    search_fields = ('user__username','display_name','phone','barcode_token')

@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ('id','member','txn_type','amount','note','created_at','staff')
    search_fields = ('member__user__username','note')
