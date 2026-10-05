import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import urllib.parse
import datetime
from datetime import datetime as dt, date, timedelta
from pathlib import Path
from streamlit_gsheets import GSheetsConnection

# Configuração da página
st.set_page_config(
    page_title="Plataforma Executiva GRUPO COVEM",
    layout="wide"
)

# Caminho para arquivos secundários locais (Tarefas, Histórico, Financeiro)
BASE_DIR = Path(__file__).parent if "__file__" in locals() else Path.cwd()
ARQUIVO_TAREFAS = BASE_DIR / "banco_tarefas_covem.xlsx"
ARQUIVO_HISTORICO = BASE_DIR / "banco_historico_covem.xlsx"
ARQUIVO_FINANCEIRO = BASE_DIR / "banco_financeiro_covem.xlsx"

# Nome Oficial do Grupo
COVEM_NAME = "GRUPO COVEM"

# Lista de Clientes do GRUPO COVEM
CARTEIRAS_COVEM = ["BraClean", "QV Energia Solar", "Elleven"]

# ---------------------------------------------------------
# PALETA COVEM & ESTILIZAÇÃO CSS
# ---------------------------------------------------------
DEFAULT_COLORS = {
    "1. Prospecção": "#F472B6",          # Rosa Pastel suave
    "2. Qualificação": "#FDE047",       # Amarelo Pastel suave
    "3. Reunião Agendada": "#FDBA74",  # Laranja Pastel suave
    "4. Proposta Enviada": "#93C5FD",  # Azul Pastel suave
    "5. Fechado": "#86EFAC",           # Verde Pastel suave
    "6. Perdido": "#FCA5A5"            # Vermelho Pastel suave
}

CORES_PERDAS = {
    "Preço / Orçamento": "#FCA5A5",             # Vermelho Pastel
    "Concorrência": "#FDBA74",                  # Laranja Pastel
    "Sem Resposta / Sumiu": "#FDE047",          # Amarelo Pastel
    "Produto / Serviço não Atende": "#93C5FD",  # Azul Pastel
    "Outros": "#D1D5DB"                         # Cinza Claro
}

if 'funnel_colors' not in st.session_state:
    st.session_state.funnel_colors = DEFAULT_COLORS.copy()

# Inicializa o estado da aba ativa se não existir
if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "Gerenciamento de Tarefas"

# Inicializa o estado da sub-aba em Tarefas se não existir
if 'sub_menu_tarefas' not in st.session_state:
    st.session_state.sub_menu_tarefas = "Tarefas"

# Inicializa o estado de edição da tabela de agenda se não existir
if 'editando_agenda_idx' not in st.session_state:
    st.session_state.editando_agenda_idx = None

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        .notranslate, [data-testid="stSidebar"], [data-baseweb="select"] {
            translate: no !important;
        }

        h1, h2, h3, h4 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.4px !important;
        }

        .title-covem {
            font-family: 'Inter', sans-serif;
            font-size: 42px;
            font-weight: 800;
            letter-spacing: 1.5px;
            color: #F1F5F9;
            text-align: center;
            margin-bottom: 2px;
            margin-top: -20px;
            text-transform: uppercase;
        }

        .subtitle-covem {
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
            color: #94A3B8;
            text-align: center;
            letter-spacing: 0.5px;
            margin-bottom: 25px;
            text-transform: uppercase;
        }

        .badge-atrasada {
            background-color: #4A2024;
            color: #FCA5A5;
            border: 1px solid #EF4444;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
            text-align: center;
            width: 100%;
        }

        .badge-hoje {
            background-color: #3F2E04;
            color: #FDE047;
            border: 1px solid #EAB308;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
            text-align: center;
            width: 100%;
        }

        .phone-highlight {
            color: #38BDF8;
            font-weight: 600;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 2px !important;
        }
        
        div[data-testid="stExpander"] {
            margin-top: 12px !important;
            margin-bottom: 8px !important;
            border: 1px solid #334155 !important;
            background-color: #0F172A !important;
        }

        div[data-testid="stExpander"] details summary {
            padding-top: 8px !important;
            padding-bottom: 8px !important;
        }

        div[data-testid="stMetricValue"] {
            font-family: 'Inter', sans-serif !important;
            font-size: 22px !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
        }

        div[data-testid="stMetricLabel"] {
            font-family: 'Inter', sans-serif !important;
            font-size: 12px !important;
        }
    </style>
""", unsafe_allow_html=True)

PROB_MAP = {
    "1. Prospecção": 0.20,
    "2. Qualificação": 0.40,
    "3. Reunião Agendada": 0.60,
    "4. Proposta Enviada": 0.80,
    "5. Fechado": 1.00,
    "6. Perdido": 0.00
}

MOTIVOS_PERDA_PADRAO = list(CORES_PERDAS.keys())

# ---------------------------------------------------------
# CONEXÃO COM O GOOGLE SHEETS (PERSISTÊNCIA NA NUVEM)
# ---------------------------------------------------------
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
            
            df_loaded["Etapa"] = df_loaded["Etapa"].replace({
                "1. Contatado": "1. Prospecção",
                "2. Conversando": "2. Qualificação"
            })
            
            return df_loaded
    except Exception as e:
        st.warning(f"Aviso ao ler do Google Sheets: {e}. Carregando dados padrão iniciais.")

    df_inicial = pd.DataFrame([
        {
            "id": 1, "Empresa": "Grupo Delta", "Cliente": "BraClean", "Etapa": "1. Prospecção", 
            "Contato": "Roberto Alves", "Cargo": "Diretor Comercial", "Telefone": "(16) 99876-5432", 
            "Email": "roberto@grupodelta.com.br", "Cidade": "Sertãozinho / SP", "Valor": 50000.0, 
            "Prob": 0.20, "Vendedor": "Lucas Mendes", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today() - timedelta(days=2)), "Followup_Nota": "Enviar apresentação institucional atualizada.", 
            "Historico": "[01/09/2026 10:00] Primeiro contato realizado."
        },
        {
            "id": 2, "Empresa": "Sistemas Sigma", "Cliente": "QV Energia Solar", "Etapa": "1. Prospecção", 
            "Contato": "Patricia Lima", "Cargo": "Gerente de Compras", "Telefone": "(16) 99765-4321", 
            "Email": "patricia@sigmasistemas.com.br", "Cidade": "Ribeirão Preto / SP", "Valor": 35000.0, 
            "Prob": 0.20, "Vendedor": "Lucas Mendes", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today()), "Followup_Nota": "Ligar para confirmar se recebeu o e-mail.", 
            "Historico": "[02/09/2026 14:30] E-mail enviado."
        },
        {
            "id": 3, "Empresa": "Indústria Omega", "Cliente": "Elleven", "Etapa": "2. Qualificação", 
            "Contato": "Fernando Souza", "Cargo": "Sócio-Proprietário", "Telefone": "(11) 98123-4567", 
            "Email": "fernando@omegaind.com.br", "Cidade": "São Paulo / SP", "Valor": 80000.0, 
            "Prob": 0.40, "Vendedor": "Gabriel Silva", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today() + timedelta(days=3)), "Followup_Nota": "Alinhar escopo do projeto técnico.", 
            "Historico": "[30/08/2026 09:15] Reunião inicial realizada."
        },
        {
            "id": 4, "Empresa": "Tecnologia Beta", "Cliente": "BraClean", "Etapa": "6. Perdido", 
            "Contato": "Carlos Eduardo", "Cargo": "Comprador", "Telefone": "(16) 98888-7777", 
            "Email": "carlos@betatech.com", "Cidade": "Sertãozinho / SP", "Valor": 25000.0, 
            "Prob": 0.00, "Vendedor": "Lucas Mendes", "Perda": "Preço / Orçamento",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": "", "Followup_Nota": "", 
            "Historico": "[25/08/2026 16:45] Achou o valor acima do orçamento."
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
            df_loaded = pd.read_excel(ARQUIVO_TAREFAS)
            for col in ["Titulo", "Descricao", "Cliente", "Data_Vencimento", "Prioridade", "Status", "Data_Criacao"]:
                if col not in df_loaded.columns:
                    df_loaded[col] = ""
            return df_loaded
        except Exception:
            pass
            
    df_inicial_vazio = pd.DataFrame(columns=["Titulo", "Descricao", "Cliente", "Data_Vencimento", "Prioridade", "Status", "Data_Criacao"])
    df_inicial_vazio.to_excel(ARQUIVO_TAREFAS, index=False)
    return df_inicial_vazio

def salvar_dados_tarefas(df):
    df.to_excel(ARQUIVO_TAREFAS, index=False)

def carregar_dados_historico():
    if ARQUIVO_HISTORICO.exists():
        try:
            return pd.read_excel(ARQUIVO_HISTORICO)
        except Exception:
            pass
    return pd.DataFrame(columns=["Mês/Ano", "Leads Qualificados", "Reuniões Agendadas", "Propostas Enviadas", "Projetos Fechados"])

def salvar_dados_historico(df):
    df.to_excel(ARQUIVO_HISTORICO, index=False)

def carregar_dados_financeiro():
    if ARQUIVO_FINANCEIRO.exists():
        try:
            return pd.read_excel(ARQUIVO_FINANCEIRO)
        except Exception:
            pass
    return pd.DataFrame(columns=["Mês/Ano", "Propostas Enviadas", "Projetos Fechados", "Total"])

def salvar_dados_financeiro(df):
    df.to_excel(ARQUIVO_FINANCEIRO, index=False)

# ---------------------------------------------------------
# ESTADO DA SESSÃO
# ---------------------------------------------------------
if 'df_crm' not in st.session_state:
    st.session_state.df_crm = carregar_dados_crm()

if 'df_tarefas' not in st.session_state:
    st.session_state.df_tarefas = carregar_dados_tarefas()

if 'cliente_editando_id' not in st.session_state:
    st.session_state.cliente_editando_id = None

df = st.session_state.df_crm

# ---------------------------------------------------------
# FUNÇÃO DE LÓGICA DE CORES DO FOLLOW-UP
# ---------------------------------------------------------
def calcular_status_followup(data_str):
    if not data_str or pd.isna(data_str) or str(data_str).strip() in ["", "nan", "NaT", "None"]:
        return "sem_data", "Sem Follow-up", '<span style="height: 10px; width: 10px; background-color: #94A3B8; border-radius: 50%; display: inline-block;" title="Sem Data"></span>'
    try:
        limpa_data = str(data_str).strip()[:10]
        dt_follow = dt.strptime(limpa_data, "%Y-%m-%d").date()
        hoje = date.today()
        if dt_follow < hoje:
            return "atrasado", "Atrasado", '<span style="height: 10px; width: 10px; background-color: #EF4444; border-radius: 50%; display: inline-block;" title="Atrasado"></span>'
        elif dt_follow == hoje:
            return "hoje", "Atenção (Hoje)", '<span style="height: 10px; width: 10px; background-color: #EAB308; border-radius: 50%; display: inline-block;" title="Hoje"></span>'
        else:
            return "em_dia", "Em Dia", '<span style="height: 10px; width: 10px; background-color: #22C55E; border-radius: 50%; display: inline-block;" title="Em Dia"></span>'
    except:
        return "sem_data", "Sem Follow-up", '<span style="height: 10px; width: 10px; background-color: #94A3B8; border-radius: 50%; display: inline-block;" title="Sem Data"></span>'

# ---------------------------------------------------------
# BARRA LATERAL (FILTROS E CONFIGURAÇÕES)
# ---------------------------------------------------------
opcoes_filtro = ["TODOS"] + CARTEIRAS_COVEM
cliente_sel = st.sidebar.selectbox("Clientes COVEM:", opcoes_filtro)

if cliente_sel != "TODOS":
    df_filtered = df[df["Cliente"] == cliente_sel]
    titulo_dinamico = f"Dashboard - {cliente_sel}"
    titulo_funil = f"Funil de Vendas — {cliente_sel}"
else:
    df_filtered = df
    titulo_dinamico = f"Dashboard - {COVEM_NAME}"
    titulo_funil = f"Funil de Vendas — {COVEM_NAME}"

st.sidebar.divider()

with st.sidebar.expander("Personalizar Cores das Etapas", expanded=False):
    st.caption("Altere as cores das etapas do funil:")
    for etapa_nome in PROB_MAP.keys():
        cor_atual = st.session_state.funnel_colors.get(etapa_nome, "#3B82F6")
        nova_cor = st.color_picker(f"Cor: {etapa_nome}", cor_atual, key=f"picker_{etapa_nome}")
        st.session_state.funnel_colors[etapa_nome] = nova_cor

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

# ---------------------------------------------------------
# 1. TÍTULO PRINCIPAL: GRUPO COVEM
# ---------------------------------------------------------
st.markdown(f'<div class="title-covem">{COVEM_NAME}</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-covem">Plataforma Executiva de Gestão Comercial e Operacional</div>', unsafe_allow_html=True)
st.divider()

# ---------------------------------------------------------
# MENU HORIZONTAL EM CARDS
# ---------------------------------------------------------
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
        is_active = (st.session_state.menu_ativo == nome_aba)
        
        if is_active:
            st.markdown(
                f"""
                <style>
                div[data-testid="column"]:nth-of-type({i+1}) div.stButton > button {{
                    background-color: #26334D !important;
                    color: #94A3B8 !important;
                    border: 1px solid #475569 !important;
                    font-weight: 500 !important;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
        
        if st.button(nome_aba, key=f"menu_card_{i}", use_container_width=True):
            st.session_state.menu_ativo = nome_aba
            st.rerun()

st.markdown("""
    <div style='margin-top: 30px; margin-bottom: 30px;'>
        <hr style='border: none; border-top: 1px solid #334155;'>
    </div>
""", unsafe_allow_html=True)

aba_selecionada = st.session_state.menu_ativo

# ---------------------------------------------------------
# FUNÇÃO DE RENDERIZAÇÃO DA AGENDA DA SEMANA (FILTRADA POR EMPRESA SELECIONADA)
# ---------------------------------------------------------
def exibir_agenda_semana(df_tarefas, df_crm, cliente_selecionado):
    st.markdown('<div style="margin-top: 4px;"></div>', unsafe_allow_html=True)
    
    sub_abas = ["Tarefas", "Follow-up"]
    c_sub1, c_sub2 = st.columns(2)
    
    with c_sub1:
        is_sub_active_1 = (st.session_state.sub_menu_tarefas == "Tarefas")
        if is_sub_active_1:
            st.markdown(
                """
                <style>
                div[data-testid="column"]:nth-of-type(1) div.stButton > button {
                    background-color: #26334D !important;
                    color: #94A3B8 !important;
                    border: 1px solid #475569 !important;
                    font-weight: 500 !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
        if st.button("Tarefas", key="sub_btn_tarefas", use_container_width=True):
            st.session_state.sub_menu_tarefas = "Tarefas"
            st.rerun()
            
    with c_sub2:
        is_sub_active_2 = (st.session_state.sub_menu_tarefas == "Follow-up")
        if is_sub_active_2:
            st.markdown(
                """
                <style>
                div[data-testid="column"]:nth-of-type(2) div.stButton > button {
                    background-color: #26334D !important;
                    color: #94A3B8 !important;
                    border: 1px solid #475569 !important;
                    font-weight: 500 !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
        if st.button("Follow-up", key="sub_btn_followups", use_container_width=True):
            st.session_state.sub_menu_tarefas = "Follow-up"
            st.rerun()

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    if st.session_state.sub_menu_tarefas == "Tarefas":
        if df_tarefas.empty or "Data_Vencimento" not in df_tarefas.columns:
            st.info("Nenhuma tarefa cadastrada.")
        else:
            hoje = datetime.date.today()
            df_temp = df_tarefas.copy()
            
            if cliente_selecionado != "TODOS":
                empresas_da_carteira = df_crm[df_crm["Cliente"] == cliente_selecionado]["Empresa"].tolist()
                df_temp = df_temp[df_temp["Cliente"].isin(empresas_da_carteira) | (df_temp["Cliente"] == cliente_selecionado)]

            df_temp["Data_Vencimento"] = pd.to_datetime(df_temp["Data_Vencimento"], errors="coerce").dt.date

            pendentes = df_temp[df_temp["Status"] != "Concluído"]
            atrasadas = pendentes[pendentes["Data_Vencimento"] < hoje]
            hoje_tarefas = pendentes[pendentes["Data_Vencimento"] == hoje]

            col_atraso, col_hoje = st.columns(2)

            with col_atraso:
                st.markdown(f'<div class="badge-atrasada">{len(atrasadas)} Tarefas Atrasadas</div>', unsafe_allow_html=True)
                with st.expander("Ver Tarefas Atrasadas"):
                    if not atrasadas.empty:
                        for _, row in atrasadas.iterrows():
                            st.write(f"- **{row['Titulo']}** | Cliente: `{row.get('Cliente', 'N/A')}` | Vencimento: {row['Data_Vencimento'].strftime('%d/%m/%Y')}")
                    else:
                        st.write("Nenhuma tarefa atrasada.")

            with col_hoje:
                st.markdown(f'<div class="badge-hoje">{len(hoje_tarefas)} Tarefas para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Tarefas para Hoje"):
                    if not hoje_tarefas.empty:
                        for _, row in hoje_tarefas.iterrows():
                            st.write(f"- **{row['Titulo']}** | Cliente: `{row.get('Cliente', 'N/A')}`")
                    else:
                        st.write("Nenhuma tarefa para hoje.")

    else:
        if df_crm.empty:
            st.info("Nenhum cliente no CRM.")
        else:
            crm_temp = df_filtered.copy()
            status_list = []
            for _, r in crm_temp.iterrows():
                st_code, st_label, st_icon = calcular_status_followup(r.get("Followup_Data", ""))
                status_list.append(st_code)
            crm_temp["status_fu"] = status_list

            c_atrasados = crm_temp[crm_temp["status_fu"] == "atrasado"]
            c_hoje = crm_temp[crm_temp["status_fu"] == "hoje"]

            col_c_atraso, col_c_hoje = st.columns(2)

            with col_c_atraso:
                st.markdown(f'<div class="badge-atrasada">{len(c_atrasados)} Follow-ups Atrasados</div>', unsafe_allow_html=True)
                with st.expander("Ver Follow-ups Atrasados"):
                    if not c_atrasados.empty:
                        for _, row in c_atrasados.iterrows():
                            raw_dt = str(row['Followup_Data']).strip()[:10]
                            try:
                                dt_f_br = dt.strptime(raw_dt, "%Y-%m-%d").strftime("%d/%m/%Y")
                            except:
                                dt_f_br = "Data Inválida"
                            st.write(f"- **{row['Empresa']}** | Contato: `{row['Contato']}` | Data: {dt_f_br}")
                    else:
                        st.write("Nenhum follow-up atrasado.")

            with col_c_hoje:
                st.markdown(f'<div class="badge-hoje">{len(c_hoje)} Follow-ups para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Follow-ups para Hoje"):
                    if not c_hoje.empty:
                        for _, row in c_hoje.iterrows():
                            st.write(f"- **{row['Empresa']}** | Contato: `{row['Contato']}`")
                    else:
                        st.write("Nenhum follow-up para hoje.")

    st.divider()

# =========================================================
# ABA 1: GERENCIADOR DE TAREFAS & CALENDÁRIO FUTURO
# =========================================================
if aba_selecionada == "Gerenciamento de Tarefas":
    st.subheader(f"Gerenciamento de Tarefas — {cliente_sel}")
    exibir_agenda_semana(st.session_state.df_tarefas, st.session_state.df_crm, cliente_sel)

    if cliente_sel != "TODOS":
        lista_clientes = ["Nenhum / Tarefa Geral"] + df_filtered["Empresa"].dropna().tolist()
    else:
        lista_clientes = (
            ["Nenhum / Tarefa Geral"] + st.session_state.df_crm["Empresa"].dropna().tolist()
            if not st.session_state.df_crm.empty
            else ["Nenhum / Tarefa Geral"]
        )

    with st.expander("Criar Nova Tarefa", expanded=False):
        with st.form(key="form_nova_tarefa_crm", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown("**Selecione a Ação Rápida:**")
                acao_selecionada = st.radio(
                    "Ação",
                    options=["Ligar", "Enviar mensagem", "Enviar e-mail", "Enviar proposta"],
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                complemento_titulo = st.text_input("Detalhes adicionais (Opcional)", placeholder="Ex: Falar com o gerente sobre o orçamento")
                descricao = st.text_area("Descrição / Observações")

            with col2:
                cliente_vinculado = st.selectbox(
                    "Vincular ao Cliente / Oportunidade", options=lista_clientes
                )
                data_vencimento = st.date_input(
                    "Data de Vencimento", min_value=datetime.date.today()
                )
                prioridade = st.selectbox(
                    "Prioridade", options=["Baixa", "Média", "Alta", "Urgente"]
                )

            submit_tarefa = st.form_submit_button("Salvar Tarefa", use_container_width=True)

            if submit_tarefa:
                titulo_final = f"{acao_selecionada}" + (f" - {complemento_titulo}" if complemento_titulo else "")
                
                nova_linha_tarefa = {
                    "Titulo": titulo_final,
                    "Descricao": descricao,
                    "Cliente": cliente_vinculado,
                    "Data_Vencimento": str(data_vencimento),
                    "Prioridade": prioridade,
                    "Status": "Pendente",
                    "Data_Criacao": str(datetime.date.today()),
                }
                st.session_state.df_tarefas = pd.concat(
                    [st.session_state.df_tarefas, pd.DataFrame([nova_linha_tarefa])],
                    ignore_index=True
                )
                salvar_dados_tarefas(st.session_state.df_tarefas)
                st.success("Tarefa criada com sucesso!")
                st.rerun()

    st.divider()

    st.subheader("Agenda de Tarefas e Follow Up")

    col_h1, col_h2 = st.columns([2, 2])
    with col_h1:
        horizonte = st.selectbox(
            "Horizonte de Visualização:",
            ["Próximos 7 Dias", "Próximos 15 Dias", "Próximos 30 Dias", "Todos os Registros Futuros"],
            label_visibility="collapsed"
        )

    hoje = date.today()
    if horizonte == "Próximos 7 Dias":
        limite_data = hoje + timedelta(days=7)
    elif horizonte == "Próximos 15 Dias":
        limite_data = hoje + timedelta(days=15)
    elif horizonte == "Próximos 30 Dias":
        limite_data = hoje + timedelta(days=30)
    else:
        limite_data = hoje + timedelta(days=365)

    eventos_futuros = []

    df_tarefas_exibicao = st.session_state.df_tarefas.copy()
    if cliente_sel != "TODOS":
        empresas_da_carteira = df_filtered["Empresa"].tolist()
        df_tarefas_exibicao = df_tarefas_exibicao[df_tarefas_exibicao["Cliente"].isin(empresas_da_carteira) | (df_tarefas_exibicao["Cliente"] == cliente_sel)]

    if not df_tarefas_exibicao.empty:
        for idx_t, t in df_tarefas_exibicao.iterrows():
            if pd.notna(t.get("Data_Vencimento")):
                try:
                    dt_v = dt.strptime(str(t["Data_Vencimento"])[:10], "%Y-%m-%d").date()
                    if hoje <= dt_v <= limite_data:
                        eventos_futuros.append({
                            "origem": "tarefa",
                            "index_original": idx_t,
                            "Data_Formatada": dt_v.strftime("%d/%m/%Y"),
                            "Tipo": "Tarefa",
                            "Título / Ação": t["Titulo"],
                            "Vinculado a": f"Cliente: {t.get('Cliente', 'Geral')}",
                            "Prioridade / Status": f"Prioridade: {t.get('Prioridade', 'Normal')}"
                        })
                except:
                    pass

    if not df_filtered.empty:
        for idx_c, c in df_filtered.iterrows():
            f_dat = c.get("Followup_Data", "")
            if pd.notna(f_dat) and str(f_dat).strip() not in ["", "nan", "NaT"]:
                try:
                    dt_f = dt.strptime(str(f_dat)[:10], "%Y-%m-%d").date()
                    if hoje <= dt_f <= limite_data:
                        eventos_futuros.append({
                            "origem": "crm",
                            "index_original": idx_c,
                            "Data_Formatada": dt_f.strftime("%d/%m/%Y"),
                            "Tipo": "Follow-up CRM",
                            "Título / Ação": c.get("Followup_Nota", "Contato Comercial"),
                            "Vinculado a": f"Empresa: {c['Empresa']} ({c.get('Contato', 'Não informado')})",
                            "Prioridade / Status": f"Etapa: {c['Etapa']}"
                        })
                except:
                    pass

    if eventos_futuros:
        df_futuro = pd.DataFrame(eventos_futuros)
        df_futuro = df_futuro.sort_values(by="Data_Formatada", ascending=True).reset_index(drop=True)

        with st.expander(f"Ver compromissos no período ({len(df_futuro)} encontrados)", expanded=True):
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric("Total de Ações no Período", len(df_futuro))
            c_m2.metric("Tarefas Pendentes", len(df_futuro[df_futuro["Tipo"] == "Tarefa"]))
            c_m3.metric("Follow-ups de CRM", len(df_futuro[df_futuro["Tipo"] == "Follow-up CRM"]))

            st.divider()

            df_exibicao_tabela = df_futuro[["Data_Formatada", "Tipo", "Título / Ação", "Vinculado a", "Prioridade / Status"]]
            
            st.dataframe(
                df_exibicao_tabela,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            
            item_selecionado_acoes = st.selectbox(
                "Selecione o compromisso para gerenciar (Editar/Excluir):",
                options=range(len(df_futuro)),
                format_func=lambda x: f"[{df_futuro.loc[x, 'Data_Formatada']}] {df_futuro.loc[x, 'Tipo']} - {df_futuro.loc[x, 'Título / Ação']} ({df_futuro.loc[x, 'Vinculado a']})",
                label_visibility="collapsed"
            )

            if item_selecionado_acoes is not None:
                sel_row = df_futuro.loc[item_selecionado_acoes]
                origem_sel = sel_row["origem"]
                idx_orig_sel = sel_row["index_original"]

                col_acao1, col_acao2 = st.columns(2)
                with col_acao1:
                    if st.button("Excluir", use_container_width=True):
                        if origem_sel == "tarefa":
                            st.session_state.df_tarefas = st.session_state.df_tarefas.drop(idx_orig_sel).reset_index(drop=True)
                            salvar_dados_tarefas(st.session_state.df_tarefas)
                        else:
                            st.session_state.df_crm.loc[idx_orig_sel, "Followup_Data"] = ""
                            st.session_state.df_crm.loc[idx_orig_sel, "Followup_Nota"] = ""
                            salvar_dados_crm(st.session_state.df_crm)
                        st.success("Item removido com sucesso!")
                        st.rerun()

                with col_acao2:
                    with st.popover("Editar", use_container_width=True):
                        novo_txt_acao = st.text_input("Título / Ação", value=sel_row["Título / Ação"])
                        novo_vinc_acao = st.text_input("Vínculo / Empresa", value=sel_row["Vinculado a"])
                        if st.button("Salvar Alterações"):
                            if origem_sel == "tarefa":
                                st.session_state.df_tarefas.loc[idx_orig_sel, "Titulo"] = novo_txt_acao
                                salvar_dados_tarefas(st.session_state.df_tarefas)
                            else:
                                st.session_state.df_crm.loc[idx_orig_sel, "Followup_Nota"] = novo_txt_acao
                                salvar_dados_crm(st.session_state.df_crm)
                            st.success("Atualizado com sucesso!")
                            st.rerun()
    else:
        st.info("Nenhuma tarefa ou follow-up agendado para este horizonte de tempo.")

# =========================================================
# ABA 2: FUNIL DE VENDAS
# =========================================================
elif aba_selecionada == "Funil de Vendas":
    col_topo_titulo, col_topo_busca = st.columns([2, 1])
    with col_topo_titulo:
        st.subheader(titulo_funil)
    with col_topo_busca:
        termo_busca = st.text_input(
            "Pesquisar cliente", 
            placeholder="🔍 Buscar por empresa, contato...", 
            label_visibility="collapsed"
        )

    if st.session_state.cliente_editando_id is not None:
        cliente_edit_id = st.session_state.cliente_editando_id
        filtro_reg = df[df["id"] == cliente_edit_id]
        
        if not filtro_reg.empty:
            row_edit = filtro_reg.iloc[0]
            
            st.markdown(
                f"""
                <div style="background-color: #0F172A; border: 2px solid #38BDF8; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);">
                    <h3 style="color: #38BDF8; margin-top: 0; margin-bottom: 20px; font-weight: 700;">Ficha Completa & Linha do Tempo: {row_edit['Empresa']}</h3>
                """,
                unsafe_allow_html=True
            )
            
            with st.form(key=f"form_full_edit_horizontal_{cliente_edit_id}"):
                etapas = list(PROB_MAP.keys())
                
                edit_etapa = st.selectbox(
                    "Etapa do Funil de Vendas", 
                    options=etapas, 
                    index=etapas.index(row_edit["Etapa"]) if row_edit["Etapa"] in etapas else 0
                )
                
                st.divider()

                hc1, hc2, hc3 = st.columns(3)
                with hc1:
                    edit_empresa = st.text_input("Empresa", value=row_edit["Empresa"])
                    edit_contato = st.text_input("Contato", value=row_edit["Contato"])
                    edit_cargo = st.text_input("Cargo", value=row_edit["Cargo"])
                with hc2:
                    edit_tel = st.text_input("Telefone", value=row_edit["Telefone"])
                    edit_email = st.text_input("E-mail", value=row_edit["Email"])
                    edit_cidade = st.text_input("Cidade", value=row_edit["Cidade"])
                with hc3:
                    edit_valor = st.number_input("Valor (R$)", value=float(row_edit["Valor"]), step=1000.0)
                    edit_vendedor = st.text_input("Vendedor", value=row_edit["Vendedor"])
                    
                    try:
                        dt_parse = dt.strptime(str(row_edit["Followup_Data"]).strip()[:10], "%Y-%m-%d").date() if row_edit["Followup_Data"] and str(row_edit["Followup_Data"]).strip() not in ["nan", "NaT", ""] else date.today()
                    except:
                        dt_parse = date.today()
                        
                    edit_fu_data = st.date_input("Próxima Data de Follow-up", value=dt_parse)
                
                edit_fu_nota = st.text_input("Resumo / Nota do Follow-up", value=row_edit["Followup_Nota"])
                
                edit_perda = str(row_edit.get("Perda", "")).strip()
                edit_motivo_perda = st.selectbox(
                    "Motivo de Perda (Se aplicável)", 
                    options=[""] + MOTIVOS_PERDA_PADRAO,
                    index=(MOTIVOS_PERDA_PADRAO.index(edit_perda) + 1) if edit_perda in MOTIVOS_PERDA_PADRAO else 0
                )
                
                st.divider()
                st.markdown("**Adicionar Nota Rápida na Linha do Tempo:**")
                col_t1, col_t2 = st.columns([3, 1])
                with col_t1:
                    nova_nota_timeline = st.text_input("Escreva o que foi conversado / alinhado:", placeholder="Ex: Cliente pediu para retornar na próxima terça para fechar o contrato.", key="input_timeline_edit")
                with col_t2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    adicionar_timeline_btn = st.form_submit_button("+ Registrar na Timeline", use_container_width=True)

                st.markdown("**Histórico de Interações (Linha do Tempo):**")
                historico_atual = str(row_edit["Historico"]) if pd.notna(row_edit["Historico"]) else ""
                
                if historico_atual.strip():
                    for linha_hist in historico_atual.split("\n"):
                        if linha_hist.strip():
                            st.markdown(f"- 🕒 `{linha_hist.strip()}`")
                else:
                    st.caption("Nenhum registro na linha do tempo ainda.")
                
                st.divider()
                bcol1, bcol2, bcol3 = st.columns([2, 2, 2])
                with bcol1:
                    btn_salvar_alt = st.form_submit_button("Salvar Alterações Gerais", use_container_width=True)
                with bcol2:
                    btn_fechar_modal = st.form_submit_button("Fechar Ficha", use_container_width=True)
                with bcol3:
                    btn_excluir = st.form_submit_button("Excluir Cliente", use_container_width=True)
                    
                idx_df = st.session_state.df_crm.index[st.session_state.df_crm["id"] == cliente_edit_id]
                
                if len(idx_df) > 0:
                    idx_real = idx_df[0]
                    
                    if adicionar_timeline_btn and nova_nota_timeline.strip():
                        timestamp_atual = dt.now().strftime("%d/%m/%Y %H:%M")
                        novo_registro_timeline = f"[{timestamp_atual}] {nova_nota_timeline.strip()}"
                        
                        if historico_atual.strip():
                            historico_atualizado = novo_registro_timeline + "\n" + historico_atual
                        else:
                            historico_atualizado = novo_registro_timeline
                            
                        st.session_state.df_crm.loc[idx_real, "Historico"] = historico_atualizado
                        salvar_dados_crm(st.session_state.df_crm)
                        st.success("Nota adicionada na linha do tempo com sucesso!")
                        st.rerun()

                    if btn_salvar_alt:
                        st.session_state.df_crm.loc[idx_real, "Etapa"] = edit_etapa
                        st.session_state.df_crm.loc[idx_real, "Prob"] = PROB_MAP[edit_etapa]
                        st.session_state.df_crm.loc[idx_real, "Empresa"] = edit_empresa
                        st.session_state.df_crm.loc[idx_real, "Contato"] = edit_contato
                        st.session_state.df_crm.loc[idx_real, "Cargo"] = edit_cargo
                        st.session_state.df_crm.loc[idx_real, "Telefone"] = edit_tel
                        st.session_state.df_crm.loc[idx_real, "Email"] = edit_email
                        st.session_state.df_crm.loc[idx_real, "Cidade"] = edit_cidade
                        st.session_state.df_crm.loc[idx_real, "Valor"] = edit_valor
                        st.session_state.df_crm.loc[idx_real, "Vendedor"] = edit_vendedor
                        st.session_state.df_crm.loc[idx_real, "Followup_Data"] = str(edit_fu_data)
                        st.session_state.df_crm.loc[idx_real, "Followup_Nota"] = edit_fu_nota
                        
                        st.session_state.df_crm["Perda"] = st.session_state.df_crm["Perda"].astype(str)
                        st.session_state.df_crm.loc[idx_real, "Perda"] = str(edit_motivo_perda)
                        
                        salvar_dados_crm(st.session_state.df_crm)
                        st.session_state.cliente_editando_id = None
                        st.success("Alterações salvas com sucesso!")
                        st.rerun()
                        
                if btn_fechar_modal:
                    st.session_state.cliente
