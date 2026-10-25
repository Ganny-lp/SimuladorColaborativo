/*
 * Ponte de tema (roda num iframe de altura 0 na página principal).
 *
 * O Streamlit decide claro/escuro sozinho (tema do sistema ou o escolhido no menu ⋮) e
 * expõe a decisão em `color-scheme` do elemento .stApp. Aqui isso vira o atributo
 * data-lumina-theme no <html>, que o brand_tokens.css usa para trocar as variáveis, e
 * que os iframes (theme_sync.js) espelham. Nada de recarregar a página: troca ao vivo.
 */
(function () {
  var P = window.parent, D, root;
  try { D = P.document; root = D.documentElement; } catch (e) { return; }

  function detect() {
    var app = D.querySelector('.stApp');
    if (app) {
      var scheme = P.getComputedStyle(app).colorScheme;
      if (scheme === 'dark' || scheme === 'light') return scheme;
    }
    var m = (P.getComputedStyle(D.body).backgroundColor || '').match(/[\d.]+/g);
    if (m && m.length >= 3) {
      return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255 < 0.5 ? 'dark' : 'light';
    }
    return P.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function sync() {
    var theme = detect();
    if (root.getAttribute('data-lumina-theme') !== theme) root.setAttribute('data-lumina-theme', theme);
  }

  sync();
  var observer = new MutationObserver(sync);
  observer.observe(root, { attributes: true });
  if (D.head) observer.observe(D.head, { childList: true });   // o Streamlit troca <style> ao mudar de tema
  var app = D.querySelector('.stApp');
  if (app) observer.observe(app, { attributes: true });
  var timer = setInterval(sync, 1500);                          // rede de segurança, custo desprezível
  P.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', sync);
  window.addEventListener('pagehide', function () { observer.disconnect(); clearInterval(timer); });
})();
