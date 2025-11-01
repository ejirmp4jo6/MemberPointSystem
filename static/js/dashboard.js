(function () {
  const tabQr   = document.getElementById('tab-qr');
  const tabBc   = document.getElementById('tab-barcode');
  const img     = document.getElementById('code-img');
  const link    = document.getElementById('download-link');
  const copyBtn = document.getElementById('copy-token');

  // 這兩個 URL、與可複製文字，請從模板塞到 data-* 內（見下方 HTML 說明）
  const qrUrl       = img?.dataset.qr || "";
  const barcodeUrl  = img?.dataset.barcode || "";   // 若使用者還沒填載具，請做成空字串
  const copyToken   = img?.dataset.token || "";
  const copyCarrier = img?.dataset.carrier || "";   // 形如 "\XXXXXXX"

  function applyActiveStyles(isQR) {
    tabQr.classList.toggle('btn-warning', isQR);
    tabQr.classList.toggle('btn-outline-secondary', !isQR);
    tabBc.classList.toggle('btn-warning', !isQR);
    tabBc.classList.toggle('btn-outline-secondary', isQR);
  }

  function setActive(type) {
    const isQR = type === 'qr';

    // 沒有載具就不讓切到 barcode，導去個資頁面補填
    if (!isQR && !barcodeUrl) {
      // 你可以換成更優雅的 modal / toast
      if (confirm('尚未設定電子發票載具，現在前往個人資料設定嗎？')) {
        // 依你的路由調整
        window.location.href = "/members/profile/";
      }
      return;
    }

    // 切換圖片來源
    const url = isQR ? qrUrl : barcodeUrl;
    if (img && url) {
      img.src = url;
      // 同步更新下載檔名與連結
      link.href = url;
      link.download = isQR ? "member_qr.png" : "invoice_barcode.png";
    }

    // 切換「複製」按鈕的目標（你也可以固定只複製 token）
    copyBtn.dataset.copy = isQR ? copyToken : copyCarrier;
    copyBtn.textContent  = isQR ? '複製會員代碼' : '複製載具號碼';

    applyActiveStyles(isQR);
  }

  tabQr?.addEventListener('click',   () => setActive('qr'));
  tabBc?.addEventListener('click',   () => setActive('barcode'));

  // 複製到剪貼簿
  copyBtn?.addEventListener('click', async () => {
    try {
      const text = copyBtn.dataset.copy || "";
      if (!text) return;
      await navigator.clipboard.writeText(text);
      copyBtn.textContent = '已複製！';
      setTimeout(() => {
        // 回復文案（依目前狀態）
        copyBtn.textContent = img.src === qrUrl ? '複製會員代碼' : '複製載具號碼';
      }, 1200);
    } catch (e) {
      alert('複製失敗，請手動複製。');
    }
  });

  // 預設顯示 QR
  setActive('qr');
})();
