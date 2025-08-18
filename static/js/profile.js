document.addEventListener('DOMContentLoaded', function () {
  const btn = document.getElementById('copy-token');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const value = btn.dataset.token;
    try {
      // 現代瀏覽器 (需 HTTPS 或 localhost)
      await navigator.clipboard.writeText(value);
    // 替換圖示
      const oldHTML = btn.innerHTML;
      btn.innerHTML = '<i class="bi bi-check-lg"></i>';
      btn.classList.remove('btn-outline-secondary');
      btn.classList.add('btn-success');
      setTimeout(() => {
        btn.innerHTML = oldHTML; // 恢復 copy icon
        btn.classList.remove('btn-success');
        btn.classList.add('btn-outline-secondary');
      }, 1500);
    } catch (e) {
      // 後備方案：建立暫時 textarea 複製（適用 http/舊瀏覽器）
      const ta = document.createElement('textarea');
      ta.value = value;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); alert('已複製'); }
      catch (_) { alert('複製失敗，請長按選取'); }
      document.body.removeChild(ta);
    }
  });
});
