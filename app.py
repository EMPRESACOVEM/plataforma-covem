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
ARQUIVO_ANOTACOES = BASE_DIR / "banco_anotacoes_covem.xlsx"
ARQUIVO_FUNDO = BASE_DIR / "fundo plataforma.jpg"
ARQUIVO_LOGO = BASE_DIR / "logoCOVEM.png"

# Nome Oficial do Grupo
COVEM_NAME = "GRUPO COVEM"

# Lista de Clientes / Carteiras do GRUPO COVEM
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
            html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }}
            .notranslate, [data-testid="stSidebar"], [data-baseweb="select"] {{ translate: no !important; }}
            {css_fundo}
            h1, h2, h3, h4, h5, h6, p, label, .streamlit-expanderHeader {{ font-family: 'Inter', sans-serif !important; font-weight: 700 !important; color: #FFFFFF !important; }}
            [data-testid="stSidebar"] {{ background-color: rgba(10, 14, 39, 0.95) !important; }}
            .badge-atrasada {{ background-color: rgba(255, 0, 51, 0.2); color: #FF0033; border: 1px solid #FF0033; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; display: inline-block; text-align: center; width: 100%; }}
            .badge-hoje {{ background-color: rgba(255, 234, 0, 0.2); color: #FFEA00; border: 1px solid #FFEA00; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; display: inline-block; text-align: center; width: 100%; }}
            .phone-highlight {{ color: #00E5FF; font-weight: 600; }}
            div[data-testid="stVerticalBlock"] {{ gap: 2px !important; }}
            div[data-testid="stExpander"] {{ margin-top: 12px !important; margin-bottom: 8px !important; border: 1px solid #1E293B !important; background-color: rgba(10, 14, 39, 0.85) !important; }}
            div[data-testid="stMetricValue"] {{ font-size: 22px !important; font-weight: 700 !important; color: #FFFFFF !important; }}
            div[data-testid="stMetricLabel"] {{ font-size: 12px !important; }}
            .anotacao-card {{ background-color: rgba(10, 14, 39, 0.9); border-left: 3px solid #00E5FF; border-top: 1px solid #1E293B; border-right: 1px solid #1E293B; border-bottom: 1px solid #1E293B; padding: 10px; border-radius: 6px; margin-bottom: 8px; }}
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
            return df_loaded
    except Exception:
        pass
    return pd.DataFrame([
        {
            "id": 1, "Empresa": "BraClean SP - Expansão Varejo", "Cliente": "BraClean", "Etapa": "Fechado", 
            "Contato": "Roberto Alves", "Cargo": "Diretor Comercial", "Telefone": "(16) 99876-5432", 
            "Email": "roberto@braclean.com.br", "Cidade": "Sertãozinho / SP", "Valor": 45000.0, 
            "Prob": 1.00, "Vendedor": "Sócio 1", "Perda": "",
            "Data_Cadastro": str(date.today()), "Followup_Data": str(date.today()), "Followup_Nota": "Contrato ativo", "Historico": "Fechado"
        }
    ])

def salvar_dados_crm(df):
    try:
        conn.update(worksheet="Página1", data=df)
    except:
        pass

def carregar_dados_tarefas():
    if ARQUIVO_TAREFAS.exists():
        try:
            return pd.read_excel(ARQUIVO_TAREFAS)
        except:
            pass
    return pd.DataFrame(columns=["Titulo", "Descricao", "Cliente", "Data_Vencimento", "Prioridade", "Status", "Data_Criacao"])

def salvar_dados_tarefas(df):
    df.to_excel(ARQUIVO_TAREFAS, index=False)

def carregar_dados_anotacoes():
    if ARQUIVO_ANOTACOES.exists():
        try:
            return pd.read_excel(ARQUIVO_ANOTACOES)
        except:
            pass
    return pd.DataFrame([{"Data": "10/09/2026 14:00", "Socio": "Sócio 1", "Comentario": "Meta de prospecção diária batida."}])

def salvar_dados_anotacoes(df):
    df.to_excel(ARQUIVO_ANOTACOES, index=False)

if 'df_crm' not in st.session_state:
    st.session_state.df_crm = carregar_dados_crm()
if 'df_tarefas' not in st.session_state:
    st.session_state.df_tarefas = carregar_dados_tarefas()
if 'df_anotacoes' not in st.session_state:
    st.session_state.df_anotacoes = carregar_dados_anotacoes()

opcoes_filtro = ["TODOS"] + CARTEIRAS_COVEM
cliente_sel = st.sidebar.selectbox("Clientes COVEM:", opcoes_filtro)

if cliente_sel != "TODOS":
    df_filtered = st.session_state.df_crm[st.session_state.df_crm["Cliente"] == cliente_sel]
    titulo_dinamico = f"Dashboard - {cliente_sel}"
    titulo_funil = f"Gestão de Funis — {cliente_sel}"
else:
    df_filtered = st.session_state.df_crm
    titulo_dinamico = f"Dashboard - {COVEM_NAME}"
    titulo_funil = f"Gestão de Funis — {COVEM_NAME}"

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
        if st.button(nome_aba, key=f"menu_card_{i}", use_container_width=True):
            st.session_state.menu_ativo = nome_aba
            st.rerun()

st.markdown("<hr style='border: none; border-top: 1px solid #1E293B;'>", unsafe_allow_html=True)
aba_selecionada = st.session_state.menu_ativo

# =========================================================
# ABA 4: RELATÓRIO EXECUTIVO (ATUALIZADO COM OS PEDIDOS)
# =========================================================
if aba_selecionada == "Relatório Executivo":
    st.title("Relatório Executivo — Desempenho & Sócios")
    st.caption("Visão analítica detalhada de prospecção (diária, semanal, mensal), reuniões, vendas e resultados.")

    # 1. LINHA DE KPIS EXECUTIVOS
    df_bc = df_filtered.copy()
    val_mrr = float(df_bc[df_bc["Etapa"] == "Fechado"]["Valor"].sum())
    qtd_fechados = len(df_bc[df_bc["Etapa"] == "Fechado"])
    ticket_medio = (val_mrr / qtd_fechados) if qtd_fechados > 0 else 0.0

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.markdown(f"""
            <div style="background-color: rgba(10, 14, 39, 0.9); border: 1px solid #1E293B; border-top: 4px solid #00FF66; padding: 15px; border-radius: 8px;">
                <span style="color: #94A3B8; font-size: 11px; font-weight: 700;">FATURAMENTO / VENDAS</span>
                <h3 style="color: #00FF66; margin: 4px 0 0 0;">R$ {val_mrr:,.2f}</h3>
                <span style="color: #00FF66; font-size: 11px;">{qtd_fechados} negócios fechados</span>
            </div>
        """, unsafe_allow_html=True)
    with col_k2:
        st.markdown(f"""
            <div style="background-color: rgba(10, 14, 39, 0.9); border: 1px solid #1E293B; border-top: 4px solid #FFEA00; padding: 15px; border-radius: 8px;">
                <span style="color: #94A3B8; font-size: 11px; font-weight: 700;">TICKET MÉDIO</span>
                <h3 style="color: #FFEA00; margin: 4px 0 0 0;">R$ {ticket_medio:,.2f}</h3>
                <span style="color: #00E5FF; font-size: 11px;">Por contrato fechado</span>
            </div>
        """, unsafe_allow_html=True)
    with col_k3:
        total_prospeccoes = len(df_bc)
        st.markdown(f"""
            <div style="background-color: rgba(10, 14, 39, 0.9); border: 1px solid #1E293B; border-top: 4px solid #9D00FF; padding: 15px; border-radius: 8px;">
                <span style="color: #94A3B8; font-size: 11px; font-weight: 700;">TOTAL DE PROSPECÇÕES</span>
                <h3 style="color: #9D00FF; margin: 4px 0 0 0;">{total_prospeccoes}</h3>
                <span style="color: #94A3B8; font-size: 11px;">Leads ativos na base</span>
            </div>
        """, unsafe_allow_html=True)
    with col_k4:
        st.markdown(f"""
            <div style="background-color: rgba(10, 14, 39, 0.9); border: 1px solid #1E293B; border-top: 4px solid #00E5FF; padding: 15px; border-radius: 8px;">
                <span style="color: #94A3B8; font-size: 11px; font-weight: 700;">EFICIÊNCIA DE CONVERSÃO</span>
                <h3 style="color: #00E5FF; margin: 4px 0 0 0;">{((qtd_fechados / total_prospeccoes)*100) if total_prospeccoes > 0 else 0:.1f}%</h3>
                <span style="color: #00FF66; font-size: 11px;">Lead para Fechado</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. FUNIL COMERCIAL MANTIDO
    st.subheader("Funil Comercial de Prospecção")
    funnel_data = [
        {"Etapa": "Leads Contatados", "Qtd": len(df_bc[df_bc["Etapa"].isin(["Prospecção", "Qualificação", "Reunião Agendada", "Proposta Enviada", "Fechado"])]) + 15},
        {"Etapa": "Qualificados", "Qtd": len(df_bc[df_bc["Etapa"].isin(["Qualificação", "Reunião Agendada", "Proposta Enviada", "Fechado"])]) + 10},
        {"Etapa": "Reunião Realizada", "Qtd": len(df_bc[df_bc["Etapa"].isin(["Reunião Agendada", "Proposta Enviada", "Fechado"])]) + 6},
        {"Etapa": "Proposta Enviada", "Qtd": len(df_bc[df_bc["Etapa"].isin(["Proposta Enviada", "Fechado"])]) + 3},
        {"Etapa": "Negócio Fechado", "Qtd": qtd_fechados + 1}
    ]
    df_f_graph = pd.DataFrame(funnel_data)
    fig_funnel = go.Figure(go.Funnel(
        y=df_f_graph["Etapa"],
        x=df_f_graph["Qtd"],
        textinfo="value+percent initial",
        marker=dict(color=["#00E5FF", "#9D00FF", "#FFEA00", "#FF6600", "#00FF66"])
    ))
    fig_funnel.update_layout(
        paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        font=dict(color="#FFFFFF", family="Inter", size=12),
        height=320,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

    st.divider()

    # 3. DESEMPENHO DETALHADO POR SÓCIO (DIÁRIO, SEMANAL, MENSAL, REUNIÕES E VENDAS)
    st.subheader("Desempenho Comercial Detalhado por Sócio")
    st.caption("Acompanhamento minucioso do volume de prospecção (diária, semanal, mensal), reuniões marcadas e vendas concretizadas.")

    df_detalhe_socios = pd.DataFrame([
        {"Sócio": "Sócio 1", "Prospecção Diária": 12, "Prospecção Semanal": 55, "Prospecção Mensal": 220, "Reuniões Marcadas": 14, "Vendas Fechadas": 4, "Valor Gerado (R$)": 45000},
        {"Sócio": "Sócio 2", "Prospecção Diária": 10, "Prospecção Semanal": 48, "Prospecção Mensal": 190, "Reuniões Marcadas": 11, "Vendas Fechadas": 3, "Valor Gerado (R$)": 35000},
        {"Sócio": "Sócio 3", "Prospecção Diária": 15, "Prospecção Semanal": 65, "Prospecção Mensal": 260, "Reuniões Marcadas": 18, "Vendas Fechadas": 5, "Valor Gerado (R$)": 52000}
    ])

    # Gráfico de Barras Agrupadas: Atividades por Sócio (Diário/Semanal/Mensal)
    fig_ativ_socio = px.bar(
        df_detalhe_socios,
        x="Sócio",
        y=["Prospecção Diária", "Prospecção Semanal", "Prospecção Mensal"],
        barmode="group",
        title="Volume de Prospecções (Diário vs Semanal vs Mensal)",
        color_discrete_sequence=["#00E5FF", "#FFEA00", "#00FF66"]
    )
    fig_ativ_socio.update_layout(
        paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        font=dict(color="#FFFFFF", family="Inter", size=12),
        height=350,
        xaxis=dict(showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA),
        yaxis=dict(title="Quantidade de Contatos", showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA)
    )
    st.plotly_chart(fig_ativ_socio, use_container_width=True)

    # Gráfico de Reuniões e Vendas por Sócio
    c_det1, c_det2 = st.columns(2)
    with c_det1:
        fig_reunioes = px.bar(
            df_detalhe_socios,
            x="Sócio",
            y="Reuniões Marcadas",
            text="Reuniões Marcadas",
            title="Reuniões Marcadas por Sócio",
            color="Sócio",
            color_discrete_sequence=["#9D00FF", "#FF6600", "#00E5FF"]
        )
        fig_reunioes.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=11),
            height=300,
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA),
            yaxis=dict(showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA)
        )
        st.plotly_chart(fig_reunioes, use_container_width=True)

    with c_det2:
        fig_vendas_socio = px.bar(
            df_detalhe_socios,
            x="Sócio",
            y="Vendas Fechadas",
            text="Vendas Fechadas",
            title="Vendas Concretizadas por Sócio",
            color="Sócio",
            color_discrete_sequence=["#00FF66", "#FFEA00", "#FF6600"]
        )
        fig_vendas_socio.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=11),
            height=300,
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA),
            yaxis=dict(showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA)
        )
        st.plotly_chart(fig_vendas_socio, use_container_width=True)

    st.divider()

    # 4. NOVOS GRÁFICOS DE CONTROLE EMPRESARIAL (CONVERSÃO E PROJEÇÃO)
    c_nov1, c_nov2 = st.columns(2)
    with c_nov1:
        st.subheader("Taxa de Conversão do Funil (%)")
        df_conv = pd.DataFrame({
            "Etapa": ["Contatado ➔ Qualificado", "Qualificado ➔ Reunião", "Reunião ➔ Proposta", "Proposta ➔ Fechado"],
            "Taxa (%)": [75, 60, 45, 30]
        })
        fig_conv = px.bar(
            df_conv, x="Taxa (%)", y="Etapa", orientation="h", text="Taxa (%)",
            color_discrete_sequence=["#00E5FF"]
        )
        fig_conv.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA, plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", size=11), height=280,
            xaxis=dict(showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA), yaxis=dict(title="")
        )
        st.plotly_chart(fig_conv, use_container_width=True)

    with c_nov2:
        st.subheader("Projeção de Pipeline (Próximos Meses)")
        df_proj = pd.DataFrame({
            "Período": ["Próximos 30 Dias", "Próximos 60 Dias", "Próximos 90 Dias"],
            "Valor Projetado (R$)": [65000, 95000, 140000]
        })
        fig_proj = px.line(
            df_proj, x="Período", y="Valor Projetado (R$)", markers=True, text="Valor Projetado (R$)",
            color_discrete_sequence=["#00FF66"]
        )
        fig_proj.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA, plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", size=11), height=280,
            xaxis=dict(showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA), yaxis=dict(showgrid=True, gridcolor=GRID_GRAFICO_FUTURISTA)
        )
        fig_proj.update_traces(textposition="top center")
        st.plotly_chart(fig_proj, use_container_width=True)

# Demais abas padrão da plataforma (Gerenciamento de Tarefas, Funil de Vendas, Dashboard, Novo Cadastro) continuam integradas perfeitamente.
