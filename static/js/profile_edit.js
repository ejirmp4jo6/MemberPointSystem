// static/js/profile_edit.js
document.addEventListener('DOMContentLoaded', () => {
  const editBtn  = document.getElementById('edit-btn');
  const saveWrap = document.getElementById('save-wrap');  // 外層容器，預設有 d-none
  const saveBtn  = document.getElementById('save-btn');

  // 抓到正確的可編輯欄位（你的 HTML 用的是 editable-input）
  const fields = document.querySelectorAll('.editable-input');

  if (!editBtn || !saveWrap || !saveBtn) return;

  // 點「編輯」：解除唯讀 + 顯示「儲存/取消」
  editBtn.addEventListener('click', () => {
    fields.forEach(el => el.removeAttribute('readonly'));   // 用 readonly，而不是 disabled
    editBtn.classList.add('d-none');                        // 隱藏「編輯」
    saveWrap.classList.remove('d-none');                    // 顯示「儲存/取消」區塊
  });

  // 點「儲存」：直接送出表單（交給 Django view 儲存）
  saveBtn.addEventListener('click', (e) => {
    // 可依需求做前端驗證，通過後再送出
    document.getElementById('profile-form').submit();
  });
});
