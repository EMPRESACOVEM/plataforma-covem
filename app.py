import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import urllib.parse
import datetime
import base64
import json
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
    "Pré: Novo Lead": "#00E5FF",         # Azul Claro Neon
    "Pré: Conexão": "#0047AB",           # Azul Escuro Neon
    "Prospecção": "#9D00FF",             # Roxo Neon
    "Qualificação": "#FF007F",          # Rosa Neon
    "Reunião Agendada": "#FFEA00",     # Amarelo Neon
    "Proposta Enviada": "#FF6600",     # Laranja Neon
    "Fechado": "#00FF66",              # Verde Neon
    "Pós: Standby": "#FFFFFF",          # Branco Neon
    "Pós: Perdido": "#FF0033"           # Vermelho Neon
}

CORES_PERDAS = {
    "Preço / Orçamento": "#FF0033",
    "Concorrência": "#FF6600",
    "Sem Resposta / Sumiu": "#FFEA00",
    "Produto / Serviço não Atende": "#00E5FF",
    "Outros": "#9D00FF"
}

CORES_PERFIL_BARRAS = {
    "Cliente A": "#00E5FF",
    "Cliente B": "#FF6600",
    "Cliente C": "#9D00FF"
}

FUNDO_GRAFICO_FUTURISTA = "#0A0E27"
GRID_GRAFICO_FUTURISTA = "rgba(0, 229, 255, 0.12)"

if 'funnel_colors' not in st.session_state:
    st.session_state.funnel_colors = DEFAULT_COLORS.copy()

if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "Gerenciamento de Tarefas"

if 'funnel_selecionado' not in st.session_state:
    st.session_state.funnel_selecionado = "Funil de Vendas"

if 'sub_menu_tarefas' not in st.session_state:
    st.session_state.sub_menu_tarefas = "Tarefas"

if 'editando_agenda_idx' not in st.session_state:
    st.session_state.editando_agenda_idx = None

if 'briefing_gerado_texto' not in st.session_state:
    st.session_state.briefing_gerado_texto = None

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
# LÓGICA DE GERAÇÃO DO BRIEFING DIÁRIO (20 GABRIEL / 20 ARIEL)
# ---------------------------------------------------------
def gerar_briefing_40_leads_nativo(df_crm):
    hoje_dt = date.today()
    crm_atrasados = []
    
    if not df_crm.empty and "Followup_Data" in df_crm.columns:
        c_copia = df_crm.copy()
        c_copia["Followup_Data_Dt"] = pd.to_datetime(c_copia["Followup_Data"], errors="coerce").dt.date
        c_filtrados = c_copia[c_copia["Followup_Data_Dt"] <= hoje_dt].sort_values(by="Followup_Data_Dt", ascending=True)
        
        for _, r in c_filtrados.iterrows():
            crm_atrasados.append({
                "empresa": str(r.get("Empresa", "")),
                "contato": str(r.get("Contato", "")),
                "telefone": str(r.get("Telefone", "Não informado")),
                "nota": str(r.get("Followup_Nota", "Sem observação"))
            })

    total_atrasados = len(crm_atrasados)
    leads_40 = crm_atrasados[:40]
    
    bloco_gabriel = leads_40[:20]
    bloco_ariel = leads_40[20:40]
    
    txt = f"LISTA DIÁRIA DE OPERAÇÕES - GRUPO COVEM ({hoje_dt.strftime('%d/%m/%Y')})\n"
    txt += f"Total de leads pendentes no CRM: {total_atrasados}\n"
    txt += f"Isolados os 40 mais urgentes (20 para Gabriel e 20 para Ariel):\n\n"
    
    txt += "========================================\n"
    txt += "20 LEADS PRIORITÁRIOS - VENDEDOR GABRIEL\n"
    txt += "========================================\n"
    if bloco_gabriel:
        for i, l in enumerate(bloco_gabriel, 1):
            txt += f"{i:02d}. Empresa: {l['empresa']} | Contato: {l['contato']} | Tel: {l['telefone']}\n    Obs: {l['nota']}\n"
    else:
        txt += "Nenhum lead pendente alocado para Gabriel hoje.\n"
        
    txt += "\n========================================\n"
    txt += "20 LEADS PRIORITÁRIOS - VENDEDOR ARIEL\n"
    txt += "========================================\n"
    if bloco_ariel:
        for i, l in enumerate(bloco_ariel, 1):
            txt += f"{i:02d}. Empresa: {l['empresa']} | Contato: {l['contato']} | Tel: {l['telefone']}\n    Obs: {l['nota']}\n"
    else:
        txt += "Nenhum lead pendente alocado para Ariel hoje.\n"
        
    txt += "\n========================================\n"
    txt += "META DIÁRIA DE EXECUÇÃO:\n"
    txt += "- Cada vendedor deve tratar os 20 alvos alocados acima.\n"
    txt += "- Realizar mais 30 novos contatos/prospecções (Meta de 50 movimentações diárias).\n"
    
    return txt

# ---------------------------------------------------------
# LÓGICA DE FIM DE DIA E ROLAGEM AUTOMÁTICA DE PENDÊNCIAS
# ---------------------------------------------------------
def processar_fim_de_dia_nativo(texto_relatorio, df_crm):
    hoje_dt = date.today()
    amanha_str = (hoje_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    timestamp_atual = dt.now().strftime("%d/%m/%Y %H:%M")
    
    texto_lower = texto_relatorio.lower()
    mencionados_count = 0
    mencionados_indices = set()

    for idx, row in df_crm.iterrows():
        nome_empresa = str(row["Empresa"]).strip().lower()
        if nome_empresa and (nome_empresa in texto_lower):
            mencionados_indices.add(idx)
            mencionados_count += 1
            novo_reg = f"[{timestamp_atual}] (Fim de Dia) Mencionado no relatório diário."
            hist_atual = str(row["Historico"]) if pd.notna(row["Historico"]) else ""
            df_crm.loc[idx, "Historico"] = novo_reg + ("\n" + hist_atual if hist_atual.strip() else "")

    # Rola automaticamente para o próximo dia todos os que estavam agendados para HOJE ou ATRASADOS e que NÃO foram trabalhados hoje
    rolados_count = 0
    if "Followup_Data" in df_crm.columns:
        for idx, row in df_crm.iterrows():
            if idx not in mencionados_indices:
                f_dat_raw = str(row.get("Followup_Data", "")).strip()[:10]
                if f_dat_raw and f_dat_raw not in ["nan", "NaT", "None", ""]:
                    try:
                        dt_f = dt.strptime(f_dat_raw, "%Y-%m-%d").date()
                        if dt_f <= hoje_dt:
                            df_crm.loc[idx, "Followup_Data"] = amanha_str
                            hist_atual = str(row["Historico"]) if pd.notna(row["Historico"]) else ""
                            novo_reg = f"[{timestamp_atual}] (Sistema) Pendência não finalizada no dia, rolada automaticamente para {amanha_str}."
                            df_crm.loc[idx, "Historico"] = novo_reg + ("\n" + hist_atual if hist_atual.strip() else "")
                            rolados_count += 1
                    except:
                        pass
                        
    return mencionados_count, rolados_count

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
# BARRA LATERAL
# ---------------------------------------------------------
if ARQUIVO_LOGO.exists():
    st.sidebar.image(str(ARQUIVO_LOGO), use_container_width=True)

st.sidebar.markdown("### BraClean")
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
# LOGO CENTRALIZADA DA COVEM
# ---------------------------------------------------------
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if ARQUIVO_LOGO.exists():
        st.image(str(ARQUIVO_LOGO), use_container_width=True)
    else:
        st.warning("Arquivo 'logoCOVEM.png' não encontrado na pasta do projeto.")

st.divider()

# ---------------------------------------------------------
# MENU HORIZONTAL PRINCIPAL
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

st.markdown("<div style='margin-top: 30px; margin-bottom: 30px;'><hr style='border: none; border-top: 1px solid #1E293B;'></div>", unsafe_allow_html=True)
aba_selecionada = st.session_state.menu_ativo

# ---------------------------------------------------------
# FUNÇÃO DE RENDERIZAÇÃO DA AGENDA DA SEMANA
# ---------------------------------------------------------
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
                            st.markdown(f"- **{row['Titulo']}**<br>&nbsp;&nbsp;&nbsp;&nbsp;Empresa: `{emp_vinculada}`<br>&nbsp;&nbsp;&nbsp;&nbsp;Tel: <span class='phone-highlight'>{tel_contato}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma tarefa atrasada.")

            with col_hoje:
                st.markdown(f'<div class="badge-hoje">{len(hoje_tarefas)} Tarefas para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Tarefas para Hoje"):
                    if not hoje_tarefas.empty:
                        for _, row in hoje_tarefas.iterrows():
                            emp_vinculada = row.get('Cliente', 'BraClean')
                            tel_contato = obter_telefone_por_empresa(emp_vinculada)
                            st.markdown(f"- **{row['Titulo']}**<br>&nbsp;&nbsp;&nbsp;&nbsp;Empresa: `{emp_vinculada}`<br>&nbsp;&nbsp;&nbsp;&nbsp;Tel: <span class='phone-highlight'>{tel_contato}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhuma tarefa para hoje.")
    else:
        if df_crm.empty:
            st.info("Nenhum cliente no CRM.")
        else:
            crm_temp = df.copy()
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
                            tel_crm = row.get('Telefone', 'Não informado')
                            st.markdown(f"- **{row['Empresa']}** (Contato: {row['Contato']})<br>&nbsp;&nbsp;&nbsp;&nbsp;Tel: <span class='phone-highlight'>{tel_crm}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhum follow-up atrasado.")

            with col_c_hoje:
                st.markdown(f'<div class="badge-hoje">{len(c_hoje)} Follow-ups para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Follow-ups para Hoje"):
                    if not c_hoje.empty:
                        for _, row in c_hoje.iterrows():
                            tel_crm = row.get('Telefone', 'Não informado')
                            st.markdown(f"- **{row['Empresa']}** (Contato: {row['Contato']})<br>&nbsp;&nbsp;&nbsp;&nbsp;Tel: <span class='phone-highlight'>{tel_crm}</span>", unsafe_allow_html=True)
                    else:
                        st.write("Nenhum follow-up para hoje.")

    st.divider()

# =========================================================
# ABA 1: GERENCIAMENTO DE TAREFAS (20 LEADS GABRIEL / 20 LEADS ARIEL + ROLAGEM)
# =========================================================
if aba_selecionada == "Gerenciamento de Tarefas":
    st.subheader("Gerenciamento de Tarefas & Alvos Diários — BraClean")
    
    col_brief_1, col_brief_2 = st.columns(2)

    with col_brief_1:
        if st.button("Gerar Lista Diária (20 Gabriel / 20 Ariel)", use_container_width=True):
            st.session_state.briefing_gerado_texto = gerar_briefing_40_leads_nativo(st.session_state.df_crm)

    if st.session_state.briefing_gerado_texto:
        st.markdown("### Alvos de Hoje:")
        st.text_area("Cópia da Lista Diária:", value=st.session_state.briefing_gerado_texto, height=280)
        if st.button("Limpar Lista"):
            st.session_state.briefing_gerado_texto = None
            st.rerun()

    with col_brief_2:
        with st.popover("Leitor de Fim de Dia & Rolagem Automática", use_container_width=True):
            st.markdown("**Relatório de Fim de Dia em Texto:**")
            st.caption("Cole abaixo o resumo do dia. O sistema registrará as empresas citadas e rolará automaticamente as pendências não feitas para o dia seguinte.")
            texto_fim_dia = st.text_area("Texto do Relatório:", placeholder="Digite ou cole aqui...", label_visibility="collapsed")
            
            if st.button("Processar Fim de Dia & Rolar Pendências", use_container_width=True):
                if not texto_fim_dia.strip():
                    st.warning("Insira o resumo do dia.")
                else:
                    mencionados, rolados = processar_fim_de_dia_nativo(texto_fim_dia, st.session_state.df_crm)
                    salvar_dados_crm(st.session_state.df_crm)
                    st.success(f"Sucesso! {mencionados} empresa(s) registrada(s) e {rolados} pendência(s) não finalizada(s) foram roladas para o dia seguinte.")
                    st.rerun()

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
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
                complemento_titulo = st.text_input("Detalhes adicionais (Opcional)")
                descricao = st.text_area("Descrição / Observações")

            with col2:
                cliente_vinculado = st.selectbox("Vincular ao Cliente", options=lista_clientes)
                data_vencimento = st.date_input("Data de Vencimento", min_value=datetime.date.today())
                prioridade = st.selectbox("Prioridade", options=["Baixa", "Média", "Alta", "Urgente"])

            if st.form_submit_button("Salvar Tarefa", use_container_width=True):
                titulo_final = f"{acao_selecionada}" + (f" - {complemento_titulo}" if complemento_titulo else "")
                nova_linha_tarefa = {
                    "Titulo": titulo_final, "Descricao": descricao, "Cliente": "BraClean",
                    "Data_Vencimento": str(data_vencimento), "Prioridade": prioridade, "Status": "Pendente", "Data_Criacao": str(datetime.date.today())
                }
                st.session_state.df_tarefas = pd.concat([st.session_state.df_tarefas, pd.DataFrame([nova_linha_tarefa])], ignore_index=True)
                salvar_dados_tarefas(st.session_state.df_tarefas)
                st.success("Tarefa criada com sucesso!")
                st.rerun()

    st.divider()
    st.subheader("Agenda de Tarefas e Follow Up")
    horizonte = st.selectbox("Horizonte de Visualização:", ["Próximos 7 Dias", "Próximos 15 Dias", "Próximos 30 Dias", "Todos os Registros Futuros"], label_visibility="collapsed")

    hoje = date.today()
    limite_data = hoje + timedelta(days=7 if horizonte == "Próximos 7 Dias" else (15 if horizonte == "Próximos 15 Dias" else (30 if horizonte == "Próximos 30 Dias" else 365)))

    eventos_futuros = []
    for idx_t, t in st.session_state.df_tarefas.iterrows():
        if pd.notna(t.get("Data_Vencimento")):
            try:
                dt_v = dt.strptime(str(t["Data_Vencimento"])[:10], "%Y-%m-%d").date()
                if hoje <= dt_v <= limite_data:
                    eventos_futuros.append({"origem": "tarefa", "index_original": idx_t, "Data_Formatada": dt_v.strftime("%d/%m/%Y"), "Tipo": "Tarefa", "Título / Ação": t["Titulo"], "Vinculado a": "BraClean", "Prioridade / Status": t.get('Prioridade', 'Normal')})
            except: pass

    for idx_c, c in df.iterrows():
        f_dat = c.get("Followup_Data", "")
        if pd.notna(f_dat) and str(f_dat).strip() not in ["", "nan", "NaT"]:
            try:
                dt_f = dt.strptime(str(f_dat)[:10], "%Y-%m-%d").date()
                if hoje <= dt_f <= limite_data:
                    eventos_futuros.append({"origem": "crm", "index_original": idx_c, "Data_Formatada": dt_f.strftime("%d/%m/%Y"), "Tipo": "Follow-up CRM", "Título / Ação": c.get("Followup_Nota", "Contato"), "Vinculado a": c['Empresa'], "Prioridade / Status": c['Etapa']})
            except: pass

    if eventos_futuros:
        df_futuro = pd.DataFrame(eventos_futuros).sort_values(by="Data_Formatada", ascending=True).reset_index(drop=True)
        with st.expander(f"Ver compromissos no período ({len(df_futuro)} encontrados)", expanded=True):
            st.dataframe(df_futuro[["Data_Formatada", "Tipo", "Título / Ação", "Vinculado a", "Prioridade / Status"]], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma tarefa ou follow-up agendado para este período.")

# =========================================================
# ABA 2: FUNIL DE VENDAS
# =========================================================
elif aba_selecionada == "Funil de Vendas":
    st.subheader("Gestão de Funis — BraClean")
    funis_list = ["Pré Funil", "Funil de Vendas", "Pós Funil"]
    cols_funis = st.columns(3)
    for idx_f, nome_f in enumerate(funis_list):
        with cols_funis[idx_f]:
            if st.button(nome_f, key=f"btn_funil_{idx_f}", use_container_width=True):
                st.session_state.funnel_selecionado = nome_f
                st.rerun()
    
    funil_atual = st.session_state.funnel_selecionado
    etapas_visiveis = ESTRUTURA_FUNIS.get(funil_atual, ESTRUTURA_FUNIS["Funil de Vendas"])
    cols = st.columns(len(etapas_visiveis))
    for idx, etapa in enumerate(etapas_visiveis):
        with cols[idx]:
            st.markdown(f"**{etapa}**")
            sub_df = df[df["Etapa"] == etapa]
            for _, row in sub_df.iterrows():
                with st.expander(f"{row['Empresa']}"):
                    st.write(f"Contato: {row['Contato']} | Tel: {row.get('Telefone')}")

# =========================================================
# ABA 3: DASHBOARD
# =========================================================
elif aba_selecionada == "Dashboard":
    st.subheader("Dashboard - BraClean")
    contagem = {e: len(df[df["Etapa"] == e]) for e in PROB_MAP.keys()}
    cols_m = st.columns(len(PROB_MAP))
    for i, (etapa, qtd) in enumerate(contagem.items()):
        cols_m[i].metric(etapa.replace("Pré: ", "").replace("Pós: ", ""), qtd)

# =========================================================
# ABA 4: RELATÓRIO EXECUTIVO
# =========================================================
elif aba_selecionada == "Relatório Executivo":
    st.subheader("Relatório Executivo — BraClean")
    st.metric("Total de Clientes no CRM", len(df))

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
        with col_r2:
            rapido_perfil = st.selectbox("Classificação *", OPCOES_PERFIL, index=2)
            rapido_etapa = st.selectbox("Etapa Inicial *", list(PROB_MAP.keys()))

        if st.form_submit_button("Cadastrar Rapidamente", use_container_width=True):
            if not rapido_empresa or not rapido_telefone:
                st.error("Preencha a Empresa e o Telefone.")
            else:
                novo_id = int(df["id"].max() + 1) if not df.empty and pd.notna(df["id"].max()) else 1
                nova_linha_rapida = {
                    "id": novo_id, "Empresa": rapido_empresa, "Cliente": "BraClean", "Perfil": rapido_perfil,
                    "Etapa": rapido_etapa, "Contato": "Não informado", "Cargo": "Não informado", "Telefone": rapido_telefone,
                    "Email": "Não informado", "Cidade": "Não informado", "Valor": TICKET_MEDIO_PERFIL.get(rapido_perfil, 8500.0),
                    "Prob": PROB_MAP[rapido_etapa], "Vendedor": "Gabriel", "Perda": "", "Data_Cadastro": str(date.today()),
                    "Followup_Data": str(date.today()), "Followup_Nota": "Cadastro rápido.", "Historico": "Criado via cadastro rápido."
                }
                st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha_rapida])], ignore_index=True)
                salvar_dados_crm(st.session_state.df_crm)
                st.success("Cadastrado com sucesso!")
                st.rerun()
