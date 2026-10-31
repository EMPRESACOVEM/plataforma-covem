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
    page_title="COVEM",
    layout="wide"
)

# Caminho para arquivos secundários locais
BASE_DIR = Path(__file__).parent if "__file__" in locals() else Path.cwd()
ARQUIVO_TAREFAS = BASE_DIR / "banco_tarefas_braclean.xlsx"
ARQUIVO_FUNDO = BASE_DIR / "fundo plataforma.jpg"
ARQUIVO_LOGO = BASE_DIR / "logoCOVEM.png"

# Nome Oficial / Exclusivo
COVEM_NAME = "GRUPO COVEM"

# Apenas a BraClean como carteira ativa
CARTEIRAS_COVEM = ["BraClean"]

# Opções Oficiais de Classificação do Lead
OPCOES_PERFIL = [
    "Cliente A",
    "Cliente B",
    "Cliente C"
]

MAPA_PERFIL_CURTO = {
    "Cliente A": "Cliente A",
    "Cliente B": "Cliente B",
    "Cliente C": "Cliente C"
}

# Ticket médio estimado padrão por perfil para estatísticas de funil
TICKET_MEDIO_PERFIL = {
    "Cliente A": 120000.0,
    "Cliente B": 45000.0,
    "Cliente C": 8500.0
}

# ---------------------------------------------------------
# PALETA DE CORES NEON PERSONALIZADA POR ETAPA
# ---------------------------------------------------------
DEFAULT_COLORS = {
    # Pré Funil
    "Pré: Novo Lead": "#00E5FF",         # Azul Claro Neon
    "Pré: Conexão": "#0047AB",           # Azul Escuro Neon

    # Funil Principal
    "Prospecção": "#9D00FF",             # Roxo Neon
    "Qualificação": "#FF007F",          # Rosa Neon
    "Reunião Agendada": "#FFEA00",     # Amarelo Neon
    "Proposta Enviada": "#FF6600",     # Laranja Neon
    "Fechado": "#00FF66",              # Verde Neon

    # Pós Funil
    "Pós: Standby": "#FFFFFF",          # Branco Neon
    "Pós: Perdido": "#FF0033"           # Vermelho Neon
}

CORES_PERDAS = {
    "Preço / Orçamento": "#FF0033",             # Vermelho Neon
    "Concorrência": "#FF6600",                  # Laranja Neon
    "Sem Resposta / Sumiu": "#FFEA00",          # Amarelo Neon
    "Produto / Serviço não Atende": "#00E5FF",  # Azul Claro Neon
    "Outros": "#9D00FF"                         # Roxo Neon
}

# Cores das Barras de Classificação de Clientes
CORES_PERFIL_BARRAS = {
    "Cliente A": "#00E5FF",  # Azul Claro Neon
    "Cliente B": "#FF6600",  # Laranja Neon
    "Cliente C": "#9D00FF"   # Roxo Neon
}

# Cor de fundo dos gráficos estilo Infográfico Futurista
FUNDO_GRAFICO_FUTURISTA = "#0A0E27"
GRID_GRAFICO_FUTURISTA = "rgba(0, 229, 255, 0.12)"

# Força a atualização das cores e estrutura na sessão
st.session_state.funnel_colors = DEFAULT_COLORS.copy()

if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "Gerenciamento de Tarefas"

if 'funnel_selecionado' not in st.session_state:
    st.session_state.funnel_selecionado = "Funil de Vendas"

if 'sub_menu_tarefas' not in st.session_state:
    st.session_state.sub_menu_tarefas = "Tarefas"

if 'editando_agenda_idx' not in st.session_state:
    st.session_state.editando_agenda_idx = None

# Função para carregar a imagem de fundo local via Base64
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
    # Pré Funil
    "Pré: Novo Lead": 0.05,
    "Pré: Conexão": 0.10,

    # Funil de Vendas Principal
    "Prospecção": 0.20,
    "Qualificação": 0.40,
    "Reunião Agendada": 0.60,
    "Proposta Enviada": 0.80,
    "Fechado": 1.00,

    # Pós Funil
    "Pós: Standby": 0.00,
    "Pós: Perdido": 0.00
}

ESTRUTURA_FUNIS = {
    "Pré Funil": ["Pré: Novo Lead", "Pré: Conexão"],
    "Funil de Vendas": ["Prospecção", "Qualificação", "Reunião Agendada", "Proposta Enviada", "Fechado"],
    "Pós Funil": ["Pós: Standby", "Pós: Perdido"]
}

MOTIVOS_PERDA_PADRAO = list(CORES_PERDAS.keys())

# ---------------------------------------------------------
# CONEXÃO COM O GOOGLE SHEETS
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
        
        colunas_esperadas = ["id", "Empresa", "Cliente", "Perfil", "Etapa", "Contato", "Cargo", "Telefone", "Email", "Cidade", "Valor", "Prob", "Vendedor", "Perda", "Data_Cadastro", "Followup_Data", "Followup_Nota", "Historico"]
        for col in colunas_esperadas:
            if col not in df_loaded.columns:
                df_loaded[col] = ""
                
        if not df_loaded.empty:
            df_loaded["id"] = pd.to_numeric(df_loaded["id"], errors="coerce").fillna(0).astype(int)
            df_loaded["Valor"] = pd.to_numeric(df_loaded["Valor"], errors="coerce").fillna(0.0)
            df_loaded["Prob"] = pd.to_numeric(df_loaded["Prob"], errors="coerce").fillna(0.2)
            df_loaded["Perda"] = df_loaded["Perda"].fillna("").astype(str)
            df_loaded["Perfil"] = df_loaded["Perfil"].fillna("Cliente C").astype(str)
            
            # FILTRAGEM AUTOMÁTICA: Remove qualquer registro antigo que não seja da BraClean
            df_loaded["Cliente"] = df_loaded["Cliente"].astype(str).str.strip()
            df_loaded = df_loaded[df_loaded["Cliente"].str.lower() == "braclean"]
            if df_loaded.empty:
                df_loaded["Cliente"] = "BraClean"
            
            df_loaded["Etapa"] = df_loaded["Etapa"].replace({
                "1. Contatado": "Prospecção",
                "2. Conversando": "Qualificação",
                "1. Prospecção": "Prospecção",
                "2. Qualificação": "Qualificação",
                "3. Reunião Agendada": "Reunião Agendada",
                "4. Proposta Enviada": "Proposta Enviada",
                "5. Fechado": "Fechado",
                "6. Perdido": "Pós: Perdido",
                "Pós: Lixeira": "Pós: Perdido"
            })
            
            df_loaded["Vendedor"] = df_loaded["Vendedor"].apply(lambda x: "Gabriel" if str(x).strip() in ["", "nan", "Não informado"] else x)
            return df_loaded
    except Exception as e:
        st.warning(f"Aviso ao ler do Google Sheets: {e}. Carregando dados padrão iniciais.")

    df_inicial = pd.DataFrame([
        {
            "id": 1, "Empresa": "Usina Santa Clara", "Cliente": "BraClean", "Perfil": "Cliente A", "Etapa": "Prospecção", 
            "Contato": "Roberto Alves", "Cargo": "Diretor Operacional", "Telefone": "(16) 99876-5432", 
            "Email": "roberto@usinasantaclara.com.br", "Cidade": "Sertãozinho / SP", "Valor": 120000.0, 
            "Prob": 0.20, "Vendedor": "Gabriel", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today() - timedelta(days=2)), "Followup_Nota": "Enviar apresentação institucional atualizada.", 
            "Historico": "[01/09/2026 10:00] Primeiro contato realizado."
        },
        {
            "id": 2, "Empresa": "Rede Postos Aliança", "Cliente": "BraClean", "Perfil": "Cliente B", "Etapa": "Qualificação", 
            "Contato": "Patricia Lima", "Cargo": "Gerente de Compras", "Telefone": "(16) 99765-4321", 
            "Email": "patricia@postosalianca.com.br", "Cidade": "Ribeirão Preto / SP", "Valor": 45000.0, 
            "Prob": 0.40, "Vendedor": "Ariel", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today()), "Followup_Nota": "Apresentar condições técnicas do catálogo.", 
            "Historico": "[02/09/2026 14:30] Lead qualificado para catálogo BraClean."
        }
    ])
    try:
        conn.update(worksheet="Página1", data=df_inicial)
    except:
        pass
    return df_inicial

def salvar_dados_crm(df):
    try:
        df["Cliente"] = "BraClean"
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
            return "atrasado", "Atrasado", '<span style="height: 10px; width: 10px; background-color: #FF0033; border-radius: 50%; display: inline-block;" title="Atrasado"></span>'
        elif dt_follow == hoje:
            return "hoje", "Atenção (Hoje)", '<span style="height: 10px; width: 10px; background-color: #FFEA00; border-radius: 50%; display: inline-block;" title="Hoje"></span>'
        else:
            return "em_dia", "Em Dia", '<span style="height: 10px; width: 10px; background-color: #00FF66; border-radius: 50%; display: inline-block;" title="Em Dia"></span>'
    except:
        return "sem_data", "Sem Follow-up", '<span style="height: 10px; width: 10px; background-color: #94A3B8; border-radius: 50%; display: inline-block;" title="Sem Data"></span>'

# ---------------------------------------------------------
# BARRA LATERAL (LOGO PEQUENA COVEM E CONFIGURAÇÕES)
# ---------------------------------------------------------
if ARQUIVO_LOGO.exists():
    st.sidebar.image(str(ARQUIVO_LOGO), use_container_width=True)

st.sidebar.markdown("### BraClean ")
st.sidebar.divider()

with st.sidebar.expander("Personalizar Cores das Etapas", expanded=False):
    st.caption("Altere as cores das etapas:")
    for etapa_nome in PROB_MAP.keys():
        cor_atual = st.session_state.funnel_colors.get(etapa_nome, "#00E5FF")
        nova_cor = st.color_picker(f"Cor: {etapa_nome.replace('Pré: ', '').replace('Pós: ', '')}", cor_atual, key=f"picker_{etapa_nome}")
        st.session_state.funnel_colors[etapa_nome] = nova_cor

st.sidebar.divider()

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='CRM_BRACLEAN')
buffer.seek(0)

st.sidebar.download_button(
    label="Baixar Planilha Excel",
    data=buffer,
    file_name="crm_braclean.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

# ---------------------------------------------------------
# 1. LOGO CENTRALIZADA DA COVEM (logoCOVEM.png)
# ---------------------------------------------------------
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if ARQUIVO_LOGO.exists():
        st.image(str(ARQUIVO_LOGO), use_container_width=True)
    else:
        st.warning("Arquivo 'logoCOVEM.png' não encontrado na pasta do projeto.")

st.divider()

# ---------------------------------------------------------
# MENU HORIZONTAL PRINCIPAL EM CARDS
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
                    background-color: #0A0E27 !important;
                    color: #00E5FF !important;
                    border: 1px solid #00E5FF !important;
                    font-weight: 600 !important;
                    box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
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
        <hr style='border: none; border-top: 1px solid #1E293B;'>
    </div>
""", unsafe_allow_html=True)

aba_selecionada = st.session_state.menu_ativo

# ---------------------------------------------------------
# FUNÇÃO DE RENDERIZAÇÃO DA AGENDA DA SEMANA
# ---------------------------------------------------------
def exibir_agenda_semana(df_tarefas, df_crm):
    st.markdown('<div style="margin-top: 4px;"></div>', unsafe_allow_html=True)
    
    c_sub1, c_sub2 = st.columns(2)
    
    with c_sub1:
        is_sub_active_1 = (st.session_state.sub_menu_tarefas == "Tarefas")
        if is_sub_active_1:
            st.markdown(
                """
                <style>
                div[data-testid="column"]:nth-of-type(1) div.stButton > button {
                    background-color: #0A0E27 !important;
                    color: #00E5FF !important;
                    border: 1px solid #00E5FF !important;
                    font-weight: 600 !important;
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
                    background-color: #0A0E27 !important;
                    color: #00E5FF !important;
                    border: 1px solid #00E5FF !important;
                    font-weight: 600 !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
        if st.button("Follow-up", key="sub_btn_followups", use_container_width=True):
            st.session_state.sub_menu_tarefas = "Follow-up"
            st.rerun()

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    def obter_telefone_por_empresa(nome_empresa):
        if not nome_empresa or nome_empresa == "Nenhum / Tarefa Geral":
            return "Não vinculado"
        match = df_crm[df_crm["Empresa"].str.lower() == str(nome_empresa).lower()]
        if not match.empty:
            tel = match.iloc[0].get("Telefone", "")
            return tel if tel else "Não informado"
        return "Não cadastrado no CRM"

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
                            emp_vinculada = row.get('Cliente', 'BraClean')
                            tel_contato = obter_telefone_por_empresa(emp_vinculada)
                            st.markdown(f"""
                                - **{row['Titulo']}**<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Empresa/Cliente: `{emp_vinculada}`<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Telefone: <span class="phone-highlight">{tel_contato}</span><br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Vencimento: {row['Data_Vencimento'].strftime('%d/%m/%Y')}
                                <hr style="margin: 4px 0; border-color: #334155;">
                            """, unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma tarefa atrasada.")

            with col_hoje:
                st.markdown(f'<div class="badge-hoje">{len(hoje_tarefas)} Tarefas para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Tarefas para Hoje"):
                    if not hoje_tarefas.empty:
                        for _, row in hoje_tarefas.iterrows():
                            emp_vinculada = row.get('Cliente', 'BraClean')
                            tel_contato = obter_telefone_por_empresa(emp_vinculada)
                            st.markdown(f"""
                                - **{row['Titulo']}**<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Empresa/Cliente: `{emp_vinculada}`<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Telefone: <span class="phone-highlight">{tel_contato}</span>
                                <hr style="margin: 4px 0; border-color: #334155;">
                            """, unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma tarefa para hoje.")

    else:
        if df_crm.empty:
            st.info("Nenhum cliente no CRM.")
        else:
            crm_temp = df.copy()
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
                            tel_crm = row.get('Telefone', 'Não informado')
                            st.markdown(f"""
                                - **{row['Empresa']}**<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Contato: `{row['Contato']}`<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Telefone: <span class="phone-highlight">{tel_crm}</span><br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Data: {dt_f_br}
                                <hr style="margin: 4px 0; border-color: #334155;">
                            """, unsafe_allow_html=True)
                    else:
                        st.write("Nenhum follow-up atrasado.")

            with col_c_hoje:
                st.markdown(f'<div class="badge-hoje">{len(c_hoje)} Follow-ups para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Follow-ups para Hoje"):
                    if not c_hoje.empty:
                        for _, row in c_hoje.iterrows():
                            tel_crm = row.get('Telefone', 'Não informado')
                            st.markdown(f"""
                                - **{row['Empresa']}**<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Contato: `{row['Contato']}`<br>
                                &nbsp;&nbsp;&nbsp;&nbsp;Telefone: <span class="phone-highlight">{tel_crm}</span>
                                <hr style="margin: 4px 0; border-color: #334155;">
                            """, unsafe_allow_html=True)
                    else:
                        st.write("Nenhum follow-up para hoje.")

    st.divider()

# =========================================================
# ABA 1: GERENCIADOR DE TAREFAS & CALENDÁRIO FUTURO
# =========================================================
if aba_selecionada == "Gerenciamento de Tarefas":
    st.subheader("Gerenciamento de Tarefas — BraClean")
    exibir_agenda_semana(st.session_state.df_tarefas, st.session_state.df_crm)

    lista_clientes = ["Nenhum / Tarefa Geral"] + df["Empresa"].dropna().tolist()

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
                    "Cliente": "BraClean",
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
                            "Vinculado a": f"Cliente: BraClean",
                            "Prioridade / Status": f"Prioridade: {t.get('Prioridade', 'Normal')}"
                        })
                except:
                    pass

    if not df.empty:
        for idx_c, c in df.iterrows():
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
        st.subheader("Gestão de Funis — BraClean")
    with col_topo_busca:
        termo_busca = st.text_input(
            "Pesquisar cliente", 
            placeholder="🔍 Buscar por empresa, contato...", 
            label_visibility="collapsed"
        )

    funis_list = ["Pré Funil", "Funil de Vendas", "Pós Funil"]
    cols_funis = st.columns(3)
    
    for idx_f, nome_f in enumerate(funis_list):
        with cols_funis[idx_f]:
            is_funil_active = (st.session_state.funnel_selecionado == nome_f)
            if is_funil_active:
                st.markdown(
                    f"""
                    <style>
                    div[data-testid="column"]:nth-of-type({idx_f+1}) div.stButton > button {{
                        background-color: #00E5FF !important;
                        color: #0A0E27 !important;
                        border: 1px solid #00E5FF !important;
                        font-weight: 700 !important;
                        box-shadow: 0 0 10px rgba(0, 229, 255, 0.4);
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )
            if st.button(nome_f, key=f"btn_funil_{idx_f}", use_container_width=True):
                st.session_state.funnel_selecionado = nome_f
                st.rerun()

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    if st.session_state.cliente_editando_id is not None:
        cliente_edit_id = st.session_state.cliente_editando_id
        filtro_reg = df[df["id"] == cliente_edit_id]
        
        if not filtro_reg.empty:
            row_edit = filtro_reg.iloc[0]
            
            st.markdown(
                f"""
                <div style="background-color: rgba(10, 14, 39, 0.95); border: 2px solid #00E5FF; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 0 15px rgba(0, 229, 255, 0.2);">
                    <h3 style="color: #00E5FF; margin-top: 0; margin-bottom: 20px; font-weight: 700;">Ficha Completa & Linha do Tempo: {row_edit['Empresa']}</h3>
                """,
                unsafe_allow_html=True
            )
            
            with st.form(key=f"form_full_edit_horizontal_{cliente_edit_id}"):
                etapas_todas = list(PROB_MAP.keys())
                
                edit_etapa = st.selectbox(
                    "Etapa do Funil (Pré, Principal ou Pós)", 
                    options=etapas_todas, 
                    index=etapas_todas.index(row_edit["Etapa"]) if row_edit["Etapa"] in etapas_todas else 0,
                    format_func=lambda x: x.replace("Pré: ", "").replace("Pós: ", "")
                )
                
                st.divider()

                hc1, hc2, hc3 = st.columns(3)
                with hc1:
                    edit_empresa = st.text_input("Empresa", value=row_edit["Empresa"])
                    edit_perfil = st.selectbox("Classificação do Lead", options=OPCOES_PERFIL, index=OPCOES_PERFIL.index(row_edit.get("Perfil", "Cliente C")) if row_edit.get("Perfil", "Cliente C") in OPCOES_PERFIL else 2)
                    edit_contato = st.text_input("Contato", value=row_edit["Contato"])
                with hc2:
                    edit_cargo = st.text_input("Cargo", value=row_edit["Cargo"])
                    edit_tel = st.text_input("Telefone", value=row_edit["Telefone"])
                    edit_email = st.text_input("E-mail", value=row_edit["Email"])
                with hc3:
                    edit_cidade = st.text_input("Cidade", value=row_edit["Cidade"])
                    edit_valor = st.number_input("Valor Estimado Mensal (R$)", value=float(row_edit["Valor"]), step=1000.0)
                    edit_vendedor = st.text_input("Vendedor", value=row_edit["Vendedor"])
                    
                    try:
                        dt_parse = dt.strptime(str(row_edit["Followup_Data"]).strip()[:10], "%Y-%m-%d").date() if row_edit["Followup_Data"] and str(row_edit["Followup_Data"]).strip() not in ["nan", "NaT", ""] else date.today()
                    except:
                        dt_parse = date.today()
                        
                    edit_fu_data = st.date_input("Próxima Data de Follow-up", value=dt_parse)
                
                edit_fu_nota = st.text_input("Resumo / Nota do Follow-up", value=row_edit["Followup_Nota"])
                
                edit_perda = str(row_edit.get("Perda", "")).strip()
                edit_motivo_perda = st.selectbox(
                    "Motivo de Perda / Sem Interesse (Se aplicável)", 
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
                        st.session_state.df_crm.loc[idx_real, "Cliente"] = "BraClean"
                        st.session_state.df_crm.loc[idx_real, "Perfil"] = edit_perfil
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
                    st.session_state.cliente_editando_id = None
                    st.rerun()
                    
                if btn_excluir:
                    st.session_state.df_crm = st.session_state.df_crm[st.session_state.df_crm["id"] != cliente_edit_id]
                    salvar_dados_crm(st.session_state.df_crm)
                    st.session_state.cliente_editando_id = None
                    st.warning("Cliente excluído com sucesso!")
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            st.divider()

    df_funil_exibicao = df.copy()
    if termo_busca:
        termo_limpo = termo_busca.lower()
        df_funil_exibicao = df_funil_exibicao[
            df_funil_exibicao["Empresa"].astype(str).str.lower().str.contains(termo_limpo) |
            df_funil_exibicao["Contato"].astype(str).str.lower().str.contains(termo_limpo) |
            df_funil_exibicao["Telefone"].astype(str).str.lower().str.contains(termo_limpo)
        ]

    funil_atual = st.session_state.funnel_selecionado
    etapas_visiveis = ESTRUTURA_FUNIS.get(funil_atual, ESTRUTURA_FUNIS["Funil de Vendas"])
    todas_etapas_existentes = list(PROB_MAP.keys())

    cols = st.columns(len(etapas_visiveis))
    
    for idx, etapa in enumerate(etapas_visiveis):
        cor_header = st.session_state.funnel_colors.get(etapa, "#00E5FF")
        nome_curto_etapa = etapa.replace("Pré: ", "").replace("Pós: ", "")
        
        with cols[idx]:
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(10, 14, 39, 0.95) 0%, rgba(5, 11, 24, 0.95) 100%); border: 1px solid #1E293B; border-top: 5px solid {cor_header}; padding: 14px 10px; border-radius: 6px; text-align: center; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);">
                    <b style="color: #FFFFFF; font-size: 13px; text-transform: uppercase; letter-spacing: 0.8px;">{nome_curto_etapa}</b>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            sub_df = df_funil_exibicao[df_funil_exibicao["Etapa"] == etapa]
            
            for _, row in sub_df.iterrows():
                st_code, st_label, st_icon = calcular_status_followup(row.get("Followup_Data", ""))
                cliente_id = int(row['id'])
                
                st.markdown(f"""
                    <div style="border-left: 5px solid {cor_header}; background-color: rgba(10, 14, 39, 0.85); border-top: 1px solid #1E293B; border-right: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-radius: 4px; margin-bottom: 6px; padding: 2px;">
                """, unsafe_allow_html=True)
                
                with st.expander(f"{row['Empresa']}"):
                    dt_f_exib = row.get('Followup_Data', '')
                    
                    try:
                        raw_val = str(dt_f_exib).strip()[:10]
                        dt_f_str = dt.strptime(raw_val, "%Y-%m-%d").strftime("%d/%m/%Y") if raw_val and raw_val not in ["nan", "NaT", ""] else "Não agendado"
                    except:
                        dt_f_str = "Não agendado"
                    
                    st.markdown(
                        f"""
                        <div style="line-height: 1.4; margin-bottom: 8px;">
                            <span style="font-size: 13px;"><b>{row['Empresa']}</b></span><br>
                            <span style="font-size: 11px; color: #00E5FF;">Carteira: BraClean</span><br>
                            <span style="font-size: 12px; color: #94A3B8;">Contato: {row['Contato']}</span><br>
                            <span class="phone-highlight" style="font-size: 12px;">{row.get('Telefone', 'Não informado')}</span><br>
                            <hr style="margin: 6px 0; border-color: #334155;">
                            <span style="font-size: 12px; color: #E2E8F0;"><b>Follow-up:</b> {st_icon} {dt_f_str}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    nova_etapa_card = st.selectbox(
                        "Mover Lead:", 
                        options=todas_etapas_existentes, 
                        index=todas_etapas_existentes.index(row["Etapa"]) if row["Etapa"] in todas_etapas_existentes else 0, 
                        key=f"mov_etapa_{cliente_id}",
                        format_func=lambda x: x.replace("Pré: ", "").replace("Pós: ", ""),
                        label_visibility="collapsed"
                    )
                    
                    if nova_etapa_card != row["Etapa"]:
                        idx_df = st.session_state.df_crm[st.session_state.df_crm["id"] == cliente_id].index
                        st.session_state.df_crm.loc[idx_df, "Etapa"] = nova_etapa_card
                        st.session_state.df_crm.loc[idx_df, "Prob"] = PROB_MAP[nova_etapa_card]
                        if "Perdido" in nova_etapa_card:
                            st.session_state.df_crm["Perda"] = st.session_state.df_crm["Perda"].astype(str)
                            st.session_state.df_crm.loc[idx_df, "Perda"] = "Outros"
                        
                        salvar_dados_crm(st.session_state.df_crm)
                        st.success("Lead movimentado com sucesso!")
                        st.rerun()

                    st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
                    if st.button("EDITAR", key=f"btn_edit_{cliente_id}", use_container_width=True):
                        st.session_state.cliente_editando_id = cliente_id
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ABA 3: DASHBOARD
# =========================================================
elif aba_selecionada == "Dashboard":
    st.markdown('<div class="notranslate"><h3>Dashboard - BraClean</h3></div>', unsafe_allow_html=True)
    
    col_f1, _ = st.columns([2, 2])
    with col_f1:
        periodo_sel = st.selectbox(
            "Visualizar Período:", 
            ["Todos os Registros", "Esta Semana", "15 Dias", "1 Mês", "2 Meses", "3 Meses"],
            label_visibility="collapsed"
        )
    
    df_dash = df.copy()
    if "Data_Cadastro" in df_dash.columns:
        df_dash["Data_Cadastro"] = pd.to_datetime(df_dash["Data_Cadastro"], errors='coerce')
        hoje = pd.Timestamp.now()
        
        if periodo_sel == "Esta Semana":
            inicio = hoje - pd.Timedelta(days=hoje.weekday())
            df_dash = df_dash[df_dash["Data_Cadastro"] >= inicio]
        elif periodo_sel == "15 Dias":
            df_dash = df_dash[df_dash["Data_Cadastro"] >= hoje - pd.Timedelta(days=15)]
        elif periodo_sel == "1 Mês":
            df_dash = df_dash[df_dash["Data_Cadastro"] >= hoje - pd.Timedelta(days=30)]
        elif periodo_sel == "2 Meses":
            df_dash = df_dash[df_dash["Data_Cadastro"] >= hoje - pd.Timedelta(days=60)]
        elif periodo_sel == "3 Meses":
            df_dash = df_dash[df_dash["Data_Cadastro"] >= hoje - pd.Timedelta(days=90)]

    st.divider()

    etapas_crm = list(PROB_MAP.keys())
    contagem_calculada = {}
    
    for etapa in etapas_crm:
        count_real = len(df_dash[df_dash["Etapa"] == etapa])
        contagem_calculada[etapa] = count_real
        
    total_leads = sum(contagem_calculada.values())
    cols_m = st.columns(len(etapas_crm) + 1)
    
    for i, etapa in enumerate(etapas_crm):
        cor_header = st.session_state.funnel_colors.get(etapa, "#00E5FF")
        qtd = contagem_calculada[etapa]
        nome_limpo = etapa.replace("Pré: ", "").replace("Pós: ", "")
        
        with cols_m[i]:
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(10, 14, 39, 0.95) 0%, rgba(5, 11, 24, 0.95) 100%); border: 1px solid #1E293B; border-top: 4px solid {cor_header}; padding: 12px 6px; border-radius: 8px; text-align: center; margin-bottom: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);">
                    <b style="color: #F8FAFC; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">{nome_limpo}</b>
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.metric(label="", value=qtd)

    with cols_m[-1]:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(10, 14, 39, 0.95) 0%, rgba(5, 11, 24, 0.95) 100%); border: 1px solid #1E293B; border-top: 4px solid #00E5FF; padding: 12px 6px; border-radius: 8px; text-align: center; margin-bottom: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);">
                <b style="color: #00E5FF; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">TOTAL LEADS</b>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.metric(label="", value=total_leads)

    st.divider()

    st.markdown('<div class="notranslate"><h3>Dashboard Gráfico - BraClean</h3></div>', unsafe_allow_html=True)
    df_pizza = pd.DataFrame(list(contagem_calculada.items()), columns=["Etapa", "Quantidade"])
    df_pizza_valida = df_pizza[df_pizza["Quantidade"] > 0]

    if not df_pizza_valida.empty:
        fig_pizza = px.pie(
            df_pizza_valida, 
            values="Quantidade", 
            names="Etapa",
            color="Etapa",
            color_discrete_map=st.session_state.funnel_colors,
            hole=0.4
        )
        fig_pizza.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=13),
            height=440,
            margin=dict(t=40, b=40, l=20, r=20),
            legend=dict(font=dict(color="#FFFFFF"))
        )
        fig_pizza.update_traces(
            textinfo="percent+value",
            marker=dict(line=dict(color='#0A0E27', width=2))
        )
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para o período selecionado.")

    st.divider()

    st.markdown('<div class="notranslate"><h3>Gráfico de Motivo de Perda — BraClean</h3></div>', unsafe_allow_html=True)
    df_perdidos = df_dash[df_dash["Etapa"] == "Pós: Perdido"].copy()
    
    if not df_perdidos.empty and "Perda" in df_perdidos.columns:
        df_perdidos["Perda"] = df_perdidos["Perda"].fillna("").astype(str).str.strip()
        df_motivos = df_perdidos[df_perdidos["Perda"] != ""].groupby("Perda").size().reset_index(name="Quantidade")
        
        if not df_motivos.empty:
            fig_perda = px.bar(
                df_motivos,
                x="Perda",
                y="Quantidade",
                color="Perda",
                color_discrete_map=CORES_PERDAS,
                text="Quantidade"
            )
            fig_perda.update_layout(
                paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
                plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
                font=dict(color="#FFFFFF", family="Inter", size=13),
                height=380,
                xaxis=dict(
                    title="Motivo de Perda",
                    showgrid=True,
                    gridcolor=GRID_GRAFICO_FUTURISTA,
                    zerolinecolor=GRID_GRAFICO_FUTURISTA
                ),
                yaxis=dict(
                    title="Quantidade",
                    showgrid=True,
                    gridcolor=GRID_GRAFICO_FUTURISTA,
                    zerolinecolor=GRID_GRAFICO_FUTURISTA
                ),
                showlegend=False
            )
            fig_perda.update_traces(textposition="outside", marker=dict(line=dict(color='#00E5FF', width=1)))
            st.plotly_chart(fig_perda, use_container_width=True)
        else:
            st.info("Nenhum motivo de perda especificado para os leads perdidos.")
    else:
        st.info("Nenhum lead registrado em 'Pós: Perdido' no momento.")

# =========================================================
# ABA 4: RELATÓRIO EXECUTIVO
# =========================================================
elif aba_selecionada == "Relatório Executivo":
    st.title("Relatório Executivo — BraClean")

    df_exec = df.copy()

    if "Perfil" not in df_exec.columns:
        df_exec["Perfil"] = "Cliente C"
    df_exec["Perfil"] = df_exec["Perfil"].fillna("Cliente C")

    # ---------------------------------------------------------
    # GRÁFICO 1: PRÉ-FUNIL
    # ---------------------------------------------------------
    st.markdown("### Pré-Funil")

    etapas_bloco_1 = ["Pré: Novo Lead", "Pré: Conexão", "Pós: Standby"]
    dados_bloco_1 = []
    for etapa in etapas_bloco_1:
        qtd = len(df_exec[df_exec["Etapa"] == etapa])
        nome_rotulo = etapa.replace("Pré: ", "").replace("Pós: ", "")
        dados_bloco_1.append({"Etapa": nome_rotulo, "Quantidade": qtd, "Etapa_Orig": etapa})

    df_b1 = pd.DataFrame(dados_bloco_1)
    if not df_b1.empty and df_b1["Quantidade"].sum() > 0:
        fig_b1 = px.funnel(
            df_b1,
            x="Quantidade",
            y="Etapa",
            color="Etapa_Orig",
            color_discrete_map=st.session_state.funnel_colors
        )
        fig_b1.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=13),
            height=260,
            showlegend=False
        )
        st.plotly_chart(fig_b1, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado no bloco de Pré-Funil e Standby.")

    # ---------------------------------------------------------
    # ESTATÍSTICA 1: TAXA DE CONVERSÃO PRÉ-FUNIL -> PROSPECÇÃO
    # ---------------------------------------------------------
    total_novo_lead = len(df_exec[df_exec["Etapa"] == "Pré: Novo Lead"])
    total_prospeccao = len(df_exec[df_exec["Etapa"] == "Prospecção"])
    
    taxa_conversao_pre_pros = (total_prospeccao / total_novo_lead * 100) if total_novo_lead > 0 else 0.0
    
    st.markdown("""
        <div style="background-color: rgba(10, 14, 39, 0.7); border: 1px solid #1E293B; border-left: 4px solid #00E5FF; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
            <b style="color: #00E5FF; font-size: 14px;">Análise Estatística & Probabilidade (Pré-Funil)</b>
    """, unsafe_allow_html=True)
    
    ec1, ec2 = st.columns(2)
    ec1.metric("Leads necessários no Pré-Funil para gerar 1 Prospecção", f"{max(1, int(1 / PROB_MAP['Pré: Novo Lead'] * PROB_MAP['Prospecção']))} leads")
    ec2.metric("Taxa de Conversão Atual (Pré ➔ Prospecção)", f"{taxa_conversao_pre_pros:.1f}%")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------------------
    # GRÁFICO 2: FUNIL DE VENDAS PRINCIPAL 
    # ---------------------------------------------------------
    st.markdown("### Funil de Vendas")

    etapas_bloco_2 = ["Prospecção", "Qualificação", "Reunião Agendada", "Proposta Enviada", "Fechado", "Pós: Perdido"]
    dados_bloco_2 = []
    for etapa in etapas_bloco_2:
        qtd = len(df_exec[df_exec["Etapa"] == etapa])
        nome_rotulo = etapa.replace("Pós: ", "")
        dados_bloco_2.append({"Etapa": nome_rotulo, "Quantidade": qtd, "Etapa_Orig": etapa})

    df_b2 = pd.DataFrame(dados_bloco_2)
    if not df_b2.empty and df_b2["Quantidade"].sum() > 0:
        fig_b2 = px.funnel(
            df_b2,
            x="Quantidade",
            y="Etapa",
            color="Etapa_Orig",
            color_discrete_map=st.session_state.funnel_colors
        )
        fig_b2.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=13),
            height=380,
            showlegend=False
        )
        st.plotly_chart(fig_b2, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado no bloco de Funil de Vendas e Perdidos.")

    # ---------------------------------------------------------
    # ESTATÍSTICA 2: TAXA DE CONVERSÃO PROSPECÇÃO -> VENDA (FECHADO)
    # ---------------------------------------------------------
    total_fechado = len(df_exec[df_exec["Etapa"] == "Fechado"])
    taxa_conversao_pros_venda = (total_fechado / total_prospeccao * 100) if total_prospeccao > 0 else 0.0
    
    st.markdown("""
        <div style="background-color: rgba(10, 14, 39, 0.7); border: 1px solid #1E293B; border-left: 4px solid #00FF66; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
            <b style="color: #00FF66; font-size: 14px;">Análise Estatística & Probabilidade (Funil de Vendas)</b>
    """, unsafe_allow_html=True)
    
    ed1, ed2 = st.columns(2)
    ed1.metric("Prospecções necessárias para gerar 1 Venda (Fechado)", f"{max(1, int(1 / PROB_MAP['Prospecção']))} prospecções")
    ed2.metric("Taxa de Conversão Atual (Prospecção ➔ Fechado)", f"{taxa_conversao_pros_venda:.1f}%")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------------------
    # GRÁFICO DE GARGALOS ORDENADO PELA SEQUÊNCIA DO FUNIL
    # ---------------------------------------------------------
    ordem_gargalos = [
        "Pré: Novo Lead", 
        "Pré: Conexão", 
        "Prospecção", 
        "Qualificação", 
        "Reunião Agendada", 
        "Proposta Enviada", 
        "Fechado", 
        "Pós: Standby", 
        "Pós: Perdido"
    ]
    
    df_gargalos = df_exec.groupby("Etapa").size().reset_index(name="Quantidade")
    
    fig_gargalo = px.bar(
        df_gargalos,
        x="Etapa",
        y="Quantidade",
        title="Levantamento de Gargalos (Onde o Lead está parando)",
        color="Etapa",
        color_discrete_map=st.session_state.funnel_colors,
        text_auto=True,
        category_orders={"Etapa": ordem_gargalos}
    )
    fig_gargalo.update_layout(
        paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        font=dict(color="#FFFFFF", family="Inter", size=13),
        height=380,
        showlegend=False,
        xaxis=dict(
            gridcolor=GRID_GRAFICO_FUTURISTA,
            categoryorder="array",
            categoryarray=ordem_gargalos
        ),
        yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA)
    )
    st.plotly_chart(fig_gargalo, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # GRÁFICO DE BARRAS VERTICAIS: CLASSIFICAÇÃO DE CLIENTES (A, B, C)
    # ---------------------------------------------------------
    st.markdown("### Classificação de Clientes (Ticket Médio)")

    contagem_perfis_dict = {"Cliente A": 0, "Cliente B": 0, "Cliente C": 0}
    df_temp_perf = df_exec["Perfil"].value_counts().to_dict()
    for k in contagem_perfis_dict.keys():
        contagem_perfis_dict[k] = int(df_temp_perf.get(k, 0))

    df_barras_perfil = pd.DataFrame(list(contagem_perfis_dict.items()), columns=["Classificação", "Quantidade"])

    fig_barras_perfil = px.bar(
        df_barras_perfil,
        x="Classificação",
        y="Quantidade",
        color="Classificação",
        color_discrete_map=CORES_PERFIL_BARRAS,
        text="Quantidade"
    )
    fig_barras_perfil.update_layout(
        paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
        font=dict(color="#FFFFFF", family="Inter", size=13),
        height=360,
        xaxis=dict(
            title="Classificação do Perfil",
            showgrid=True,
            gridcolor=GRID_GRAFICO_FUTURISTA,
            zerolinecolor=GRID_GRAFICO_FUTURISTA
        ),
        yaxis=dict(
            title="Número de Clientes",
            showgrid=True,
            gridcolor=GRID_GRAFICO_FUTURISTA,
            zerolinecolor=GRID_GRAFICO_FUTURISTA
        ),
        showlegend=False
    )
    fig_barras_perfil.update_traces(textposition="outside", marker=dict(line=dict(color='#00E5FF', width=1)))
    st.plotly_chart(fig_barras_perfil, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # ATIVIDADES INDIVIDUAIS (GABRIEL VS ARIEL) E METAS
    # ---------------------------------------------------------
    st.markdown("### Atividades Individuais & Metas de Vendedores")

    vendedores_covem = ["Gabriel", "Ariel"]
    df_exec["Vendedor"] = df_exec["Vendedor"].fillna("Gabriel")
    
    vendedores_dados = []
    for v in vendedores_covem:
        sub_v = df_exec[df_exec["Vendedor"].str.contains(v, case=False, na=False)]
        qtd_leads = len(sub_v)
        vendedores_dados.append({"Vendedor": v, "Leads Movimentados": qtd_leads})
        
    df_vend = pd.DataFrame(vendedores_dados)
    
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("Meta Diária", "50 Leads/Dia")
    c_m2.metric("Meta Semanal", "250 Leads/Sem")
    c_m3.metric("Meta Mensal", "1.000 Leads/Mês")

    col_g1, col_g2, col_g3 = st.columns(3)

    cores_vendedores_map = {
        "Gabriel": "#FF0033",  # Vermelho Neon
        "Ariel": "#00E5FF"     # Azul Neon
    }

    with col_g1:
        df_vend["Meta Diária"] = 50
        fig_meta_diaria = go.Figure(data=[
            go.Bar(name='Leads Movimentados', x=df_vend['Vendedor'], y=df_vend['Leads Movimentados'], 
                   marker_color=[cores_vendedores_map.get(v, "#00E5FF") for v in df_vend['Vendedor']], text=df_vend['Leads Movimentados'], textposition='auto'),
            go.Bar(name='Meta Diária', x=df_vend['Vendedor'], y=df_vend['Meta Diária'], 
                   marker_color='#FFEA00', text=df_vend['Meta Diária'], textposition='auto')
        ])
        fig_meta_diaria.update_layout(
            barmode='group',
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=11),
            height=320,
            margin=dict(t=40, b=20, l=20, r=20),
            xaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
            yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
            showlegend=False
        )
        st.plotly_chart(fig_meta_diaria, use_container_width=True)

    with col_g2:
        df_vend["Meta Semanal"] = 250
        fig_meta_semanal = go.Figure(data=[
            go.Bar(name='Leads Movimentados', x=df_vend['Vendedor'], y=df_vend['Leads Movimentados'], 
                   marker_color=[cores_vendedores_map.get(v, "#00E5FF") for v in df_vend['Vendedor']], text=df_vend['Leads Movimentados'], textposition='auto'),
            go.Bar(name='Meta Semanal', x=df_vend['Vendedor'], y=df_vend['Meta Semanal'], 
                   marker_color='#FFEA00', text=df_vend['Meta Semanal'], textposition='auto')
        ])
        fig_meta_semanal.update_layout(
            barmode='group',
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=11),
            height=320,
            margin=dict(t=40, b=20, l=20, r=20),
            xaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
            yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
            showlegend=False
        )
        st.plotly_chart(fig_meta_semanal, use_container_width=True)

    with col_g3:
        df_vend["Meta Mensal"] = 1000
        fig_meta_mensal = go.Figure(data=[
            go.Bar(name='Leads Movimentados', x=df_vend['Vendedor'], y=df_vend['Leads Movimentados'], 
                   marker_color=[cores_vendedores_map.get(v, "#00E5FF") for v in df_vend['Vendedor']], text=df_vend['Leads Movimentados'], textposition='auto'),
            go.Bar(name='Meta Mensal', x=df_vend['Vendedor'], y=df_vend['Meta Mensal'], 
                   marker_color='#FFEA00', text=df_vend['Meta Mensal'], textposition='auto')
        ])
        fig_meta_mensal.update_layout(
            barmode='group',
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=11),
            height=320,
            margin=dict(t=40, b=20, l=20, r=20), 
            xaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
            yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA),
            showlegend=False
        )
        st.plotly_chart(fig_meta_mensal, use_container_width=True)

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # GRÁFICO MACRO DE LINHAS PROGRESSIVO (DIÁRIO, SEMANAL, MENSAL)
    # ---------------------------------------------------------
    st.markdown("### Visão Macro: Comportamento de Atividades dos Vendedores")
    st.markdown("Acompanhamento progressivo e automático da movimentação dos vendedores ao longo do tempo (acumulado diariamente rumo a dezembro).")

    tipo_visao_macro = st.selectbox(
        "Selecione a Escala Temporal:",
        options=["Evolução Diária", "Evolução Semanal", "Evolução Mensal"],
        key="select_visao_macro"
    )

    df_macro_dinamico = df_exec.copy()
    if "Data_Cadastro" in df_macro_dinamico.columns:
        df_macro_dinamico["Data_Cadastro"] = pd.to_datetime(df_macro_dinamico["Data_Cadastro"], errors='coerce')
        df_macro_dinamico = df_macro_dinamico.dropna(subset=["Data_Cadastro"])
        
        if tipo_visao_macro == "Evolução Diária":
            df_macro_dinamico["Periodo"] = df_macro_dinamico["Data_Cadastro"].dt.strftime("%d/%m/%Y (%a)")
            df_agrupado = df_macro_dinamico.groupby(["Periodo", "Vendedor", df_macro_dinamico["Data_Cadastro"].dt.date]).size().reset_index(name="Volume de Atividades")
            df_agrupado = df_agrupado.sort_values(by="Data_Cadastro")
        elif tipo_visao_macro == "Evolução Semanal":
            df_macro_dinamico["Periodo"] = "Semana " + df_macro_dinamico["Data_Cadastro"].dt.isocalendar().week.astype(str) + " (" + df_macro_dinamico["Data_Cadastro"].dt.year.astype(str) + ")"
            df_agrupado = df_macro_dinamico.groupby(["Periodo", "Vendedor"]).size().reset_index(name="Volume de Atividades")
        else:
            df_agrupado_mes = df_macro_dinamico.groupby([df_macro_dinamico["Data_Cadastro"].dt.to_period("M"), "Vendedor"]).size().reset_index(name="Volume de Atividades")
            df_agrupado_mes["Periodo"] = df_agrupado_mes["Data_Cadastro"].dt.strftime("%B / %Y")
            df_agrupado = df_agrupado_mes.sort_values(by="Data_Cadastro")
    else:
        df_agrupado = pd.DataFrame(columns=["Periodo", "Vendedor", "Volume de Atividades"])

    if not df_agrupado.empty:
        fig_macro_progressivo = px.line(
            df_agrupado,
            x="Periodo",
            y="Volume de Atividades",
            color="Vendedor",
            markers=True,
            title=f"Comportamento Operacional — {tipo_visao_macro}",
            color_discrete_map=cores_vendedores_map
        )
        fig_macro_progressivo.update_layout(
            paper_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            plot_bgcolor=FUNDO_GRAFICO_FUTURISTA,
            font=dict(color="#FFFFFF", family="Inter", size=13),
            height=400,
            xaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA, title="Período"),
            yaxis=dict(gridcolor=GRID_GRAFICO_FUTURISTA, title="Atividades Registradas"),
            legend=dict(font=dict(color="#FFFFFF"))
        )
        st.plotly_chart(fig_macro_progressivo, use_container_width=True)
    else:
        st.info("Ainda não há registros suficientes com data para traçar a evolução macro.")

    st.divider()

    # ---------------------------------------------------------
    # META BRACLEAN (TICKET MÉDIO E R$ 100K MENSAL ATÉ DEZEMBRO)
    # ---------------------------------------------------------
    st.markdown("### Meta BraClean (Ticket Médio e R$ 100k Mensais até Dezembro)")
    
    faturamento_braclean = float(df_exec[df_exec["Etapa"] == "Fechado"]["Valor"].sum())
    qtd_clientes_braclean = len(df_exec[df_exec["Etapa"] == "Fechado"])
    
    ticket_medio = (faturamento_braclean / qtd_clientes_braclean) if qtd_clientes_braclean > 0 else (df_exec["Valor"].mean() if not df_exec.empty else 0.0)
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

# =========================================================
# ABA 5: + NOVO CADASTRO
# =========================================================
elif aba_selecionada == "+ Novo Cadastro":
    st.subheader("+ Novo Cadastro Rápido (BraClean)")

    with st.form("form_cadastro_rapido", clear_on_submit=True):
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            rapido_empresa = st.text_input("Nome da Empresa *")
            rapido_telefone = st.text_input("Telefone *")
            rapido_perfil = st.selectbox("Classificação do Lead *", OPCOES_PERFIL, index=2)

        with col_r2:
            rapido_etapa = st.selectbox(
                "Etapa / Funil Inicial *", 
                list(PROB_MAP.keys()), 
                key="rapido_etapa",
                format_func=lambda x: x.replace("Pré: ", "").replace("Pós: ", "")
            )

        btn_salvar_rapido = st.form_submit_button("Cadastrar Rapidamente", use_container_width=True)

        if btn_salvar_rapido:
            if not rapido_empresa or not rapido_telefone:
                st.error("Por favor, preencha o Nome da Empresa e o Telefone.")
            else:
                novo_id = int(df["id"].max() + 1) if not df.empty and pd.notna(df["id"].max()) else 1
                val_sugestao = TICKET_MEDIO_PERFIL.get(rapido_perfil, 8500.0)

                nova_linha_rapida = {
                    "id": novo_id,
                    "Empresa": rapido_empresa,
                    "Cliente": "BraClean",
                    "Perfil": rapido_perfil,
                    "Etapa": rapido_etapa,
                    "Contato": "Não informado",
                    "Cargo": "Não informado",
                    "Telefone": rapido_telefone,
                    "Email": "Não informado",
                    "Cidade": "Não informado",
                    "Valor": val_sugestao,
                    "Prob": PROB_MAP[rapido_etapa],
                    "Vendedor": "Gabriel",
                    "Perda": "",
                    "Data_Cadastro": str(date.today()),
                    "Followup_Data": str(date.today()),
                    "Followup_Nota": "Novo cadastro rápido efetuado.",
                    "Historico": f"[{dt.now().strftime('%d/%m/%Y %H:%M')}] Cadastro rápido realizado."
                }
                st.session_state.df_crm = pd.concat(
                    [st.session_state.df_crm, pd.DataFrame([nova_linha_rapida])], 
                    ignore_index=True
                )
                salvar_dados_crm(st.session_state.df_crm)
                st.success(f"Empresa '{rapido_empresa}' cadastrada e salva com sucesso na nuvem!")
                st.rerun()

    st.write("---")
    st.subheader("Cadastrar Oportunidade Completa (BraClean)")
    
    with st.form("form_oportunidade", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            nova_empresa = st.text_input("Nome da Empresa / Cliente *")
            novo_perfil = st.selectbox("Classificação do Lead *", OPCOES_PERFIL, index=2, key="completo_perfil")
            novo_contato = st.text_input("Contato / Nome")
            novo_cargo = st.text_input("Cargo")
            novo_telefone = st.text_input("Telefone de Contato *")
            novo_email = st.text_input("E-mail Comercial")
            
        with col_f2:
            nova_cidade = st.text_input("Cidade / Estado")
            novo_vendedor = st.selectbox("Vendedor / Responsável", options=["Gabriel", "Ariel"])
            nova_valor = st.number_input("Valor Estimado Mensal (R$)", min_value=0.0, step=1000.0, format="%.2f")
            nova_etapa = st.selectbox(
                "Etapa Inicial *", 
                list(PROB_MAP.keys()),
                format_func=lambda x: x.replace("Pré: ", "").replace("Pós: ", "")
            )
            motivo_perda = st.selectbox("Motivo de Perda / Sem Interesse (Se aplicável)", [""] + MOTIVOS_PERDA_PADRAO)
            
        st.divider()
        st.markdown("**Dados Iniciais de Follow-up:**")
        f_data_ini = st.date_input("Data do Primeiro Follow-up", value=date.today())
        f_nota_ini = st.text_input("Lembrete / Ação de Follow-up")

        btn_salvar = st.form_submit_button("Salvar Oportunidade Completa")
        
        if btn_salvar:
            if not nova_empresa:
                st.error("Preencha o Nome da Empresa.")
            else:
                novo_id = int(df["id"].max() + 1) if not df.empty and pd.notna(df["id"].max()) else 1
                
                email_valido = nova_email if 'nova_email' in locals() and nova_email else "Não informado"
                contato_valido = novo_contato if 'novo_contato' in locals() and novo_contato else "Não informado"
                cargo_valido = novo_cargo if 'nova_cargo' in locals() and novo_cargo else "Não informado"
                telefone_valido = novo_telefone if 'novo_telefone' in locals() and novo_telefone else "Não informado"
                cidade_valida = nova_cidade if 'nova_cidade' in locals() and nova_cidade else "Não informado"

                nova_linha = {
                    "id": novo_id,
                    "Empresa": nova_empresa,
                    "Cliente": "BraClean",
                    "Perfil": novo_perfil,
                    "Etapa": nova_etapa,
                    "Contato": contato_valido,
                    "Cargo": cargo_valido,
                    "Telefone": telefone_valido,
                    "Email": email_valido,
                    "Cidade": cidade_valida,
                    "Valor": nova_valor,
                    "Prob": PROB_MAP[nova_etapa],
                    "Vendedor": novo_vendedor,
                    "Perda": str(motivo_perda) if "Perdido" in nova_etapa else "",
                    "Data_Cadastro": str(date.today()),
                    "Followup_Data": str(f_data_ini) if f_nota_ini else "",
                    "Followup_Nota": f_nota_ini,
                    "Historico": f"[{dt.now().strftime('%d/%m/%Y %H:%M')}] Oportunidade cadastrada."
                }
                st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_dados_crm(st.session_state.df_crm)
                st.success("Oportunidade cadastrada e salva com sucesso na nuvem!")
                st.rerun()
