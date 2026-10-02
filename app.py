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
# FUNÇÃO DE LÓGICA DE CORES DO FOLLOW-UP E STATUS DE LEAD
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

def classificar_status_lead(row):
    """
    Classifica o lead com base na data de follow-up e na etapa/probabilidade:
    - Quente: Follow-up para hoje/atrasado ou alta probabilidade.
    - Morno: Follow-up nos próximos 7 dias.
    - Frio: Sem follow-up próximo ou etapas iniciais.
    """
    follow_str = str(row.get("Followup_Data", "")).strip()
    etapa = str(row.get("Etapa", ""))
    prob = float(row.get("Prob", 0.0))
    hoje = date.today()
    
    if "Fechado" in etapa:
        return "Fechado", "#86EFAC"
    if "Perdido" in etapa:
        return "Perdido", "#FCA5A5"
        
    try:
        if follow_str and follow_str not in ["nan", "NaT", ""]:
            dt_follow = dt.strptime(follow_str[:10], "%Y-%m-%d").date()
            dias_diff = (dt_follow - hoje).days
            
            if dias_diff <= 0 or prob >= 0.60:
                return "Quente", "#EF4444"
            elif dias_diff <= 7:
                return "Morno", "#F59E0B"
            else:
                return "Frio", "#3B82F6"
    except:
        pass
        
    if prob >= 0.60:
        return "Quente", "#EF4444"
    elif prob >= 0.40:
        return "Morno", "#F59E0B"
    
    return "Frio", "#3B82F6"

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
# FUNÇÃO DE RENDERIZAÇÃO DA AGENDA DA SEMANA (COM STATUS DE LEADS)
# ---------------------------------------------------------
def exibir_agenda_semana(df_tarefas, df_crm):
    st.markdown('<div style="margin-top: 4px;"></div>', unsafe_allow_html=True)
    
    sub_abas = ["Tarefas", "Follow-up & Leads"]
    c_sub1, c_sub2 = st.columns(2)
    
    with c_sub1:
        if st.session_state.sub_menu_tarefas == "Tarefas":
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
        if st.session_state.sub_menu_tarefas == "Follow-up":
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
        if st.button("Follow-up & Leads", key="sub_btn_followups", use_container_width=True):
            st.session_state.sub_menu_tarefas = "Follow-up"
            st.rerun()

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    if st.session_state.sub_menu_tarefas == "Tarefas":
        if df_tarefas.empty or "Data_Vencimento" not in df_tarefas.columns:
            st.info("Nenhuma tarefa cadastrada.")
        else:
            hoje = datetime.date.today()
            df_temp = df_tarefas.copy()
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
                            cli_nome = str(row.get('Cliente', 'N/A'))
                            tel_encontrado = "Não informado"
                            if not df_crm.empty and cli_nome != "Nenhum / Tarefa Geral":
                                match_cli = df_crm[df_crm["Empresa"].astype(str).str.lower() == cli_nome.lower()]
                                if not match_cli.empty:
                                    tel_encontrado = match_cli.iloc[0].get("Telefone", "Não informado")
                            
                            st.markdown(f"- **{row['Titulo']}** | Cliente: `{cli_nome}` | Tel: <span class=\"phone-highlight\">{tel_encontrado}</span> | Venc: {row['Data_Vencimento'].strftime('%d/%m/%Y')}", unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma tarefa atrasada.")

            with col_hoje:
                st.markdown(f'<div class="badge-hoje">{len(hoje_tarefas)} Tarefas para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Tarefas para Hoje"):
                    if not hoje_tarefas.empty:
                        for _, row in hoje_tarefas.iterrows():
                            cli_nome = str(row.get('Cliente', 'N/A'))
                            tel_encontrado = "Não informado"
                            if not df_crm.empty and cli_nome != "Nenhum / Tarefa Geral":
                                match_cli = df_crm[df_crm["Empresa"].astype(str).str.lower() == cli_nome.lower()]
                                if not match_cli.empty:
                                    tel_encontrado = match_cli.iloc[0].get("Telefone", "Não informado")

                            st.markdown(f"- **{row['Titulo']}** | Cliente: `{cli_nome}` | Tel: <span class=\"phone-highlight\">{tel_encontrado}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma tarefa para hoje.")

    else:
        if df_crm.empty:
            st.info("Nenhum cliente no CRM.")
        else:
            crm_temp = df_crm.copy()
            status_list = []
            classif_list = []
            
            for _, r in crm_temp.iterrows():
                st_code, st_label, st_icon = calcular_status_followup(r.get("Followup_Data", ""))
                status_list.append(st_code)
                
                status_lead_txt, _ = classificar_status_lead(r)
                classif_list.append(status_lead_txt)
                
            crm_temp["status_fu"] = status_list
            crm_temp["status_lead"] = classif_list

            c_quentes = crm_temp[crm_temp["status_lead"] == "Quente"]
            c_mornos = crm_temp[crm_temp["status_lead"] == "Morno"]

            col_q, col_m = st.columns(2)

            with col_q:
                st.markdown(f'<div class="badge-atrasada">{len(c_quentes)} Leads Quentes (Atenção Imediata)</div>', unsafe_allow_html=True)
                with st.expander("Ver Leads Quentes"):
                    if not c_quentes.empty:
                        for _, row in c_quentes.iterrows():
                            tel_cli = row.get('Telefone', 'Não informado')
                            st.markdown(f"- **{row['Empresa']}** | Contato: `{row['Contato']}` | Tel: <span class=\"phone-highlight\">{tel_cli}</span> | Etapa: {row['Etapa']}", unsafe_allow_html=True)
                    else:
                        st.write("Nenhum lead quente no momento.")

            with col_m:
                st.markdown(f'<div class="badge-hoje">{len(c_mornos)} Leads Mornos (Acompanhamento)</div>', unsafe_allow_html=True)
                with st.expander("Ver Leads Mornos"):
                    if not c_mornos.empty:
                        for _, row in c_mornos.iterrows():
                            tel_cli = row.get('Telefone', 'Não informado')
                            st.markdown(f"- **{row['Empresa']}** | Contato: `{row['Contato']}` | Tel: <span class=\"phone-highlight\">{tel_cli}</span> | Etapa: {row['Etapa']}", unsafe_allow_html=True)
                    else:
                        st.write("Nenhum lead morno no momento.")

    st.divider()

# =========================================================
# ABA 1: GERENCIADOR DE TAREFAS & CALENDÁRIO FUTURO
# =========================================================
if aba_selecionada == "Gerenciamento de Tarefas":
    st.subheader("Gerenciamento de Tarefas e Sincronização")
    exibir_agenda_semana(st.session_state.df_tarefas, st.session_state.df_crm)

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
                cliente_vinculado = st.selectbox("Vincular ao Cliente / Oportunidade", options=lista_clientes)
                data_vencimento = st.date_input("Data de Vencimento", min_value=datetime.date.today())
                prioridade = st.selectbox("Prioridade", options=["Baixa", "Média", "Alta", "Urgente"])

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

# =========================================================
# ABA 2: FUNIL DE VENDAS (COM BADGES DE QUENTE/MORNO/FRIO)
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
                <div style="background-color: #0F172A; border: 2px solid #38BDF8; padding: 25px; border-radius: 12px; margin-bottom: 25px;">
                    <h3 style="color: #38BDF8; margin-top: 0; margin-bottom: 20px;">Ficha Completa: {row_edit['Empresa']}</h3>
                """,
                unsafe_allow_html=True
            )
            
            with st.form(key=f"form_full_edit_horizontal_{cliente_edit_id}"):
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
                
                bcol1, bcol2, bcol3 = st.columns([2, 2, 2])
                with bcol1:
                    btn_salvar_alt = st.form_submit_button("Salvar Alterações", use_container_width=True)
                with bcol2:
                    btn_fechar_modal = st.form_submit_button("Fechar Ficha", use_container_width=True)
                with bcol3:
                    btn_excluir = st.form_submit_button("Excluir Cliente", use_container_width=True)
                    
                idx_df = st.session_state.df_crm[st.session_state.df_crm["id"] == cliente_edit_id].index
                
                if btn_salvar_alt:
                    st.session_state.df_crm.loc[idx_df, "Empresa"] = edit_empresa
                    st.session_state.df_crm.loc[idx_df, "Contato"] = edit_contato
                    st.session_state.df_crm.loc[idx_df, "Cargo"] = edit_cargo
                    st.session_state.df_crm.loc[idx_df, "Telefone"] = edit_tel
                    st.session_state.df_crm.loc[idx_df, "Email"] = edit_email
                    st.session_state.df_crm.loc[idx_df, "Cidade"] = edit_cidade
                    st.session_state.df_crm.loc[idx_df, "Valor"] = edit_valor
                    st.session_state.df_crm.loc[idx_df, "Vendedor"] = edit_vendedor
                    st.session_state.df_crm.loc[idx_df, "Followup_Data"] = str(edit_fu_data)
                    st.session_state.df_crm.loc[idx_df, "Followup_Nota"] = edit_fu_nota
                    st.session_state.df_crm["Perda"] = st.session_state.df_crm["Perda"].astype(str)
                    st.session_state.df_crm.loc[idx_df, "Perda"] = str(edit_motivo_perda)
                    
                    salvar_dados_crm(st.session_state.df_crm)
                    st.session_state.cliente_editando_id = None
                    st.success("Alterações salvas!")
                    st.rerun()
                    
                if btn_fechar_modal:
                    st.session_state.cliente_editando_id = None
                    st.rerun()
                    
                if btn_excluir:
                    st.session_state.df_crm = st.session_state.df_crm[st.session_state.df_crm["id"] != cliente_edit_id]
                    salvar_dados_crm(st.session_state.df_crm)
                    st.session_state.cliente_editando_id = None
                    st.warning("Excluído!")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            st.divider()

    df_funil_exibicao = df_filtered.copy()
    if termo_busca:
        termo_limpo = termo_busca.lower()
        df_funil_exibicao = df_funil_exibicao[
            df_funil_exibicao["Empresa"].astype(str).str.lower().str.contains(termo_limpo) |
            df_funil_exibicao["Contato"].astype(str).str.lower().str.contains(termo_limpo)
        ]

    etapas = list(PROB_MAP.keys())
    cols = st.columns(len(etapas))
    
    for idx, etapa in enumerate(etapas):
        cor_header = st.session_state.funnel_colors.get(etapa, "#3B82F6")
        
        with cols[idx]:
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #334155; border-top: 4px solid {cor_header}; padding: 8px; border-radius: 6px; text-align: center; margin-bottom: 16px;">
                    <b style="color: #F8FAFC; font-size: 11px; text-transform: uppercase;">{etapa}</b>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            sub_df = df_funil_exibicao[df_funil_exibicao["Etapa"] == etapa]
            
            for _, row in sub_df.iterrows():
                cliente_id = int(row['id'])
                status_lead_txt, cor_status = classificar_status_lead(row)
                
                st.markdown(f"""
                    <div style="border-left: 4px solid {cor_status}; background-color: #111C31; border: 1px solid #1E293B; border-radius: 4px; margin-bottom: 6px; padding: 4px;">
                """, unsafe_allow_html=True)
                
                with st.expander(f"{row['Empresa']} ({status_lead_txt})"):
                    st.markdown(
                        f"""
                        <div style="line-height: 1.4; font-size: 12px;">
                            <b>Contato:</b> {row['Contato']}<br>
                            <b>Tel:</b> <span class="phone-highlight">{row.get('Telefone', 'N/A')}</span><br>
                            <b>Status:</b> <span style="color: {cor_status}; font-weight: bold;">{status_lead_txt}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    nova_etapa_card = st.selectbox(
                        "Mover Etapa:", 
                        options=etapas, 
                        index=etapas.index(row["Etapa"]), 
                        key=f"mov_etapa_{cliente_id}",
                        label_visibility="collapsed"
                    )
                    
                    if nova_etapa_card != row["Etapa"]:
                        idx_df = st.session_state.df_crm[st.session_state.df_crm["id"] == cliente_id].index
                        st.session_state.df_crm.loc[idx_df, "Etapa"] = nova_etapa_card
                        st.session_state.df_crm.loc[idx_df, "Prob"] = PROB_MAP[nova_etapa_card]
                        salvar_dados_crm(st.session_state.df_crm)
                        st.rerun()

                    if st.button("EDITAR", key=f"btn_edit_{cliente_id}", use_container_width=True):
                        st.session_state.cliente_editando_id = cliente_id
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ABA 3: DASHBOARD
# =========================================================
elif aba_selecionada == "Dashboard":
    st.markdown(f'<div class="notranslate"><h3>{titulo_dinamico}</h3></div>', unsafe_allow_html=True)
    st.info("Painel de métricas consolidado com base na distribuição dos leads.")

# =========================================================
# ABA 4: RELATÓRIO EXECUTIVO
# =========================================================
elif aba_selecionada == "Relatório Executivo":
    st.title("Relatório Executivo")
    st.info("Visão consolidada do histórico de atividades e faturamento.")

# =========================================================
# ABA 5: + NOVO CADASTRO
# =========================================================
elif aba_selecionada == "+ Novo Cadastro":
    st.subheader("+ Novo Cadastro de Oportunidade")
    
    with st.form("form_oportunidade", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            nova_empresa = st.text_input("Nome da Empresa / Cliente *")
            novo_cliente = st.selectbox("Marca / Carteira *", CARTEIRAS_COVEM)
            novo_contato = st.text_input("Contato / Nome")
            novo_telefone = st.text_input("Telefone de Contato *")
            
        with col_f2:
            nova_valor = st.number_input("Valor da Oportunidade (R$)", min_value=0.0, step=1000.0)
            nova_etapa = st.selectbox("Etapa Inicial *", list(PROB_MAP.keys()))
            f_data_ini = st.date_input("Data de Follow-up", value=date.today())

        btn_salvar = st.form_submit_button("Salvar Oportunidade")
        
        if btn_salvar:
            if not nova_empresa or not novo_telefone:
                st.error("Preencha a Empresa e o Telefone.")
            else:
                novo_id = int(df["id"].max() + 1) if not df.empty and pd.notna(df["id"].max()) else 1
                nova_linha = {
                    "id": novo_id,
                    "Empresa": nova_empresa,
                    "Cliente": novo_cliente,
                    "Etapa": nova_etapa,
                    "Contato": novo_contato or "Não informado",
                    "Cargo": "Não informado",
                    "Telefone": novo_telefone,
                    "Email": "Não informado",
                    "Cidade": "Não informado",
                    "Valor": nova_valor,
                    "Prob": PROB_MAP[nova_etapa],
                    "Vendedor": "Não informado",
                    "Perda": "",
                    "Data_Cadastro": str(date.today()),
                    "Followup_Data": str(f_data_ini),
                    "Followup_Nota": "Novo cadastro sincronizado.",
                    "Historico": f"[{dt.now().strftime('%d/%m/%Y %H:%M')}] Oportunidade criada."
                }
                st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_dados_crm(st.session_state.df_crm)
                st.success("Oportunidade cadastrada com sucesso!")
                st.rerun()
