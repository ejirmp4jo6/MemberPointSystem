// static/js/scan_redeem_hint.js
document.addEventListener('DOMContentLoaded', () => {
  const tokenInput   = document.querySelector('input[name="barcode_token"]');
  const hint         = document.getElementById('deduct-hint');
  const btnAll       = document.getElementById('btn-redeem-all');
  const amountInput  = document.getElementById('amount-input');
  const deductRadio  = document.getElementById('mode-deduct');
  const earnRadio    = document.getElementById('mode-earn');
  const redeemPer    = Number(document.getElementById('redeem-per-point')?.value || 1);

  let currentMaxTwd = 0;

  async function fetchMember() {
    const token = (tokenInput?.value || '').trim();
    if (!token) {
      hint.textContent = '本次可折抵上限：—';
      btnAll.disabled = true;
      currentMaxTwd = 0;
      return;
    }
    try {
      const resp = await fetch(`/members/api/member_by_token/?token=${encodeURIComponent(token)}`);
      if (!resp.ok) throw new Error('not ok');
      const data = await resp.json();
      currentMaxTwd = Number(data.max_redeem_twd || 0);
      hint.textContent = `本次可折抵上限：${currentMaxTwd} 元（${data.points} 點）`;
      btnAll.disabled = currentMaxTwd <= 0;
    } catch (e) {
      hint.textContent = '找不到會員或卡號無效';
      btnAll.disabled = true;
      currentMaxTwd = 0;
    }
  }

  // 一鍵折抵：切到「扣點」，把金額填成上限
  btnAll?.addEventListener('click', () => {
    if (currentMaxTwd <= 0) return;
    if (deductRadio) deductRadio.checked = true;
    amountInput.value = currentMaxTwd;
    amountInput.focus();
    amountInput.select?.();
    // 若你的 scan_typeSwitch.js 會改 label，可手動觸發 change
    earnRadio?.dispatchEvent(new Event('change'));
    deductRadio?.dispatchEvent(new Event('change'));
  });

  // 當卡號輸入變化（掃描或貼上）時，自動查詢上限
  if (tokenInput) {
    const debounce = (fn, wait=350) => {
      let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
    };
    tokenInput.addEventListener('input', debounce(fetchMember));
    tokenInput.addEventListener('change', fetchMember);
  }

  // 頁面一載入先試著抓一次（若欄位已有值）
  fetchMember();
});
