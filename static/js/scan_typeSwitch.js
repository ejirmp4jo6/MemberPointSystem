// static/js/scan_typeSwitch.js
document.addEventListener("DOMContentLoaded", function () {
  const label   = document.getElementById("amount-label");
  const earn    = document.getElementById("mode-earn");
  const deduct  = document.getElementById("mode-deduct");
  // 若也想改 placeholder，可拿來用：
  // const input   = document.getElementById("amount-input");

  function updateLabel() {
    if (!label || !earn || !deduct) return;

    if (deduct.checked) {
      label.textContent = "扣除點數";
      // input.placeholder = "請輸入要扣除的點數";
    } else {
      label.textContent = "消費金額（TWD）";
      // input.placeholder = "請輸入消費金額";
    }
  }

  earn.addEventListener("change", updateLabel);
  deduct.addEventListener("change", updateLabel);

  // 首次載入就同步一次狀態
  updateLabel();
});
