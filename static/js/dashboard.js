(function(){
  const tabQr = document.getElementById('tab-qr');
  const tabBc = document.getElementById('tab-barcode');
  const img   = document.getElementById('code-img');
  const link  = document.getElementById('download-link');
  const copy  = document.getElementById('copy-token');

  function setActive(type){
    const isQR = type === 'qr';
    link.href = img.src;
    link.download = isQR ? "member_qr.png" : "member_barcode.png";

    tabQr.classList.toggle('btn-warning', isQR);
    tabQr.classList.toggle('btn-outline-secondary', !isQR);
    tabBc.classList.toggle('btn-warning', !isQR);
    tabBc.classList.toggle('btn-outline-secondary', isQR);
  }
  tabQr.addEventListener('click', () => setActive('qr'));
  tabBc.addEventListener('click', () => setActive('barcode'));
  setActive('qr'); // 預設 QR
})();