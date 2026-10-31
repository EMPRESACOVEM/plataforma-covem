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
    page_title="Plataforma Executiva GRUPO COVEM - BraClean",
    layout="wide"
)

# Caminho para arquivos secundários locais
BASE_DIR = Path(__file__).parent if "__file__" in locals() else Path.cwd()
ARQUIVO_TAREFAS = BASE_DIR / "banco_tarefas_covem.xlsx"
ARQUIVO_FUNDO = BASE_DIR / "fundo plataforma.jpg"
ARQUIVO_LOGO = BASE_DIR / "logoCOVEM.png"

# Nome Oficial do Grupo
COVEM_NAME = "GRUPO COVEM"

# Apenas a BraClean conforme solicitado
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
    "Preço / Orçamento": "#FF0033",             # Red Neon
    "Concorrência": "#FF6600",                  # Orange Neon
    "Sem Resposta / Sumiu": "#FFEA00",          # Yellow Neon
    "Produto / Serviço não Atende": "#00E5FF",  # Light Blue Neon
    "Outros": "#9D00FF"                         # Purple Neon
}

CORES_PERFIL_BARRAS = {
    "Cliente A": "#00E5FF",
    "Cliente B": "#FF6600",
    "Cliente C": "#9D00FF"
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
            div[data-testid="stMetricValue"] {{
                font-size: 22px !important;
                font-weight: 700 !important;
                color: #FFFFFF !important;
            }}
            div[data-testid="stMetricLabel"] {{
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
            df_loaded["Cliente"] = "BraClean"  # Força para BraClean
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

if 'df_crm' not in st.session_state:
    st.session_state.df_crm = carregar_dados_crm()

if 'df_tarefas' not in st.session_state:
    st.session_state.df_tarefas = carregar_dados_tarefas()

if 'cliente_editando_id' not in st.session_state:
    st.session_state.cliente_editando_id = None

df = st.session_state.df_crm

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

df_filtered = df.copy()
titulo_dinamico = "Dashboard - BraClean"
titulo_funil = "Gestão de Funis — BraClean"

st.sidebar.markdown("### Plataforma Exclusiva BraClean")
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
    df_filtered.to_excel(writer, index=False, sheet_name='CRM_BRACLEAN')
buffer.seek(0)

st.sidebar.download_button(
    label="Baixar Planilha Excel",
    data=buffer,
    file_name="crm_braclean.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if ARQUIVO_LOGO.exists():
        st.image(str(ARQUIVO_LOGO), use_container_width=True)
    else:
        st.warning("Arquivo 'logoCOVEM.png' não encontrado na pasta do projeto.")

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

def exibir_agenda_semana(df_tarefas, df_crm):
    st.markdown('<div style="margin-top: 4px;"></div>', unsafe_allow_html=True)
    c_sub1, c_sub2 = st.columns(2)
    
    with c_sub1:
        if st.button("Tarefas", key="sub_btn_tarefas", use_container_width=True):
            st.session_state.sub_menu_tarefas = "Tarefas"
            st.rerun()
    with c_sub2:
        if st.button("Follow-up", key="sub_btn_followups", use_container_width=True):
            st.session_state.sub_menu_tarefas = "Follow-up"
            st.rerun()

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
                            st.markdown(f"- **{row['Titulo']}**<br>&nbsp;&nbsp;&nbsp;&nbsp;Empresa: `{emp_vinculada}`<br>&nbsp;&nbsp;&nbsp;&nbsp;Telefone: <span class='phone-highlight'>{tel_contato}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma tarefa atrasada.")
            with col_hoje:
                st.markdown(f'<div class="badge-hoje">{len(hoje_tarefas)} Tarefas para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Tarefas para Hoje"):
                    if not hoje_tarefas.empty:
                        for _, row in hoje_tarefas.iterrows():
                            emp_vinculada = row.get('Cliente', 'BraClean')
                            tel_contato = obter_telefone_por_empresa(emp_vinculada)
                            st.markdown(f"- **{row['Titulo']}**<br>&nbsp;&nbsp;&nbsp;&nbsp;Empresa: `{emp_vinculada}`<br>&nbsp;&nbsp;&nbsp;&nbsp;Telefone: <span class='phone-highlight'>{tel_contato}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma tarefa para hoje.")
    else:
        if df_crm.empty:
            st.info("Nenhum cliente no CRM.")
        else:
            crm_temp = df_filtered.copy()
            status_list = [calcular_status_followup(r.get("Followup_Data", ""))[0] for _, r in crm_temp.iterrows()]
            crm_temp["status_fu"] = status_list

            c_atrasados = crm_temp[crm_temp["status_fu"] == "atrasado"]
            c_hoje = crm_temp[crm_temp["status_fu"] == "hoje"]

            col_c_atraso, col_c_hoje = st.columns(2)
            with col_c_atraso:
                st.markdown(f'<div class="badge-atrasada">{len(c_atrasados)} Follow-ups Atrasados</div>', unsafe_allow_html=True)
                with st.expander("Ver Follow-ups Atrasados"):
                    if not c_atrasados.empty:
                        for _, row in c_atrasados.iterrows():
                            st.markdown(f"- **{row['Empresa']}**<br>&nbsp;&nbsp;&nbsp;&nbsp;Contato: `{row['Contato']}`<br>&nbsp;&nbsp;&nbsp;&nbsp;Telefone: <span class='phone-highlight'>{row.get('Telefone', '')}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhum atrasado.")
            with col_c_hoje:
                st.markdown(f'<div class="badge-hoje">{len(c_hoje)} Follow-ups para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Follow-ups para Hoje"):
                    if not c_hoje.empty:
                        for _, row in c_hoje.iterrows():
                            st.markdown(f"- **{row['Empresa']}**<br>&nbsp;&nbsp;&nbsp;&nbsp;Contato: `{row['Contato']}`<br>&nbsp;&nbsp;&nbsp;&nbsp;Telefone: <span class='phone-highlight'>{row.get('Telefone', '')}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhum para hoje.")

# =========================================================
# ABA 1: GERENCIAMENTO DE TAREFAS
# =========================================================
if aba_selecionada == "Gerenciamento de Tarefas":
    st.subheader("Gerenciamento de Tarefas — BraClean")
    exibir_agenda_semana(st.session_state.df_tarefas, st.session_state.df_crm)

    lista_clientes = ["Nenhum / Tarefa Geral"] + df_filtered["Empresa"].dropna().tolist()

    with st.expander("Criar Nova Tarefa", expanded=False):
        with st.form(key="form_nova_tarefa_crm", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("**Selecione a Ação Rápida:**")
                acao_selecionada = st.radio("Ação", options=["Ligar", "Enviar mensagem", "Enviar e-mail", "Enviar proposta"], horizontal=True, label_visibility="collapsed")
                complemento_titulo = st.text_input("Detalhes adicionais (Opcional)")
                descricao = st.text_area("Descrição / Observações")
            with col2:
                cliente_vinculado = st.selectbox("Vincular ao Cliente", options=lista_clientes)
                data_vencimento = st.date_input("Data de Vencimento", min_value=datetime.date.today())
                prioridade = st.selectbox("Prioridade", options=["Baixa", "Média", "Alta", "Urgente"])

            if st.form_submit_button("Salvar Tarefa", use_container_width=True):
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
                st.session_state.df_tarefas = pd.concat([st.session_state.df_tarefas, pd.DataFrame([nova_linha_tarefa])], ignore_index=True)
                salvar_dados_tarefas(st.session_state.df_tarefas)
                st.success("Tarefa criada com sucesso!")
                st.rerun()

    st.divider()
    st.subheader("Agenda de Tarefas e Follow Up")
    
    horizonte = st.selectbox("Horizonte de Visualização:", ["Próximos 7 Dias", "Próximos 15 Dias", "Próximos 30 Dias", "Todos os Registros Futuros"], label_visibility="collapsed")
    hoje = date.today()
    limite_data = hoje + timedelta(days=7 if horizonte=="Próximos 7 Dias" else (15 if horizonte=="Próximos 15 Dias" else (30 if horizonte=="Próximos 30 Dias" else 365)))

    eventos_futuros = []
    df_tarefas_exibicao = st.session_state.df_tarefas.copy()

    for idx_t, t in df_tarefas_exibicao.iterrows():
        if pd.notna(t.get("Data_Vencimento")):
            try:
                dt_v = dt.strptime(str(t["Data_Vencimento"])[:10], "%Y-%m-%d").date()
                if hoje <= dt_v <= limite_data:
                    eventos_futuros.append({
                        "origem": "tarefa", "index_original": idx_t, "Data_Formatada": dt_v.strftime("%d/%m/%Y"),
                        "Tipo": "Tarefa", "Título / Ação": t["Titulo"], "Vinculado a": f"Cliente: {t.get('Cliente', 'Geral')}", "Prioridade / Status": f"Prioridade: {t.get('Prioridade', 'Normal')}"
                    })
            except:
                pass

    for idx_c, c in df_filtered.iterrows():
        f_dat = c.get("Followup_Data", "")
        if pd.notna(f_dat) and str(f_dat).strip() not in ["", "nan", "NaT"]:
            try:
                dt_f = dt.strptime(str(f_dat)[:10], "%Y-%m-%d").date()
                if hoje <= dt_f <= limite_data:
                    eventos_futuros.append({
                        "origem": "crm", "index_original": idx_c, "Data_Formatada": dt_f.strftime("%d/%m/%Y"),
                        "Tipo": "Follow-up CRM", "Título / Ação": c.get("Followup_Nota", "Contato Comercial"), "Vinculado a": f"Empresa: {c['Empresa']}", "Prioridade / Status": f"Etapa: {c['Etapa']}"
                    })
            except:
                pass

    if eventos_futuros:
        df_futuro = pd.DataFrame(eventos_futuros).sort_values(by="Data_Formatada", ascending=True).reset_index(drop=True)
        with st.expander(f"Ver compromissos no período ({len(df_futuro)} encontrados)", expanded=True):
            st.dataframe(df_futuro[["Data_Formatada", "Tipo", "Título / Ação", "Vinculado a", "Prioridade / Status"]], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma tarefa ou follow-up agendado.")

# =========================================================
# ABA 2: FUNIL DE VENDAS
# =========================================================
elif aba_selecionada == "Funil de Vendas":
    col_topo_titulo, col_topo_busca = st.columns([2, 1])
    with col_topo_titulo:
        st.subheader("Gestão de Funis — BraClean")
    with col_topo_busca:
        termo_busca = st.text_input("Pesquisar cliente", placeholder="🔍 Buscar por empresa, contato...", label_visibility="collapsed")

    funis_list = ["Pré Funil", "Funil de Vendas", "Pós Funil"]
    cols_funis = st.columns(3)
    
    for idx_f, nome_f in enumerate(funis_list):
        with cols_funis[idx_f]:
            if st.session_state.funnel_selecionado == nome_f:
                st.markdown(f"""<style>div[data-testid="column"]:nth-of-type({idx_f+1}) div.stButton > button {{ background-color: #00E5FF !important; color: #0A0E27 !important; border: 1px solid #00E5FF !important; font-weight: 700 !important; }}</style>""", unsafe_allow_html=True)
            if st.button(nome_f, key=f"btn_funil_{idx_f}", use_container_width=True):
                st.session_state.funnel_selecionado = nome_f
                st.rerun()

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    if st.session_state.cliente_editando_id is not None:
        cliente_edit_id = st.session_state.cliente_editando_id
        filtro_reg = df[df["id"] == cliente_edit_id]
        
        if not filtro_reg.empty:
            row_edit = filtro_reg.iloc[0]
            st.markdown(f"""<div style="background-color: rgba(10, 14, 39, 0.95); border: 2px solid #00E5FF; padding: 25px; border-radius: 12px; margin-bottom: 25px;"><h3 style="color: #00E5FF; margin-top: 0;">Ficha: {row_edit['Empresa']}</h3>""", unsafe_allow_html=True)
            
            with st.form(key=f"form_full_edit_{cliente_edit_id}"):
                etapas_todas = list(PROB_MAP.keys())
                edit_etapa = st.selectbox("Etapa", options=etapas_todas, index=etapas_todas.index(row_edit["Etapa"]) if row_edit["Etapa"] in etapas_todas else 0, format_func=lambda x: x.replace("Pré: ", "").replace("Pós: ", ""))
                
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
                    edit_fu_data = st.date_input("Próxima Data de Follow-up", value=date.today())
                
                edit_fu_nota = st.text_input("Nota do Follow-up", value=row_edit["Followup_Nota"])
                edit_motivo_perda = st.selectbox("Motivo de Perda", options=[""] + MOTIVOS_PERDA_PADRAO)
                
                bcol1, bcol2, bcol3 = st.columns(3)
                with bcol1:
                    btn_salvar_alt = st.form_submit_button("Salvar Alterações", use_container_width=True)
                with bcol2:
                    btn_fechar_modal = st.form_submit_button("Fechar Ficha", use_container_width=True)
                with bcol3:
                    btn_excluir = st.form_submit_button("Excluir Cliente", use_container_width=True)
                    
                idx_df = st.session_state.df_crm.index[st.session_state.df_crm["id"] == cliente_edit_id]
                if len(idx_df) > 0:
                    idx_real = idx_df[0]
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
                        salvar_dados_crm(st.session_state.df_crm)
                        st.session_state.cliente_editando_id = None
                        st.success("Atualizado!")
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

    df_funil_exibicao = df_filtered.copy()
    if termo_busca:
        df_funil_exibicao = df_funil_exibicao[df_funil_exibicao["Empresa"].str.lower().str.contains(termo_busca.lower())]

    funil_atual = st.session_state.funnel_selecionado
    etapas_visiveis = ESTRUTURA_FUNIS.get(funil_atual, ESTRUTURA_FUNIS["Funil de Vendas"])
    cols = st.columns(len(etapas_visiveis))
    
    for idx, etapa in enumerate(etapas_visiveis):
        cor_header = st.session_state.funnel_colors.get(etapa, "#00E5FF")
        with cols[idx]:
            st.markdown(f"""<div style="background: rgba(10, 14, 39, 0.95); border-top: 5px solid {cor_header}; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 12px;"><b style="font-size: 13px;">{etapa.replace('Pré: ', '').replace('Pós: ', '')}</b></div>""", unsafe_allow_html=True)
            sub_df = df_funil_exibicao[df_funil_exibicao["Etapa"] == etapa]
            for _, row in sub_df.iterrows():
                cliente_id = int(row['id'])
                with st.expander(f"{row['Empresa']}"):
                    st.markdown(f"**Contato:** {row['Contato']}<br><span class='phone-highlight'>{row.get('Telefone', '')}</span>", unsafe_allow_html=True)
                    if st.button("EDITAR", key=f"btn_edit_{cliente_id}", use_container_width=True):
                        st.session_state.cliente_editando_id = cliente_id
                        st.rerun()

# =========================================================
# ABA 3: DASHBOARD
# =========================================================
elif aba_selecionada == "Dashboard":
    st.markdown('<div class="notranslate"><h3>Dashboard - BraClean</h3></div>', unsafe_allow_html=True)
    etapas_crm = list(PROB_MAP.keys())
    contagem_calculada = {etapa: len(df_filtered[df_filtered["Etapa"] == etapa]) for etapa in etapas_crm}
    
    cols_m = st.columns(len(etapas_crm) + 1)
    for i, etapa in enumerate(etapas_crm):
        with cols_m[i]:
            st.metric(etapa.replace('Pré: ', '').replace('Pós: ', ''), contagem_calculada[etapa])
    with cols_m[-1]:
        st.metric("TOTAL", sum(contagem_calculada.values()))

    st.divider()
    df_pizza = pd.DataFrame(list(contagem_calculada.items()), columns=["Etapa", "Quantidade"])
    df_pizza_valida = df_pizza[df_pizza["Quantidade"] > 0]
    if not df_pizza_valida.empty:
        fig_pizza = px.pie(df_pizza_valida, values="Quantidade", names="Etapa", color="Etapa", color_discrete_map=st.session_state.funnel_colors, hole=0.4)
        fig_pizza.update_layout(paper_bgcolor=FUNDO_GRAFICO_FUTURISTA, plot_bgcolor=FUNDO_GRAFICO_FUTURISTA, font=dict(color="#FFFFFF"))
        st.plotly_chart(fig_pizza, use_container_width=True)

# =========================================================
# ABA 4: RELATÓRIO EXECUTIVO
# =========================================================
elif aba_selecionada == "Relatório Executivo":
    st.title("Relatório Executivo — BraClean")
    df_exec = df_filtered.copy()

    st.markdown("### Visão Macro: Comportamento de Atividades dos Vendedores")
    tipo_visao_macro = st.selectbox("Selecione a Escala Temporal:", options=["Evolução Diária", "Evolução Semanal", "Evolução Mensal"], key="select_visao_macro")

    df_macro_dinamico = df_exec.copy()
    if "Data_Cadastro" in df_macro_dinamico.columns:
        df_macro_dinamico["Data_Cadastro"] = pd.to_datetime(df_macro_dinamico["Data_Cadastro"], errors='coerce')
        df_macro_dinamico = df_macro_dinamico.dropna(subset=["Data_Cadastro"])
        
        if tipo_visao_macro == "Evolução Diária":
            df_macro_dinamico["Periodo"] = df_macro_dinamico["Data_Cadastro"].dt.strftime("%d/%m/%Y (%a)")
            df_agrupado = df_macro_dinamico.groupby(["Periodo", "Vendedor", df_macro_dinamico["Data_Cadastro"].dt.date]).size().reset_index(name="Volume de Atividades")
            df_agrupado = df_agrupado.sort_values(by="Data_Cadastro")
        elif tipo_visao_macro == "Evolução Semanal":
            df_macro_dinamico["Periodo"] = "Semana " + df_macro_dinamico["Data_Cadastro"].dt.isocalendar().week.astype(str)
            df_agrupado = df_macro_dinamico.groupby(["Periodo", "Vendedor"]).size().reset_index(name="Volume de Atividades")
        else:
            df_agrupado_mes = df_macro_dinamico.groupby([df_macro_dinamico["Data_Cadastro"].dt.to_period("M"), "Vendedor"]).size().reset_index(name="Volume de Atividades")
            df_agrupado_mes["Periodo"] = df_agrupado_mes["Data_Cadastro"].dt.strftime("%B / %Y")
            df_agrupado = df_agrupado_mes.sort_values(by="Data_Cadastro")
    else:
        df_agrupado = pd.DataFrame(columns=["Periodo", "Vendedor", "Volume de Atividades"])

    cores_vendedores_map = {"Gabriel": "#FF0033", "Ariel": "#00E5FF"}
    if not df_agrupado.empty:
        fig_macro_progressivo = px.line(df_agrupado, x="Periodo", y="Volume de Atividades", color="Vendedor", markers=True, title=f"Comportamento Operacional — {tipo_visao_macro}", color_discrete_map=cores_vendedores_map)
        fig_macro_progressivo.update_layout(paper_bgcolor=FUNDO_GRAFICO_FUTURISTA, plot_bgcolor=FUNDO_GRAFICO_FUTURISTA, font=dict(color="#FFFFFF"))
        st.plotly_chart(fig_macro_progressivo, use_container_width=True)

    st.divider()
    st.markdown("### Meta BraClean (R$ 100k Mensais até Dezembro)")
    faturamento_braclean = float(df_exec[df_exec["Etapa"] == "Fechado"]["Valor"].sum())
    meta_alvo = 100000.0
    
    bm1, bm2 = st.columns(2)
    bm1.metric("Meta Faturamento Mensal", f"R$ {meta_alvo:,.2f}")
    bm2.metric("Faturamento Fechado Atual", f"R$ {faturamento_braclean:,.2f}")

# =========================================================
# ABA 5: + NOVO CADASTRO
# =========================================================
elif aba_selecionada == "+ Novo Cadastro":
    st.subheader("+ Novo Cadastro Exclusivo BraClean")
    with st.form("form_oportunidade_braclean", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nova_empresa = st.text_input("Nome da Empresa *")
            novo_perfil = st.selectbox("Classificação do Lead *", OPCOES_PERFIL, index=2)
            novo_contato = st.text_input("Contato")
            novo_telefone = st.text_input("Telefone *")
        with col_f2:
            novo_vendedor = st.selectbox("Vendedor", options=["Gabriel", "Ariel"])
            nova_valor = st.number_input("Valor Estimado Mensal (R$)", min_value=0.0, step=1000.0)
            nova_etapa = st.selectbox("Etapa Inicial *", list(PROB_MAP.keys()), format_func=lambda x: x.replace("Pré: ", "").replace("Pós: ", ""))

        if st.form_submit_button("Salvar Oportunidade"):
            if not nova_empresa or not novo_telefone:
                st.error("Preencha os campos obrigatórios.")
            else:
                novo_id = int(df["id"].max() + 1) if not df.empty and pd.notna(df["id"].max()) else 1
                nova_linha = {
                    "id": novo_id, "Empresa": nova_empresa, "Cliente": "BraClean", "Perfil": novo_perfil,
                    "Etapa": nova_etapa, "Contato": novo_contato or "Não informado", "Cargo": "Não informado",
                    "Telefone": novo_telefone, "Email": "Não informado", "Cidade": "Não informado",
                    "Valor": nova_valor, "Prob": PROB_MAP[nova_etapa], "Vendedor": novo_vendedor,
                    "Perda": "", "Data_Cadastro": str(date.today()), "Followup_Data": str(date.today()),
                    "Followup_Nota": "Cadastro BraClean.", "Historico": f"[{dt.now().strftime('%d/%m/%Y %H:%M')}] Criado."
                }
                st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_dados_crm(st.session_state.df_crm)
                st.success("Salvo com sucesso!")
                st.rerun()
