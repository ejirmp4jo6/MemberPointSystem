from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('barcode/', views.barcode_image, name='barcode_image'),
    path('scan/', views.scan_page, name='scan_page'),          # 店員掃描頁（相機或手動輸入）
    path('earn/', views.earn_points, name='earn_points'),      # 店員提交累點
    path('qr/', views.qrcode_image, name='qrcode_image'),
    path('points/', views.point_history, name='point_history'),  # 新增
    path('profile/', views.profile, name='profile'),
    path('api/member_by_token/', views.api_member_by_token, name='api_member_by_token'),
    path('liff-entry/', views.liff_entry, name='liff_entry'),
    path('auth/line/liff/', views.line_liff_auth, name='line_liff_auth'),
    path('line/callback/', views.line_oauth_callback, name='line_oauth_callback'),
]