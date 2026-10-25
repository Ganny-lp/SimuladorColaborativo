/* Iframes (diagrama, régua): herdam o tema que theme_sync.html gravou na página. */
(function () {
  var r = document.documentElement;
  function s() {
    try {
      var t = window.parent.document.documentElement.getAttribute('data-lumina-theme');
      if (t && r.getAttribute('data-lumina-theme') !== t) r.setAttribute('data-lumina-theme', t);
    } catch (e) {}
  }
  s(); setInterval(s, 600);
})();
