# members/views.py
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from .models import Member, PointTransaction
import qrcode
from io import BytesIO


def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            # 店員或超管：不建立 Member，直接導向累點頁
            if user.is_staff or user.is_superuser:
                return redirect('scan_page')
            # 一般會員：確保有 Member 再進 dashboard
            Member.objects.get_or_create(user=user)
            return redirect('dashboard')
        messages.error(request, '帳號或密碼錯誤')
    return render(request, 'members/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    # 店員帳號沒有會員功能 → 給友善提示或直接導去累點頁
    if request.user.is_staff or request.user.is_superuser:
        # 你可以改成 render 出一個提示頁；這裡直接導去累點頁最直覺
        return redirect('scan_page')

    member, _ = Member.objects.get_or_create(user=request.user)
    txns = member.txns.all()[:10]
    return render(request, 'members/dashboard.html', {'member': member, 'txns': txns})

# 條碼圖片：只有一般會員才有
from barcode import Code128
from barcode.writer import ImageWriter
from io import BytesIO

@login_required
def barcode_image(request):
    if request.user.is_staff or request.user.is_superuser:
        raise PermissionDenied  # 店員不該有條碼
    member = get_object_or_404(Member, user=request.user)
    value = member.barcode_token
    buf = BytesIO()
    Code128(value, writer=ImageWriter()).write(buf, options={
        'module_width': 0.2, 'module_height': 12, 'font_size': 10, 'text': value
    })
    return HttpResponse(buf.getvalue(), content_type='image/png')

# --- 店員累點頁（你之前已加 403 保護，保留即可） ---
@login_required
def scan_page(request):
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied
    return render(request, 'members/scan.html')

@login_required
def earn_points(request):
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied
    if request.method != 'POST':
        return HttpResponseForbidden('POST only')
    token = (request.POST.get('barcode_token') or '').strip()
    amount_twd = int(request.POST.get('amount_twd') or 0)
    note = request.POST.get('note', '')
    points = amount_twd // 20

    try:
        member = Member.objects.get(barcode_token=token)
    except Member.DoesNotExist:
        messages.error(request, '找不到此會員')
        return redirect('scan_page')

    PointTransaction.objects.create(
        member=member, txn_type=PointTransaction.EARN, amount=points,
        note=note or f'消費 NT${amount_twd}', staff=request.user
    )
    member.points += points
    member.save()
    messages.success(request, f'已為 {member.user.username} 累積 {points} 點（NT${amount_twd}）')
    return redirect('scan_page')

