"""Layout regression on the real Streamlit app, including its Markdown CSS."""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
import pytest

pytestmark=pytest.mark.skipif(os.environ.get('RUN_BROWSER_TESTS')!='1',reason='Real browser runs in CI')

@pytest.fixture(scope='module')
def app_url():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    root=Path(__file__).resolve().parents[2]
    process=subprocess.Popen([sys.executable,'-m','streamlit','run',str(root/'app.py'),'--server.headless=true',f'--server.port={port}','--browser.gatherUsageStats=false'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(120):
            try:
                with urlopen(f'http://127.0.0.1:{port}/_stcore/health',timeout=1) as response:
                    if response.status==200:break
            except OSError:time.sleep(.25)
        else:pytest.fail('Streamlit failed to start')
        yield f'http://127.0.0.1:{port}'
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()

@pytest.mark.parametrize('width',[320,390,900,1366])
@pytest.mark.parametrize('theme',['light','dark'])
def test_real_app_header_and_kpi_alignment(app_url,width,theme):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':width,'height':1000},color_scheme=theme)
        page.goto(app_url)
        page.get_by_role('tab',name='Simulação').click()
        page.locator('.kpi').first.wait_for()
        # Inspect the rendered geometry after web fonts have settled.
        page.evaluate('document.fonts.ready')
        header=page.locator('.lumina-header').bounding_box()
        subtitle=page.locator('.sub-header').bounding_box()
        if width>640:
            assert abs(header['x']+header['width']-subtitle['x']-subtitle['width'])<2
        else:
            assert abs(header['x']-subtitle['x'])<2
            wordmark=page.locator('.lumina-wordmark').bounding_box()
            assert subtitle['y']>=wordmark['y']+wordmark['height']
        boxes=[page.locator('.kpi').nth(i).bounding_box() for i in range(4)]
        values=[page.locator('.kpi-value').nth(i).bounding_box() for i in range(4)]
        for i in range(4):
            for j in range(i+1,4):
                if abs(boxes[i]['y']-boxes[j]['y'])<2:
                    assert abs(boxes[i]['width']-boxes[j]['width'])<2
                    assert abs(values[i]['y']-values[j]['y'])<2
        note=page.locator('.st-key-preparation-note [data-testid="stAlert"]').bounding_box()
        assert note['y']-max(b['y']+b['height'] for b in boxes)>=10
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert page.locator('.lab-intro').is_visible()
        assert page.locator('.lab-route li').count()==3
        for card in page.locator('.pulse-item').all():
            assert card.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
        if width<=480:
            pulse_boxes=[page.locator('.pulse-item').nth(i).bounding_box() for i in range(3)]
            assert pulse_boxes[1]['y']>pulse_boxes[0]['y']
        page.get_by_text('Minha hipótese para o próximo ciclo',exact=True).click()
        page.get_by_role('textbox',name='O que você espera observar?').fill('Observar a fila no próximo mês')
        page.get_by_role('button',name='Avançar ciclo',exact=True).click()
        page.get_by_text('Observar a fila no próximo mês',exact=True).first.wait_for()
        assert page.get_by_role('button',name='Exportar caderno CSV').is_visible()
        artifacts=Path(__file__).resolve().parents[2]/'test-artifacts'
        artifacts.mkdir(exist_ok=True)
        page.screenshot(path=str(artifacts/f'lab-{theme}-{width}.png'),full_page=True)
        browser.close()
