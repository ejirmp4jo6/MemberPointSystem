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
import math
from .utils import get_loyalty_config
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import json
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest  # 你下方 line_liff_auth 有用到，現在沒匯入會 NameError
from barcode import Code128
from barcode.writer import ImageWriter
import re

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

@login_required
def scan_page(request):
    cfg = get_loyalty_config()
    return render(request, 'members/scan.html', {
        'redeem_per_point': cfg.redeem_value_per_point,
    })

@login_required
def earn_points(request):
    if request.method != 'POST':
        return redirect('scan_page')

    token = (request.POST.get('barcode_token') or '').strip()
    # 你之前有用過 amount / amount_twd 兩種 name，這裡兩個都接
    raw_amount = (request.POST.get('amount') or request.POST.get('amount_twd') or '').strip()
    mode = request.POST.get('mode', 'earn')  # 'earn' or 'deduct'
    note = (request.POST.get('note') or '').strip()

    try:
        amount = int(raw_amount)
    except ValueError:
        messages.error(request, f'金額格式錯誤：「{raw_amount}」')
        return redirect('scan_page')
    if amount <= 0:
        messages.error(request, '金額必須為正數')
        return redirect('scan_page')

    try:
        m = Member.objects.get(barcode_token=token)
    except Member.DoesNotExist:
        messages.error(request, '找不到會員')
        return redirect('scan_page')

    cfg = get_loyalty_config()
    # cfg.earn_spend_unit            # 例：100
    # cfg.earn_points_per_unit       # 例：1
    # cfg.redeem_value_per_point     # 例：1

    if mode == 'earn':
        # 每 earn_spend_unit 元 → earn_points_per_unit 點；不足單位捨去
        units = amount // cfg.earn_spend_unit
        pts = units * cfg.earn_points_per_unit

        if pts <= 0:
            messages.info(request, f"本次金額未達 {cfg.earn_spend_unit} 元門檻，未累點。")
            return redirect('scan_page')

        PointTransaction.objects.create(
            member=m,
            txn_type=PointTransaction.EARN,
            amount=pts,  # 交易 amount 存「點數變動量」
            note=note or f"消費{units * cfg.earn_spend_unit}元（{cfg.earn_spend_unit}元=+{cfg.earn_points_per_unit}點）",
            staff=request.user
        )
        Member.objects.filter(pk=m.pk).update(points=F('points') + pts)
        m.refresh_from_db()
        messages.success(request, f"加點 +{pts}，目前點數：{m.points}")
        return redirect('scan_page')

    else:  # mode == 'deduct'（折抵）
        # 想折抵 amount 元 → 所需點數 = ceil(amount / 每點折抵元)
        need_pts = math.ceil(amount / cfg.redeem_value_per_point)
        if m.points <= 0:
            messages.error(request, '會員目前沒有可用點數')
            return redirect('scan_page')

        use_pts = min(m.points, need_pts)  # 不能超過現有點數
        discount_twd = use_pts * cfg.redeem_value_per_point

        if use_pts <= 0:
            messages.error(request, '折抵金額必須 > 0')
            return redirect('scan_page')

        PointTransaction.objects.create(
            member=m,
            txn_type=PointTransaction.ADJUST,  # 你既有的扣點/調整類型
            amount=-use_pts,                   # 交易 amount 存「點數變動量」（負數）
            note=note or f"折抵{discount_twd}元（1點={cfg.redeem_value_per_point}元）",
            staff=request.user
        )
        Member.objects.filter(pk=m.pk).update(points=F('points') - use_pts)
        m.refresh_from_db()
        messages.success(request, f"成功折抵 {discount_twd} 元，扣點 -{use_pts}，剩餘點數：{m.points}")
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
    member = request.user.member
    qs = (PointTransaction.objects
          .filter(member=member)
          .order_by('-created_at')
          .only('id', 'amount', 'created_at'))  # 只取需要欄位（見下條）

    paginator = Paginator(qs, 30)          # 每頁 30 筆
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'members/points.html', {
        'page_obj': page_obj,
        'records': page_obj.object_list,   # 舊模板沿用 records
    })

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

@login_required
@require_GET
def api_member_by_token(request):
    token = (request.GET.get('token') or '').strip()
    if not token:
        return JsonResponse({'ok': False, 'error': 'empty token'}, status=400)

    try:
        m = Member.objects.only('id', 'points', 'display_name').get(barcode_token=token)
    except Member.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)

    cfg = get_loyalty_config()
    return JsonResponse({
        'ok': True,
        'display_name': m.display_name or request.user.username,
        'points': m.points,
        'redeem_value_per_point': cfg.redeem_value_per_point,
        'max_redeem_twd': m.points * cfg.redeem_value_per_point,
    })

# ========= LINE / LIFF 登入相關 =========

User = get_user_model()
LINE_VERIFY_EP = "https://api.line.me/oauth2/v2.1/verify"

def liff_entry(request):
    """
    LIFF 入口頁：前端會載入 LIFF SDK，自動做 LINE Login，拿到 id_token 後打後端 /auth/line/liff/
    """
    return render(request, "members/liff_entry.html", {"liff_id": settings.LINE_LIFF_ID})

def _verify_id_token(id_token: str):
    """
    呼叫 LINE 官方 verify 端點，驗證 id_token，成功會回 payload（含 sub/name/picture/email）
    """
    try:
        r = requests.post(LINE_VERIFY_EP, data={
            "id_token": id_token,
            "client_id": settings.LINE_LOGIN_CHANNEL_ID,
        }, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except requests.RequestException:
        return None

@csrf_exempt  # 若前端沒帶 CSRF token，開發期先豁免；上線可改為更嚴謹作法
def line_liff_auth(request):
    """
    前端把 LIFF 取得的 id_token 傳進來：
    1) 驗證 id_token → 取出 line_user_id（payload['sub']）
    2) 綁定/建立本地 Member(User) 檔
    3) login() 成功後回應 next_url（首登或資料不完整 → /members/profile/；否則 /members/dashboard/）
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "bad_request"}, status=400)

    id_token = data.get("id_token")
    display_name = (data.get("display_name") or "").strip()
    picture_url = (data.get("picture_url") or "").strip()

    payload = _verify_id_token(id_token)
    if not payload:
        return JsonResponse({"error": "invalid_token"}, status=401)

    line_user_id = payload.get("sub")  # LINE 使用者唯一識別碼
    email = payload.get("email")  # 若 scope 有 email

    # 看看是否已經綁過
    member = Member.objects.filter(line_user_id=line_user_id).select_related("user").first()
    first_login = False

    if member:
        user = member.user
        # 可選：同步暱稱/頭像（依你的欄位命名調整）
        if display_name and member.display_name != display_name:
            member.display_name = display_name
        # 若你的 Member 有 avatar 欄位可在此更新
        member.save()
    else:
        # 沒綁過 → 建 User + Member
        username = f"line_{line_user_id[:20]}"
        user = User.objects.create_user(username=username, email=email or "")
        member = Member.objects.create(
            user=user,
            line_user_id=line_user_id,
            display_name=display_name
        )
        first_login = True

    # 建立 Django session
    login(request, user)

    # 判斷是否導向個資頁（你有 MemberProfileForm；這裡用「缺 phone 或首次登入」作為未完成個資的判斷）
    phone = getattr(member, "phone", "")  # 你的 Member 若無 phone 欄位，不會出錯
    if first_login or not (member.display_name and phone):
        next_url = "/members/profile/"
    else:
        next_url = "/members/dashboard/"

    return JsonResponse({"ok": True, "next_url": next_url})

def line_oauth_callback(request):
    """
    外部瀏覽器用的 OAuth code flow callback（目前先不用，避免 404，回首頁即可）
    """
    return redirect('/')

CARRIER_RE = re.compile(r"^/[A-Z0-9\.\+\-]{7}$")

@login_required
def carrier_barcode_image(request):
    m = get_object_or_404(Member, user=request.user)
    code = (getattr(m, "carrier_code", "") or "").strip().upper()

    if not CARRIER_RE.match(code):   # 這裡只接受 / 開頭
        raise Http404("no or invalid carrier code")

    buf = BytesIO()
    Code128(code, writer=ImageWriter()).write(buf, {
        "module_width": 0.4, "module_height": 28.0,
        "quiet_zone": 3.0, "font_size": 0, "text_distance": 1.0,
    })
    return HttpResponse(buf.getvalue(), content_type="image/png")
