/* 深淺色初始化：在 <head> 同步載入，避免頁面閃一下白底。 */
(function () {
  var d = document.documentElement;
  d.classList.add('js');
  try {
    var t = localStorage.getItem('theme');
    if (t === 'light' || t === 'dark') d.setAttribute('data-theme', t);
  } catch (e) { /* 無痕模式或封鎖儲存時，直接跟隨系統 */ }
})();
