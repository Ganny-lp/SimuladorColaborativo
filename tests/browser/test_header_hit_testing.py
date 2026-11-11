"""Browser regression for the transparent Streamlit header covering scrolled tabs.
Run explicitly with RUN_BROWSER_TESTS=1 and Playwright Chromium installed.
"""
import os
from pathlib import Path
import pytest

pytestmark=pytest.mark.skipif(os.environ.get('RUN_BROWSER_TESTS')!='1',reason='Requires Playwright Chromium; enabled in browser CI')

@pytest.mark.parametrize('width',[390,1366])
def test_header_wrappers_do_not_capture_tabs(width):
    from playwright.sync_api import sync_playwright
    css=(Path(__file__).resolve().parents[2]/'frontend/assets/global_theme.css').read_text()
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':width,'height':800})
        page.set_content('''<style>
        body{margin:0;height:2000px}
        header{position:fixed;top:0;width:100%;height:60px;z-index:1000}
        [data-testid=stToolbar]{pointer-events:auto;width:100%;height:100%}
        .layout{display:flex;justify-content:flex-end;width:100%;height:100%;pointer-events:auto}
        nav{margin-top:500px;height:60px} button{height:44px}
        </style><style>'''+css+'''</style>
        <header data-testid="stHeader"><div data-testid="stToolbar"><div class="layout">
        <button id="menu" aria-label="Menu"><span>⋮</span></button></div></div></header>
        <nav role="tablist"><button role="tab" id="diagram" aria-selected="true">Diagrama</button>
        <button role="tab" id="variables" aria-selected="false">Variáveis</button></nav>
        <script>
        variables.onclick=()=>{variables.setAttribute('aria-selected','true');diagram.setAttribute('aria-selected','false')};
        menu.onclick=()=>{menu.dataset.clicked='true'};
        </script>''')
        page.evaluate('scrollTo(0,500)')
        tab=page.locator('#variables')
        # Hit testing is essential: element visibility alone missed this regression.
        assert tab.evaluate('(e)=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}')
        tab.click(timeout=3000)
        assert tab.get_attribute('aria-selected')=='true'
        page.get_by_role('button',name='Menu',exact=True).click(timeout=3000)
        assert page.locator('#menu').get_attribute('data-clicked')=='true'
        browser.close()
