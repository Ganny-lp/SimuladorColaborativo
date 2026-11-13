"""The experiment narrative uses existing snapshots; it never changes model equations."""
from html import escape
import csv
import io
import streamlit as st
from frontend.compat import keyed_container
from frontend.formatters import currency, decimal_number

EVIDENCE_NAMES={'Inflacao','Nc','Carga_Tributaria','Alfa','Beta_1','Preco_Equipamento_Novo','Inovacao_Fabricantes','Influencia_Avaliacoes_Online'}


def evidence_count(snapshot):
    records=snapshot.model_payload.get('calibration',{})
    return sum(isinstance(records.get(v.name),dict) and records[v.name].get('value')==v.value for v in snapshot.variables if v.name in EVIDENCE_NAMES)


def intro_html(snapshot):
    stage='Preparação' if snapshot.cycle==0 else f'Ciclo {snapshot.cycle} concluído'
    return ('<section class="lab-intro" aria-label="Laboratório de decisões">'
            '<div><span class="lab-eyebrow">LUMINA / LABORATÓRIO DE DECISÕES</span>'
            '<h1>Pequenas escolhas.<br>Novas perspectivas.</h1>'
            '<p>Explore como preço, equipe e investimento transformam a trajetória de uma assistência técnica.</p></div>'
            '<div class="lab-passport"><span>SEU EXPERIMENTO</span>'
            f'<strong>{escape(stage)}</strong><p>{evidence_count(snapshot)} de 8 parâmetros com evidência vinculada</p>'
            '<small>Modelo didático · ciclos mensais</small></div></section>')


def render_intro(snapshot):
    st.markdown(intro_html(snapshot),unsafe_allow_html=True)
    st.markdown('<ol class="lab-route" aria-label="Roteiro do experimento">'
                '<li><span>01</span><div><b>Formule</b><small>O que você quer investigar?</small></div></li>'
                '<li><span>02</span><div><b>Experimente</b><small>Ajuste e avance um ciclo.</small></div></li>'
                '<li><span>03</span><div><b>Observe</b><small>Compare resultados e registre.</small></div></li></ol>',unsafe_allow_html=True)


def render_pulse(snapshot):
    def value(name):
        v=snapshot.variable(name)
        return v.value if v else 0
    cards=[('Fila atual',decimal_number(value('Backlog_Servicos')),'serviços aguardando atendimento'),
           ('Peças disponíveis',decimal_number(value('Estoque_Pecas')),'saldo atual do estoque'),
           ('Caixa operacional',currency(value('Caixa_Disponivel')),'saldo após o último estado calculado')]
    html=''.join(f'<div class="pulse-item"><span>{escape(label)}</span><strong>{escape(number)}</strong><small>{escape(hint)}</small></div>' for label,number,hint in cards)
    st.markdown('<section class="lab-pulse" aria-label="Estado atual da operação">'+html+'</section>',unsafe_allow_html=True)


def notebook_csv(snapshot,notes):
    buffer=io.StringIO();writer=csv.writer(buffer)
    writer.writerow(['ciclo','resultado_mensal_brl','fluxo_acumulado_brl','hipotese','preco_decidido_brl'])
    # Only completed cycles are exported; unfinished hypotheses remain drafts.
    for record in snapshot.history:
        note=notes.get(str(record.cycle),{})
        text=note.get('hypothesis','')
        if text.lstrip().startswith(('=','+','-','@')) or text.startswith(('\t','\r','\n')):text="'"+text
        writer.writerow([record.cycle,record.profit,record.accumulated_profitability,text,note.get('price','')])
    return buffer.getvalue()


def render_notebook(snapshot):
    notes=st.session_state.get('lab.completed_notes',{})
    with keyed_container('lab-notebook'):
        st.markdown('### Caderno do experimento')
        st.caption('Suas hipóteses ficam nesta sessão e podem acompanhar os resultados no CSV. Não são enviadas ao modelo compartilhado.')
        if not snapshot.history:
            st.info('Seu primeiro registro aparece depois de avançar um ciclo.',icon=':material/edit_note:')
        else:
            latest=snapshot.history[-1]
            st.metric(f'Resultado do ciclo {latest.cycle}',currency(latest.profit))
            note=notes.get(str(latest.cycle),{}).get('hypothesis','')
            if note:st.write(note)
            else:st.caption('Nenhuma hipótese registrada para este ciclo.')
            with st.expander('Revisitar ciclos anteriores'):
                for record in reversed(snapshot.history):
                    st.markdown(f'**Ciclo {record.cycle} · {currency(record.profit)}**')
                    st.write(notes.get(str(record.cycle),{}).get('hypothesis') or 'Sem hipótese registrada.')
            st.download_button('Exportar caderno CSV',notebook_csv(snapshot,notes).encode('utf-8-sig'),file_name='lumina_experimento.csv',mime='text/csv',key='lab.export')
