from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('barcode/', views.barcode_image, name='barcode_image'),
    path('scan/', views.scan_page, name='scan_page'),          # 店員掃描頁（相機或手動輸入）
    path('earn/', views.earn_points, name='earn_points'),      # 店員提交累點
    path('qr/', views.qrcode_image, name='qrcode_image'),
]
