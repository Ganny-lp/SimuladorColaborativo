/*
 * Espelha o tema da página dentro de um iframe (diagrama, régua de preço).
 * Lê data-lumina-theme do documento pai; sem acesso a ele, usa a preferência do sistema.
 */
(function () {
  var root = document.documentElement;
  var media = window.matchMedia('(prefers-color-scheme: dark)');
  function read() {
    try {
      var t = window.parent.document.documentElement.getAttribute('data-lumina-theme');
      if (t === 'dark' || t === 'light') return t;
    } catch (e) { /* sem acesso ao pai */ }
    return media.matches ? 'dark' : 'light';
  }
  function apply() { root.setAttribute('data-theme', read()); }
  apply();
  try {
    new MutationObserver(apply).observe(window.parent.document.documentElement,
      { attributes: true, attributeFilter: ['data-lumina-theme'] });
  } catch (e) { /* idem */ }
  media.addEventListener('change', apply);
})();
