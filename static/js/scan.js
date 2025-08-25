// static/js/scan.js  或 members/static/members/js/scan.js
document.addEventListener('DOMContentLoaded', function () {
  const tokenInput  = document.querySelector('input[name="barcode_token"]');
  const amountInput = document.getElementById('amount-input');
  const openBtn     = document.getElementById('open-scanner');   // 右邊的相機按鈕
  const qrBox       = document.getElementById('qr-box');         // 你頁面已有的掃描區
  const containerId = 'qr-reader';                                // 你頁面已有的容器
  let scanner = null;
  let running = false;

  function onDecoded(text){
    if (!tokenInput) return;
    const token = (text || '').trim(); // 去掉換行/空白
    tokenInput.value = token;
    // 讓監聽 token 變化的程式（查可折抵上限）跑起來
    tokenInput.dispatchEvent(new Event('input',  { bubbles: true }));
    tokenInput.dispatchEvent(new Event('change', { bubbles: true }));
    if (navigator.vibrate) navigator.vibrate(80);
    stopScanner();
    if (amountInput) amountInput.focus();
  }

  async function startScanner(){
    if (running) return;
    // 確保掃描區顯示
    if (qrBox) qrBox.style.display = 'block';
    if (!scanner) scanner = new Html5Qrcode(containerId);
    try {
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 }, rememberLastUsedCamera: true },
        (decoded) => { onDecoded(decoded); },
        () => {} // onScanFailure: 忽略
      );
      running = true;
    } catch (e) {
      console.error('[scan] start error:', e);
      alert('無法啟動相機。請以 HTTPS（ngrok/Cloudflare）開啟並允許相機權限。');
      stopScanner();
    }
  }

  async function stopScanner(){
    if (!scanner) return;
    try { await scanner.stop(); } catch(_) {}
    try { await scanner.clear(); } catch(_) {}
    running = false;
  }

  // 點相機按鈕 → 啟動掃描
  if (openBtn) openBtn.addEventListener('click', startScanner);

  // 離開頁面時關閉相機
  window.addEventListener('beforeunload', stopScanner);

});
