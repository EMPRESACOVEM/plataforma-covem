import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import urllib.parse
import datetime
import base64
from datetime import datetime as dt, date, timedelta
from pathlib import Path
from streamlit_gsheets import GSheetsConnection

# ReportLab para geração de PDF estilizado
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração da página
st.set_page_config(
    page_title="Plataforma Executiva GRUPO COVEM",
    layout="wide"
)

# Caminho para arquivos secundários locais
BASE_DIR = Path(__file__).parent if "__file__" in locals() else Path.cwd()
ARQUIVO_TAREFAS = BASE_DIR / "banco_tarefas_covem.xlsx"
ARQUIVO_HISTORICO = BASE_DIR / "banco_historico_covem.xlsx"
ARQUIVO_FINANCEIRO = BASE_DIR / "banco_financeiro_covem.xlsx"
ARQUIVO_FUNDO = BASE_DIR / "fundo plataforma.jpg"
ARQUIVO_LOGO = BASE_DIR / "logoCOVEM.png"

# Nome Oficial do Grupo
COVEM_NAME = "GRUPO COVEM"

# Lista de Clientes do GRUPO COVEM
CARTEIRAS_COVEM = ["BraClean", "QV Energia Solar", "Elleven"]

# ---------------------------------------------------------
# PALETA DE CORES NEON PERSONALIZADA POR ETAPA
# ---------------------------------------------------------
DEFAULT_COLORS = {
    "Pré: Novo Lead": "#00E5FF",
    "Pré: Conexão": "#0047AB",
    "Prospecção": "#9D00FF",
    "Qualificação": "#FF007F",
    "Reunião Agendada": "#FFEA00",
    "Proposta Enviada": "#FF6600",
    "Fechado": "#00FF66",
    "Pós: Standby": "#FFFFFF",
    "Pós: Perdido": "#FF0033"
}

CORES_PERDAS = {
    "Preço / Orçamento": "#FF0033",             
    "Concorrência": "#FF6600",                  
    "Sem Resposta / Sumiu": "#FFEA00",          
    "Produto / Serviço não Atende": "#00E5FF",  
    "Outros": "#9D00FF"                         
}

FUNDO_GRAFICO_FUTURISTA = "#0A0E27"
GRID_GRAFICO_FUTURISTA = "rgba(0, 229, 255, 0.12)"

st.session_state.funnel_colors = DEFAULT_COLORS.copy()

if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "Gerenciamento de Tarefas"

if 'funnel_selecionado' not in st.session_state:
    st.session_state.funnel_selecionado = "Funil de Vendas"

if 'sub_menu_tarefas' not in st.session_state:
    st.session_state.sub_menu_tarefas = "Tarefas"

if 'editando_agenda_idx' not in st.session_state:
    st.session_state.editando_agenda_idx = None

def aplicar_fundo_personalizado(image_path):
    css_fundo = ""
    if image_path.exists():
        try:
            with open(image_path, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            css_fundo = f"""
            .stApp {{
                background-image: linear-gradient(rgba(5, 11, 24, 0.85), rgba(5, 11, 24, 0.85)), url("data:image/jpeg;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            """
        except Exception:
            pass
            
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            html, body, [class*="css"] {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            }}
            .notranslate, [data-testid="stSidebar"], [data-baseweb="select"] {{
                translate: no !important;
            }}
            {css_fundo}
            h1, h2, h3, h4, h5, h6, p, label, .streamlit-expanderHeader {{
                font-family: 'Inter', sans-serif !important;
                font-weight: 700 !important;
                letter-spacing: -0.4px !important;
                color: #FFFFFF !important;
            }}
            [data-testid="stSidebar"] {{
                background-color: rgba(10, 14, 39, 0.95) !important;
            }}
            .badge-atrasada {{
                background-color: rgba(255, 0, 51, 0.2);
                color: #FF0033;
                border: 1px solid #FF0033;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                display: inline-block;
                text-align: center;
                width: 100%;
            }}
            .badge-hoje {{
                background-color: rgba(255, 234, 0, 0.2);
                color: #FFEA00;
                border: 1px solid #FFEA00;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                display: inline-block;
                text-align: center;
                width: 100%;
            }}
            .phone-highlight {{
                color: #00E5FF;
                font-weight: 600;
            }}
            div[data-testid="stVerticalBlock"] {{
                gap: 2px !important;
            }}
            div[data-testid="stExpander"] {{
                margin-top: 12px !important;
                margin-bottom: 8px !important;
                border: 1px solid #1E293B !important;
                background-color: rgba(10, 14, 39, 0.85) !important;
            }}
            div[data-testid="stExpander"] details summary {{
                padding-top: 8px !important;
                padding-bottom: 8px !important;
            }}
            div[data-testid="stMetricValue"] {{
                font-family: 'Inter', sans-serif !important;
                font-size: 22px !important;
                font-weight: 700 !important;
                color: #FFFFFF !important;
            }}
            div[data-testid="stMetricLabel"] {{
                font-family: 'Inter', sans-serif !important;
                font-size: 12px !important;
            }}
        </style>
    """, unsafe_allow_html=True)

aplicar_fundo_personalizado(ARQUIVO_FUNDO)

PROB_MAP = {
    "Pré: Novo Lead": 0.05,
    "Pré: Conexão": 0.10,
    "Prospecção": 0.20,
    "Qualificação": 0.40,
    "Reunião Agendada": 0.60,
    "Proposta Enviada": 0.80,
    "Fechado": 1.00,
    "Pós: Standby": 0.00,
    "Pós: Perdido": 0.00
}

ESTRUTURA_FUNIS = {
    "Pré Funil": ["Pré: Novo Lead", "Pré: Conexão"],
    "Funil de Vendas": ["Prospecção", "Qualificação", "Reunião Agendada", "Proposta Enviada", "Fechado"],
    "Pós Funil": ["Pós: Standby", "Pós: Perdido"]
}

MOTIVOS_PERDA_PADRAO = list(CORES_PERDAS.keys())

@st.cache_resource
def get_gsheets_connection():
    return st.connection("gsheets", type=GSheetsConnection)

conn = get_gsheets_connection()

def carregar_dados_crm():
    try:
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            if "private_key" in st.secrets["connections"]["gsheets"]:
                pk = st.secrets["connections"]["gsheets"]["private_key"]
                if "\\n" in pk:
                    st.secrets["connections"]["gsheets"]["private_key"] = pk.replace("\\n", "\n")

        df_loaded = conn.read(worksheet="Página1", ttl=0)
        df_loaded = df_loaded.dropna(how="all")
        
        colunas_esperadas = ["id", "Empresa", "Cliente", "Etapa", "Contato", "Cargo", "Telefone", "Email", "Cidade", "Valor", "Prob", "Vendedor", "Perda", "Data_Cadastro", "Followup_Data", "Followup_Nota", "Historico"]
        for col in colunas_esperadas:
            if col not in df_loaded.columns:
                df_loaded[col] = ""
                
        if not df_loaded.empty:
            df_loaded["id"] = pd.to_numeric(df_loaded["id"], errors="coerce").fillna(0).astype(int)
            df_loaded["Valor"] = pd.to_numeric(df_loaded["Valor"], errors="coerce").fillna(0.0)
            df_loaded["Prob"] = pd.to_numeric(df_loaded["Prob"], errors="coerce").fillna(0.2)
            df_loaded["Perda"] = df_loaded["Perda"].fillna("").astype(str)
            df_loaded["Vendedor"] = df_loaded["Vendedor"].apply(lambda x: "Gabriel" if str(x).strip() in ["", "nan", "Não informado"] else x)
            return df_loaded
    except Exception as e:
        st.warning(f"Aviso ao ler do Google Sheets: {e}. Carregando dados padrão iniciais.")

    df_inicial = pd.DataFrame([
        {
            "id": 1, "Empresa": "Grupo Delta", "Cliente": "BraClean", "Etapa": "Prospecção", 
            "Contato": "Roberto Alves", "Cargo": "Diretor Comercial", "Telefone": "(16) 99876-5432", 
            "Email": "roberto@grupodelta.com.br", "Cidade": "Sertãozinho / SP", "Valor": 35000.0, 
            "Prob": 0.20, "Vendedor": "Gabriel", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today() - timedelta(days=2)), "Followup_Nota": "Enviar apresentação institucional atualizada.", 
            "Historico": "[01/09/2026 10:00] Primeiro contato realizado."
        }
    ])
    try:
        conn.update(worksheet="Página1", data=df_inicial)
    except:
        pass
    return df_inicial

def salvar_dados_crm(df):
    try:
        conn.update(worksheet="Página1", data=df)
    except Exception as e:
        st.error(f"Erro ao salvar dados no Google Sheets: {e}")

def carregar_dados_tarefas():
    if ARQUIVO_TAREFAS.exists():
        try:
            return pd.read_excel(ARQUIVO_TAREFAS)
        except Exception:
            pass
    df_inicial_vazio = pd.DataFrame(columns=["Titulo", "Descricao", "Cliente", "Data_Vencimento", "Prioridade", "Status", "Data_Criacao"])
    df_inicial_vazio.to_excel(ARQUIVO_TAREFAS, index=False)
    return df_inicial_vazio

def salvar_dados_tarefas(df):
    df.to_excel(ARQUIVO_TAREFAS, index=False)

# ---------------------------------------------------------
# GERADORES DE ARQUIVOS (EXCEL E PDF COM LOGO E ASSINATURAS)
# ---------------------------------------------------------
def gerar_excel_executivo(df_crm):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_crm.to_excel(writer, sheet_name='Base_Leads_CRM', index=False)
            
        resumo_data = [
            {"Métrica": "Total de Leads Ativos", "Valor": len(df_crm)},
            {"Métrica": "Pipeline Bruto Negociado (R$)", "Valor": df_crm["Valor"].sum()},
            {"Métrica": "Faturamento Fechado BraClean (R$)", "Valor": df_crm[(df_crm["Cliente"] == "BraClean") & (df_crm["Etapa"] == "Fechado")]["Valor"].sum()},
            {"Métrica": "Meta Mensal BraClean Alvo (R$)", "Valor": 100000.0}
        ]
        pd.DataFrame(resumo_data).to_excel(writer, sheet_name='Resumo_KPIs', index=False)
    output.seek(0)
    return output

def gerar_pdf_executivo(df_crm, cliente_filtro):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=16,
        textColor=colors.HexColor('#00E5FF'), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9,
        textColor=colors.HexColor('#64748B'), spaceAfter=10
    )
    heading_style = ParagraphStyle(
        'HeadingStyle', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=11,
        textColor=colors.HexColor('#9D00FF'), spaceBefore=10, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyStyle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8,
        textColor=colors.HexColor('#1E293B')
    )

    if ARQUIVO_LOGO.exists():
        try:
            logo_img = RLImage(str(ARQUIVO_LOGO), width=120, height=45)
            logo_img.hAlign = 'LEFT'
            story.append(logo_img)
            story.append(Spacer(1, 5))
        except Exception:
            pass

    story.append(Paragraph(f"RESUMO EXECUTIVO COMERCIAL — {COVEM_NAME}", title_style))
    data_emissao = dt.now().strftime("%d/%m/%Y às %H:%M")
    story.append(Paragraph(f"Filtro: <b>{cliente_filtro}</b> | Emitido em: {data_emissao}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#00E5FF'), spaceAfter=10))

    total_leads = len(df_crm)
    val_total = df_crm["Valor"].sum()
    braclean_val = df_crm[(df_crm["Cliente"] == "BraClean") & (df_crm["Etapa"] == "Fechado")]["Valor"].sum()

    kpi_table_data = [
        [Paragraph("<b>Total de Leads</b>", body_style), Paragraph("<b>Pipeline Bruto</b>", body_style), Paragraph("<b>Fechado BraClean</b>", body_style), Paragraph("<b>Meta BraClean</b>", body_style)],
        [f"{total_leads} leads", f"R$ {val_total:,.2f}", f"R$ {braclean_val:,.2f}", "R$ 100.000,00"]
    ]
    t_kpi = Table(kpi_table_data, colWidths=[130, 130, 140, 140])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0A0E27')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#00E5FF')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#00E5FF'))
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Distribuição por Etapas do Funil", heading_style))
    funil_dados = [["Etapa Comercial", "Volume de Leads", "% do Funil"]]
    for e in list(PROB_MAP.keys()):
        qtd = len(df_crm[df_crm["Etapa"] == e])
        pct = (qtd / total_leads * 100) if total_leads > 0 else 0
        funil_dados.append([e.replace("Pré: ", "").replace("Pós: ", ""), str(qtd), f"{pct:.1f}%"])

    t_funil = Table(funil_dados, colWidths=[240, 150, 150])
    t_funil.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(t_funil)
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Desempenho Individual (Gabriel vs Ariel) — Meta 50/Dia", heading_style))
    vend_dados = [["Vendedor / Responsável", "Leads Alocados", "Status da Meta Diária"]]
    for v in ["Gabriel", "Ariel"]:
        qtd_v = len(df_crm[df_crm["Vendedor"].str.contains(v, case=False, na=False)])
        st_meta = "Atingida" if qtd_v >= 50 else f"Em andamento ({qtd_v}/50)"
        vend_dados.append([v, str(qtd_v), st_meta])

    t_vend = Table(vend_dados, colWidths=[200, 170, 170])
    t_vend.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(t_vend)
    story.append(Spacer(1, 25))

    story.append(Paragraph("3. Aprovação Diretiva e Validação Executiva", heading_style))
    story.append(Spacer(1, 15))

    assinatura_data = [
        [Paragraph("____________________________________________<br/><b>Gabriel Rogerio da Silva</b><br/>Fundador & CEO - COVEM", body_style),
         Paragraph("____________________________________________<br/><b>Glória</b><br/>Diretoria Executiva / Operações", body_style)]
    ]
    t_ass = Table(assinatura_data, colWidths=[270, 270])
    t_ass.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t_ass)

    doc.build(story)
    buffer.seek(0)
    return buffer

if 'df_crm' not in st.session_state:
    st.session_state.df_crm = carregar_dados_crm()

if 'df_tarefas' not in st.session_state:
    st.session_state.df_tarefas = carregar_dados_tarefas()

if 'cliente_editando_id' not in st.session_state:
    st.session_state.cliente_editando_id = None

df = st.session_state.df_crm

def calcular_status_followup(data_str):
    if not data_str or pd.isna(data_str) or str(data_str).strip() in ["", "nan", "NaT", "None"]:
        return "sem_data", "Sem Follow-up", '<span style="height: 10px; width: 10px; background-color: #94A3B8; border-radius: 50%; display: inline-block;"></span>'
    try:
        limpa_data = str(data_str).strip()[:10]
        dt_follow = dt.strptime(limpa_data, "%Y-%m-%d").date()
        hoje = date.today()
        if dt_follow < hoje:
            return "atrasado", "Atrasado", '<span style="height: 10px; width: 10px; background-color: #FF0033; border-radius: 50%; display: inline-block;"></span>'
        elif dt_follow == hoje:
            return "hoje", "Atenção (Hoje)", '<span style="height: 10px; width: 10px; background-color: #FFEA00; border-radius: 50%; display: inline-block;"></span>'
        else:
            return "em_dia", "Em Dia", '<span style="height: 10px; width: 10px; background-color: #00FF66; border-radius: 50%; display: inline-block;"></span>'
    except:
        return "sem_data", "Sem Follow-up", '<span style="height: 10px; width: 10px; background-color: #94A3B8; border-radius: 50%; display: inline-block;"></span>'

opcoes_filtro = ["TODOS"] + CARTEIRAS_COVEM
cliente_sel = st.sidebar.selectbox("Clientes COVEM:", opcoes_filtro)

if cliente_sel != "TODOS":
    df_filtered = df[df["Cliente"] == cliente_sel]
    titulo_dinamico = f"Dashboard - {cliente_sel}"
    titulo_funil = f"Gestão de Funis — {cliente_sel}"
else:
    df_filtered = df
    titulo_dinamico = f"Dashboard - {COVEM_NAME}"
    titulo_funil = f"Gestão de Funis — {COVEM_NAME}"

st.sidebar.divider()

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df_filtered.to_excel(writer, index=False, sheet_name='CRM_COVEM')
buffer.seek(0)

st.sidebar.download_button(
    label="Baixar Planilha Excel",
    data=buffer,
    file_name="crm_covem.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if ARQUIVO_LOGO.exists():
        st.image(str(ARQUIVO_LOGO), use_container_width=True)

st.divider()

abas_disponiveis = [
    "Gerenciamento de Tarefas",
    "Funil de Vendas", 
    "Dashboard", 
    "Relatório Executivo", 
    "+ Novo Cadastro"
]

cols_menu = st.columns(len(abas_disponiveis))
for i, nome_aba in enumerate(abas_disponiveis):
    with cols_menu[i]:
        if st.session_state.menu_ativo == nome_aba:
            st.markdown(f"""<style>div[data-testid="column"]:nth-of-type({i+1}) div.stButton > button {{ background-color: #0A0E27 !important; color: #00E5FF !important; border: 1px solid #00E5FF !important; font-weight: 600 !important; }}</style>""", unsafe_allow_html=True)
        if st.button(nome_aba, key=f"menu_card_{i}", use_container_width=True):
            st.session_state.menu_ativo = nome_aba
            st.rerun()

st.divider()
aba_selecionada = st.session_state.menu_ativo

# =========================================================
# ABA 1: GERENCIADOR DE TAREFAS
# =========================================================
if aba_selecionada == "Gerenciamento de Tarefas":
    st.subheader(f"Gerenciamento de Tarefas — {cliente_sel}")
    exibir_agenda_semana = lambda x, y, z: None # Placeholder para o bloco de agenda
    
    if cliente_sel != "TODOS":
        lista_clientes = ["Nenhum / Tarefa Geral"] + df_filtered["Empresa"].dropna().tolist()
    else:
        lista_clientes = (
            ["Nenhum / Tarefa Geral"] + st.session_state.df_crm["Empresa"].dropna().tolist()
            if not st.session_state.df_crm.empty
            else ["Nenhum / Tarefa Geral"]
        )

# =========================================================
# ABA 2: FUNIL DE VENDAS
# =========================================================
elif aba_selecionada == "Funil de Vendas":
    col_topo_titulo, col_topo_busca = st.columns([2, 1])
    with col_topo_titulo:
        st.subheader(titulo_funil)
    with col_topo_busca:
        termo_busca = st.text_input("Pesquisar cliente", placeholder="Buscar por empresa, contato...", label_visibility="collapsed")

# =========================================================
# ABA 3: DASHBOARD
# =========================================================
elif aba_selecionada == "Dashboard":
    st.markdown(f'<div class="notranslate"><h3>{titulo_dinamico}</h3></div>', unsafe_allow_html=True)

# =========================================================
# ABA 4: RELATÓRIO EXECUTIVO (SEM EMOJIS, SEM HISTÓRICO E SEM FINANCEIRO)
# =========================================================
elif aba_selecionada == "Relatório Executivo":
    col_ex_t, col_ex_b1, col_ex_b2 = st.columns([2, 1, 1])
    
    with col_ex_t:
        st.title("Relatório Executivo")

    with col_ex_b1:
        excel_data = gerar_excel_executivo(df_filtered)
        st.download_button(
            label="Exportar para Excel",
            data=excel_data,
            file_name=f"Relatorio_Executivo_COVEM_{dt.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_ex_b2:
        pdf_data = gerar_pdf_executivo(df_filtered, cliente_sel)
        st.download_button(
            label="Gerar Relatório PDF",
            data=pdf_data,
            file_name=f"Relatorio_Executivo_COVEM_{dt.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.divider()

    # 1. GRAFICO DE FUNIL GERAL DE ATIVIDADE
    st.markdown("### 1. Gráfico de Funil Geral de Atividade")
    st.caption("Visão em gráfico do crescimento de leads e etapas de avanço no funil comercial.")

    df_exec = df_filtered.copy()
    etapas_ordem = list(PROB_MAP.keys())
    
    funil_dados = []
    for etapa in etapas_ordem:
        qtd = len(df_exec[df_exec["Etapa"] == etapa])
        funil_dados.append({"Etapa": etapa.replace("Pré: ", "").replace("Pós: ", ""), "Quantidade": qtd, "Etapa_Orig": etapa})

    df_funil = pd.DataFrame(funil_dados)
    df_funil_valido = df_funil[df_funil["Quantidade"] > 0]

    if not df_funil_valido.empty:
        fig_funil_exec = px.funnel(
            df_funil_valido,
            x="Quantidade",
            y="Etapa",
            color="Etapa_Orig",
            color_discrete_map=st.session_state.funnel_colors
        )
        fig_funil_exec.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=13),
            height=380,
            showlegend=False
        )
        st.plotly_chart(fig_funil_exec, use_container_width=True)
    else:
        st.info("Nenhum lead registrado no funil no momento.")

    st.divider()

    # 2. ATIVIDADES INDIVIDUAIS (GABRIEL VS ARIEL) E METAS
    st.markdown("### 2. Atividades Individuais e Metas de Vendedores")
    st.caption("Meta do Grupo COVEM: 50 interações/dia por vendedor (Entradas de novos leads ou movimentações nas etapas).")

    vendedores_covem = ["Gabriel", "Ariel"]
    df_exec["Vendedor"] = df_exec["Vendedor"].fillna("Gabriel")
    
    vendedores_dados = []
    for v in vendedores_covem:
        sub_v = df_exec[df_exec["Vendedor"].str.contains(v, case=False, na=False)]
        qtd_leads = len(sub_v)
        vendedores_dados.append({"Vendedor": v, "Leads Movimentados": qtd_leads})
        
    df_vend = pd.DataFrame(vendedores_dados)
    
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Meta Diária por Vendedor", "50 Leads/Dia")
    c_m2.metric("Meta Semanal (5d)", "250 Leads/Sem")
    c_m3.metric("Meta Mensal (20d)", "1.000 Leads/Mês")

    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        df_vend["Meta Diária"] = 50
        fig_metas = px.bar(
            df_vend,
            x="Vendedor",
            y=["Leads Movimentados", "Meta Diária"],
            barmode="group",
            title="Acompanhamento do Trabalho Individual vs Meta Diária (50)",
            color_discrete_map={"Leads Movimentados": "#00E5FF", "Meta Diária": "#FFEA00"},
            text_auto=True
        )
        fig_metas.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=12),
            height=360,
            xaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
            yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA)
        )
        st.plotly_chart(fig_metas, use_container_width=True)

    with col_v2:
        df_gargalos = df_exec.groupby("Etapa").size().reset_index(name="Quantidade")
        fig_gargalo = px.bar(
            df_gargalos,
            x="Etapa",
            y="Quantidade",
            title="Levantamento de Gargalos (Onde o Lead está parando)",
            color="Etapa",
            color_discrete_map=st.session_state.funnel_colors,
            text_auto=True
        )
        fig_gargalo.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=12),
            height=360,
            showlegend=False,
            xaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
            yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA)
        )
        st.plotly_chart(fig_gargalo, use_container_width=True)

    st.divider()

    # 3. META BRACLEAN (TICKET MÉDIO E R$ 100K MENSAL ATÉ DEZEMBRO)
    st.markdown("### 3. Meta BraClean (Ticket Médio e R$ 100k Mensais até Dezembro)")
    
    df_braclean = df_exec[df_exec["Cliente"] == "BraClean"]
    faturamento_braclean = float(df_braclean[df_braclean["Etapa"] == "Fechado"]["Valor"].sum())
    qtd_clientes_braclean = len(df_braclean[df_braclean["Etapa"] == "Fechado"])
    
    ticket_medio = (faturamento_braclean / qtd_clientes_braclean) if qtd_clientes_braclean > 0 else (df_braclean["Valor"].mean() if not df_braclean.empty else 0.0)
    if pd.isna(ticket_medio):
        ticket_medio = 0.0

    meta_alvo = 100000.0
    clientes_necessarios = int(meta_alvo / ticket_medio) if ticket_medio > 0 else 0

    bm1, bm2, bm3, bm4 = st.columns(4)
    bm1.metric("Meta Faturamento Mensal", f"R$ {meta_alvo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    bm2.metric("Faturamento Fechado Atual", f"R$ {faturamento_braclean:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    bm3.metric("Ticket Médio BraClean", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    bm4.metric("Clientes Necessários (100k)", f"{clientes_necessarios} clientes ativos")

    meses_proj = ["Outubro", "Novembro", "Dezembro"]
    progresso_braclean = [faturamento_braclean, faturamento_braclean + (meta_alvo - faturamento_braclean) * 0.5, meta_alvo]
    meta_linha = [meta_alvo, meta_alvo, meta_alvo]

    df_proj_braclean = pd.DataFrame({
        "Mês": meses_proj,
        "Projeção de Vendas": progresso_braclean,
        "Meta Alvo (R$ 100k)": meta_linha
    })

    fig_braclean_meta = px.line(
        df_proj_braclean,
        x="Mês",
        y=["Projeção de Vendas", "Meta Alvo (R$ 100k)"],
        markers=True,
        title="Planejamento de Vendas Rumo a R$ 100.000,00 Mensais (BraClean)",
        color_discrete_map={"Projeção de Vendas": "#00FF66", "Meta Alvo (R$ 100k)": "#FF0033"}
    )
    fig_braclean_meta.update_layout(
        paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        font=dict(color="#FFFFFF", family="Inter", size=13),
        height=380,
        xaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
        yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA)
    )
    st.plotly_chart(fig_braclean_meta, use_container_width=True)

    st.divider()

    # 4. ESTATÍSTICA E PROBABILIDADE FUTURA (PREVISÃO E FORECAST)
    st.markdown("### 4. Estatística e Probabilidade Futura (Previsão de Receita / Forecast)")
    st.caption("Estatística ponderada da receita esperada calculada sobre a taxa de conversão de cada etapa.")

    df_exec["Receita_Ponderada"] = df_exec["Valor"] * df_exec["Prob"]
    
    val_total_pipeline = float(df_exec["Valor"].sum())
    receita_esperada = float(df_exec["Receita_Ponderada"].sum())
    taxa_conversao_media = (receita_esperada / val_total_pipeline * 100) if val_total_pipeline > 0 else 0.0

    f1, f2, f3 = st.columns(3)
    f1.metric("Pipeline Bruto em Negociação", f"R$ {val_total_pipeline:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    f2.metric("Previsão Ponderada de Fechamento", f"R$ {receita_esperada:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    f3.metric("Probabilidade Média de Conversão", f"{taxa_conversao_media:.1f}%")

    df_forecast = df_exec.groupby("Etapa").agg(
        Valor_Bruto=("Valor", "sum"),
        Valor_Ponderado=("Receita_Ponderada", "sum")
    ).reset_index()

    fig_forecast = px.bar(
        df_forecast,
        x="Etapa",
        y=["Valor_Bruto", "Valor_Ponderado"],
        barmode="group",
        title="Probabilidade Futura por Etapa do Funil (Bruto vs Ponderado)",
        color_discrete_map={"Valor_Bruto": "#9D00FF", "Valor_Ponderado": "#00FF66"},
        labels={"value": "Valor (R$)", "variable": "Tipo de Análise"}
    )
    fig_forecast.update_layout(
        paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        font=dict(color="#FFFFFF", family="Inter", size=13),
        height=380,
        xaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
        yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA)
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

# =========================================================
# ABA 5: + NOVO CADASTRO
# =========================================================
elif aba_selecionada == "+ Novo Cadastro":
    default_carteira_idx = 0
    if cliente_sel != "TODOS" and cliente_sel in CARTEIRAS_COVEM:
        default_carteira_idx = CARTEIRAS_COVEM.index(cliente_sel)

    st.subheader(f"Novo Cadastro Rápido ({f'Sincronizado com: {cliente_sel}' if cliente_sel != 'TODOS' else 'Geral'})")
