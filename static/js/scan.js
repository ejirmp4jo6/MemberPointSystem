(function(){
  // ====== 共用 ======
  const tokenInput = document.getElementById('token-input');
  const amountInput = document.getElementById('amount-input');
  const tabQr = document.getElementById('tab-qr');
  const tabBc = document.getElementById('tab-bc');
  const qrBox = document.getElementById('qr-box');
  const bcBox = document.getElementById('bc-box');
  const bcSwapBtn = document.getElementById('bc-swap');
  let activeScanner = 'qr';     // 'qr' or 'bc'
  let html5Qr = null;
  let bcStream = null;
  let bcDeviceIds = []; let bcDeviceIdx = 0;

  function onDetected(text){
    // 寫入欄位，去空白
    tokenInput.value = (text || '').trim();
    // 震動提示（支援裝置）
    if (navigator.vibrate) navigator.vibrate(80);
    // 跳到金額欄位
    amountInput.focus();
  }

  function setTabs(type){
    const isQR = type === 'qr';
    tabQr.classList.toggle('btn-warning', isQR);
    tabQr.classList.toggle('btn-outline-secondary', !isQR);
    tabBc.classList.toggle('btn-warning', !isQR);
    tabBc.classList.toggle('btn-outline-secondary', isQR);
    qrBox.style.display = isQR ? 'block' : 'none';
    bcBox.style.display = isQR ? 'none' : 'block';
  }

  // ====== QR 掃描（html5-qrcode）======
  async function startQR(){
    if (html5Qr) return; // 已啟動
    const opts = {
      formatsToSupport: [ Html5QrcodeSupportedFormats.QR_CODE ],
      fps: 10,
      qrbox: { width: 250, height: 250 },
      rememberLastUsedCamera: true
    };
    html5Qr = new Html5Qrcode("qr-reader");
    try {
      await html5Qr.start(
        { facingMode: "environment" },
        opts,
        (decoded) => {
          stopQR(); onDetected(decoded);
        },
        () => {}
      );
    } catch (e) {
      console.error(e);
      alert("無法啟動相機（行動裝置需 HTTPS 或 localhost）。");
      stopQR();
    }
  }
  async function stopQR(){
    if (html5Qr) {
      try { await html5Qr.stop(); } catch(_){}
      try { await html5Qr.clear(); } catch(_){}
      html5Qr = null;
    }
  }

  // ====== 條碼掃描（Quagga2）======
  async function listCameras(){
    const devices = await navigator.mediaDevices.enumerateDevices();
    bcDeviceIds = devices.filter(d => d.kind === 'videoinput').map(d => d.deviceId);
    if (bcDeviceIdx >= bcDeviceIds.length) bcDeviceIdx = 0;
  }
  async function startBC(){
    await listCameras();
    const deviceId = bcDeviceIds[bcDeviceIdx] || undefined;
    const constraints = deviceId ? { deviceId: { exact: deviceId } } : { facingMode: "environment" };

    // 先開原生串流以獲取寬高
    try{
      bcStream = await navigator.mediaDevices.getUserMedia({ video: constraints, audio:false });
    } catch(e){
      console.error(e);
      alert("無法啟動相機（行動裝置需 HTTPS 或 localhost）。");
      return;
    }

    const video = document.createElement('video');
    video.setAttribute('playsinline', true);
    video.srcObject = bcStream;
    await video.play();

    const width = Math.min(window.innerWidth, 480);
    const height = Math.floor(width * 0.75);

    Quagga.init({
      inputStream: {
        type: "LiveStream",
        target: document.querySelector("#bc-reader"),
        constraints: { ...constraints, width, height }
      },
      decoder: {
        readers: ["code_128_reader"]  // 你的條碼是 Code128
      },
      locate: true,
      numOfWorkers: 0
    }, function(err){
      if (err) { console.error(err); alert("條碼掃描啟動失敗"); return; }
      Quagga.start();
    });

    Quagga.onDetected(function(res){
      const code = (res && res.codeResult && res.codeResult.code) || "";
      if (code) {
        stopBC(); onDetected(code);
      }
    });
  }
  function stopBC(){
    try { Quagga.offDetected(); Quagga.stop(); } catch(_){}
    if (bcStream){
      bcStream.getTracks().forEach(t => t.stop());
      bcStream = null;
    }
  }
  bcSwapBtn.addEventListener('click', async function(){
    if (!bcDeviceIds.length) await listCameras();
    bcDeviceIdx = (bcDeviceIdx + 1) % (bcDeviceIds.length || 1);
    stopBC(); startBC();
  });

  // ====== 切換控制 ======
  tabQr.addEventListener('click', async () => {
    if (activeScanner === 'qr') return;
    activeScanner = 'qr'; setTabs('qr'); stopBC(); await startQR();
  });
  tabBc.addEventListener('click', async () => {
    if (activeScanner === 'bc') return;
    activeScanner = 'bc'; setTabs('bc'); await stopQR(); await startBC();
  });

  // 預設啟動 QR
  setTabs('qr');
  // 稍等庫載入完成
  window.addEventListener('load', () => {
    startQR();
  });

  // 離開頁面時清理相機
  window.addEventListener('beforeunload', () => { stopQR(); stopBC(); });
})();