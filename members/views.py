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
from django.db.models import F
from django.http import Http404
from .forms import MemberProfileForm


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

# # 條碼圖片：目前用不到
# from barcode import Code128
# from barcode.writer import ImageWriter
# from io import BytesIO

# @login_required
# def barcode_image(request):
#     if request.user.is_staff or request.user.is_superuser:
#         raise PermissionDenied  # 店員不該有條碼
#     member = get_object_or_404(Member, user=request.user)
#     value = member.barcode_token
#     buf = BytesIO()
#     Code128(value, writer=ImageWriter()).write(buf, options={
#         'module_width': 0.2, 'module_height': 12, 'font_size': 10, 'text': value
#     })
#     return HttpResponse(buf.getvalue(), content_type='image/png')

# --- 店員累點頁（你之前已加 403 保護，保留即可） ---
@login_required
def scan_page(request):
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied
    return render(request, 'members/scan.html')

@login_required
def earn_points(request):
    if request.method != 'POST':
        return redirect('scan_page')

    token = request.POST.get('barcode_token', '').strip()
    try:
        amount = int(request.POST.get('amount_twd', '0'))
    except ValueError:
        messages.error(request, '金額格式錯誤')
        return redirect('scan_page')

    mode = request.POST.get('mode', 'earn')  # 'earn' or 'deduct'
    note = request.POST.get('note', '').strip()

    if amount <= 0:
        messages.error(request, '金額必須為正數')
        return redirect('scan_page')

    try:
        m = Member.objects.get(barcode_token=token)
    except Member.DoesNotExist:
        messages.error(request, '找不到會員')
        return redirect('scan_page')

    # 兌換比率自行套用：這裡示範 1 元 = 0.05 點
    pts = round(amount * 0.05)

    delta = pts if mode == 'earn' else -pts
    txn_type = PointTransaction.EARN if mode == 'earn' else PointTransaction.ADJUST

    PointTransaction.objects.create(
        member=m, txn_type=txn_type, amount=delta,
        note=note or ('扣點' if delta < 0 else '加點'),
        staff=request.user
    )

    Member.objects.filter(pk=m.pk).update(points=F('points') + delta)
    m.refresh_from_db()

    messages.success(request, f"{'加' if delta>0 else '扣'}點成功，已為您{'新增' if delta>0 else '扣除'}：{pts}點")
    return redirect('scan_page')

@login_required
def qrcode_image(request):
    if request.user.is_staff or request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    member = get_object_or_404(Member, user=request.user)
    data = member.barcode_token  # 也可改成 URL，如 f"https://your.site/m/{member.barcode_token}"
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")

@login_required
def point_history(request):
    try:
        member = request.user.member
    except Member.DoesNotExist:
        raise Http404("尚未綁定會員")

    records = (
        PointTransaction.objects
        .filter(member=member)
        .select_related('staff')         # 顯示處理人員時比較省查詢
        .order_by('-created_at')
    )
    return render(request, 'members/points.html', {'records': records})

@login_required
def profile(request):
    member = request.user.member  # 假設已建立 OneToOne

    if request.method == "POST":
        form = MemberProfileForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, "會員資料已更新")
            return redirect("profile")
        editing = True
    else:
        form = MemberProfileForm(instance=member)
        editing = False

    return render(request, "members/profile.html", {
        "member": member,
        "form": form,
        "editing": editing,
    })