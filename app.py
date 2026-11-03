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
import google.generativeai as genai
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

COVEM_NAME = "GRUPO COVEM"

OPCOES_PERFIL = [
    "Cliente A",
    "Cliente B",
    "Cliente C"
]

TICKET_MEDIO_PERFIL = {
    "Cliente A": 120000.0,
    "Cliente B": 45000.0,
    "Cliente C": 8500.0
}

# Paleta de cores neon personalizada
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

if 'funnel_colors' not in st.session_state:
    st.session_state.funnel_colors = DEFAULT_COLORS.copy()

if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "Gerenciamento de Tarefas"

if 'funnel_selecionado' not in st.session_state:
    st.session_state.funnel_selecionado = "Funil de Vendas"

if 'sub_menu_tarefas' not in st.session_state:
    st.session_state.sub_menu_tarefas = "Tarefas"

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
            return df_loaded
    except Exception as e:
        st.warning(f"Aviso ao ler do Google Sheets: {e}.")

    df_inicial = pd.DataFrame([
        {
            "id": 1, "Empresa": "Usina Santa Clara", "Cliente": "BraClean", "Perfil": "Cliente A", "Etapa": "Prospecção", 
            "Contato": "Roberto Alves", "Cargo": "Diretor Operacional", "Telefone": "(16) 99876-5432", 
            "Email": "roberto@usinasantaclara.com.br", "Cidade": "Sertãozinho / SP", "Valor": 120000.0, 
            "Prob": 0.20, "Vendedor": "Gabriel", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today() - timedelta(days=2)), "Followup_Nota": "Enviar apresentação institucional atualizada.", 
            "Historico": "[01/09/2026 10:00] Primeiro contato realizado."
        }
    ])
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

def configurar_gemini_api():
    try:
        if "gemini" in st.secrets:
            if "GEMINI_API_KEY" in st.secrets["gemini"]:
                genai.configure(api_key=st.secrets["gemini"]["GEMINI_API_KEY"])
                return True
            elif "api_key" in st.secrets["gemini"]:
                genai.configure(api_key=st.secrets["gemini"]["api_key"])
                return True
        elif "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            return True
        else:
            api_key_env = os.environ.get("GEMINI_API_KEY")
            if api_key_env:
                genai.configure(api_key=api_key_env)
                return True
    except Exception as e:
        st.error(f"Erro ao configurar Gemini API: {e}")
    return False

# ---------------------------------------------------------
# GERAÇÃO DO BRIEFING DIÁRIO (20 PARA GABRIEL / 20 PARA ARIEL)
# ---------------------------------------------------------
def gerar_briefing_diario_40_leads(df_crm, df_tarefas):
    hoje_dt = date.today()
    hoje_str = hoje_dt.strftime("%Y-%m-%d")
    
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
    
    if not configurar_gemini_api():
        # Fallback estruturado caso não haja chave configurada
        texto = f"BRIEFING DIÁRIO — {hoje_dt.strftime('%d/%m/%Y')}\nTotal atrasados: {total_atrasados}\n\n=== GABRIEL (20 LEADS) ===\n"
        for i, l in enumerate(bloco_gabriel, 1):
            texto += f"{i}. {l['empresa']} | Tel: {l['telefone']} | Obs: {l['nota']}\n"
        texto += "\n=== ARIEL (20 LEADS) ===\n"
        for i, l in enumerate(bloco_ariel, 1):
            texto += f"{i}. {l['empresa']} | Tel: {l['telefone']} | Obs: {l['nota']}\n"
        return texto

    prompt = f"""
    Você é o Gerente Operacional de Vendas do GRUPO COVEM (Conta BraClean).
    Sua missão é gerar a Lista Diária de Execução dos vendedores Gabriel e Ariel para hoje ({hoje_str}).

    DIAGNOSTICO DO CRM:
    - Total de leads atrasados/pendentes no sistema: {total_atrasados}
    - Selecionei os 40 leads mais críticos para distribuição de hoje.

    BLOCO 1 (20 LEADS PARA O VENDEDOR GABRIEL):
    {json.dumps(bloco_gabriel, ensure_ascii=False)}

    BLOCO 2 (20 LEADS PARA O VENDEDOR ARIEL):
    {json.dumps(bloco_ariel, ensure_ascii=False)}

    DIRETRIZES:
    1. Organize o briefing dividindo claramente em Bloco do Gabriel (20 leads) e Bloco do Ariel (20 leads) com Empresa, Contato, Telefone e Observação.
    2. Encerre reforçando a meta diária de movimentações.
    3. Tom estritamente profissional e limpo (sem emojis).
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        if response and hasattr(response, 'text'):
            return response.text
        return "Erro: Resposta vazia da IA."
    except Exception as e:
        return f"Erro ao gerar briefing com IA (Verifique sua chave de API): {e}"

# ---------------------------------------------------------
# PROCESSAMENTO DE FIM DE DIA E ROLAGEM DE PENDÊNCIAS
# ---------------------------------------------------------
def processar_fim_de_dia_inteligente(texto_relatorio, df_crm, df_tarefas):
    if not configurar_gemini_api():
        st.error("Chave da API do Gemini necessária para processar o relatório inteligente.")
        return False

    lista_leads_ativos = df_crm[["Empresa", "Etapa", "Contato"]].to_dict(orient="records")
    amanha_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    prompt = f"""
    Você é o motor de inteligência de um CRM de alta performance (GRUPO COVEM - BraClean).
    Aqui estão os leads ativos cadastrados:
    {json.dumps(lista_leads_ativos, ensure_ascii=False)}

    O vendedor enviou o seguinte relatório de fim de dia em texto corrido:
    "{texto_relatorio}"

    INSTRUÇÕES RÍGIDAS DE ATUALIZAÇÃO E ROLAGEM:
    1. Identifique quais empresas/leads foram mencionados e quais tiveram atualizações, mudanças de etapa (opções válidas: Pré: Novo Lead, Pré: Conexão, Prospecção, Qualificação, Reunião Agendada, Proposta Enviada, Fechado, Pós: Standby, Pós: Perdido), se houve novo agendamento de follow-up (YYYY-MM-DD).
    2. REGRA DE ROLAGEM AUTOMÁTICA: Se o relatório indicar que um lead/tarefa planejado para hoje NÃO FOI ATENDIDO ou ficou pendente, altere obrigatoriamente a data de follow-up dele para o próximo dia útil ({amanha_str}) e registre no histórico que foi rolado para amanhã por falta de atendimento hoje.
    
    Retorne estritamente um array JSON válido contendo objetos com as chaves:
    - "lead_name": nome exato da empresa no CRM
    - "nova_etapa": nome da nova etapa ou "Manter"
    - "proximo_follow_up": data YYYY-MM-DD (se não atendido, coloque "{amanha_str}")
    - "nota_historico": resumo executivo para o histórico do lead
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        updates_json = json.loads(response.text)
        atualizacoes = 0
        
        for update in updates_json:
            nome_alvo = str(update.get("lead_name", "")).strip().lower()
            if not nome_alvo:
                continue
                
            for idx, row in df_crm.iterrows():
                if str(row["Empresa"]).strip().lower() == nome_alvo:
                    nova_etapa = update.get("nova_etapa", "Manter")
                    if nova_etapa and nova_etapa != "Manter" and nova_etapa in PROB_MAP:
                        df_crm.loc[idx, "Etapa"] = nova_etapa
                        df_crm.loc[idx, "Prob"] = PROB_MAP[nova_etapa]

                    novo_fu = update.get("proximo_follow_up")
                    if novo_fu:
                        df_crm.loc[idx, "Followup_Data"] = str(novo_fu)[:10]

                    nota_hist = update.get("nota_historico", "Atualização diária.")
                    timestamp = dt.now().strftime("%d/%m/%Y %H:%M")
                    novo_reg = f"[{timestamp}] (Fim de Dia) {nota_hist}"
                    
                    hist_atual = str(row["Historico"]) if pd.notna(row["Historico"]) else ""
                    df_crm.loc[idx, "Historico"] = novo_reg + ("\n" + hist_atual if hist_atual.strip() else "")
                    df_crm.loc[idx, "Followup_Nota"] = nota_hist
                    atualizacoes += 1
                    break
                    
        return atualizacoes
    except Exception as e:
        st.error(f"Erro ao processar relatório de fim de dia: {e}")
        return False

# ---------------------------------------------------------
# ESTADO DA SESSÃO
# ---------------------------------------------------------
if 'df_crm' not in st.session_state:
    st.session_state.df_crm = carregar_dados_crm()

if 'df_tarefas' not in st.session_state:
    st.session_state.df_tarefas = carregar_dados_tarefas()

df = st.session_state.df_crm

# ---------------------------------------------------------
# STATUS DE FOLLOW-UP
# ---------------------------------------------------------
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
            return "hoje", "Hoje", '<span style="height: 10px; width: 10px; background-color: #FFEA00; border-radius: 50%; display: inline-block;"></span>'
        else:
            return "em_dia", "Em Dia", '<span style="height: 10px; width: 10px; background-color: #00FF66; border-radius: 50%; display: inline-block;"></span>'
    except:
        return "sem_data", "Sem Follow-up", '<span style="height: 10px; width: 10px; background-color: #94A3B8; border-radius: 50%; display: inline-block;"></span>'

# ---------------------------------------------------------
# BARRA LATERAL
# ---------------------------------------------------------
if ARQUIVO_LOGO.exists():
    st.sidebar.image(str(ARQUIVO_LOGO), use_container_width=True)

st.sidebar.markdown("### BraClean")
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
# LOGO CENTRALIZADA E MENU PRINCIPAL
# ---------------------------------------------------------
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

# =========================================================
# ABA 1: GERENCIAMENTO DE TAREFAS (COM LEITOR DIÁRIO E FIM DE DIA)
# =========================================================
if aba_selecionada == "Gerenciamento de Tarefas":
    st.subheader("Gerenciamento de Tarefas & Alvos Diários — BraClean")
    
    col_ia_1, col_ia_2 = st.columns(2)

    with col_ia_1:
        if st.button("Gerar Briefing Matinal (20 Gabriel / 20 Ariel)", use_container_width=True):
            with st.spinner("Analisando base e separando 40 leads críticos..."):
                st.session_state.briefing_gerado_texto = gerar_briefing_diario_40_leads(st.session_state.df_crm, st.session_state.df_tarefas)

    if st.session_state.briefing_gerado_texto:
        st.markdown("### Alvos de Hoje (Gabriel & Ariel):")
        st.text_area("Cópia do Briefing Diário:", value=st.session_state.briefing_gerado_texto, height=300)
        if st.button("Limpar Briefing"):
            st.session_state.briefing_gerado_texto = None
            st.rerun()

    with col_ia_2:
        with st.popover("Processar Fim de Dia com IA (Rolagem de Pendências)", use_container_width=True):
            st.markdown("**Relatório de Fim de Dia em Texto:**")
            st.caption("Descreva o que foi feito. O que não foi feito será automaticamente rolado para amanhã.")
            texto_fim_dia = st.text_area("Relatório bruto:", placeholder="Ex: Gabriel atendeu a Usina Santa Clara (agendou para quinta). Ariel não conseguiu falar com o Cliente X...", label_visibility="collapsed")
            
            if st.button("Processar Fim de Dia & Rolar Pendências", use_container_width=True):
                if not texto_fim_dia.strip():
                    st.warning("Insira o resumo do dia.")
                else:
                    with st.spinner("Atualizando CRM e jogando pendências para amanhã..."):
                        atualizados = processar_fim_de_dia_inteligente(texto_fim_dia, st.session_state.df_crm, st.session_state.df_tarefas)
                        if atualizados is not False:
                            salvar_dados_crm(st.session_state.df_crm)
                            st.success(f"Fim de dia processado! {atualizados} registros atualizados e pendências roladas para o próximo dia útil.")
                            st.rerun()

    st.markdown("<div style='margin-bottom: 20px;'></div>", st.empty() if False else None)

    # Exibição rápida de Pendências de Hoje
    crm_temp = df.copy()
    crm_temp["status_fu"] = [calcular_status_followup(r.get("Followup_Data", ""))[0] for _, r in crm_temp.iterrows()]
    atrasados_totais = crm_temp[crm_temp["status_fu"] == "atrasado"]
    hoje_totais = crm_temp[crm_temp["status_fu"] == "hoje"]

    col_atraso, col_hoje = st.columns(2)
    with col_atraso:
        st.markdown(f'<div class="badge-atrasada">{len(atrasados_totais)} Follow-ups Atrasados na Base</div>', unsafe_allow_html=True)
    with col_hoje:
        st.markdown(f'<div class="badge-hoje">{len(hoje_totais)} Follow-ups para Hoje</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Agenda de Tarefas e Follow Up")
    horizonte = st.selectbox("Horizonte de Visualização:", ["Próximos 7 Dias", "Próximos 15 Dias", "Próximos 30 Dias", "Todos os Registros Futuros"], label_visibility="collapsed")

    hoje = date.today()
    limite_data = hoje + timedelta(days=7 if horizonte == "Próximos 7 Dias" else (15 if horizonte == "Próximos 15 Dias" else (30 if horizonte == "Próximos 30 Dias" else 365)))
    
    eventos_futuros = []
    for idx_c, c in df.iterrows():
        f_dat = c.get("Followup_Data", "")
        if pd.notna(f_dat) and str(f_dat).strip() not in ["", "nan", "NaT"]:
            try:
                dt_f = dt.strptime(str(f_dat)[:10], "%Y-%m-%d").date()
                if hoje <= dt_f <= limite_data:
                    eventos_futuros.append({"Data_Formatada": dt_f.strftime("%d/%m/%Y"), "Tipo": "Follow-up CRM", "Título / Ação": c.get("Followup_Nota", "Contato"), "Vinculado a": c['Empresa'], "Etapa": c['Etapa']})
            except: pass

    if eventos_futuros:
        df_futuro = pd.DataFrame(eventos_futuros).sort_values(by="Data_Formatada", ascending=True).reset_index(drop=True)
        with st.expander(f"Ver compromissos no período ({len(df_futuro)} encontrados)", expanded=True):
            st.dataframe(df_futuro, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum follow-up agendado para este período.")

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
