import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import urllib.parse
import datetime
from datetime import datetime as dt, date, timedelta
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Plataforma Executiva GRUPO COVEM",
    page_icon="🏢",
    layout="wide"
)

# Caminho do diretório base
BASE_DIR = Path(__file__).parent if "__file__" in locals() else Path.cwd()

# Nome Oficial do Grupo
COVEM_NAME = "GRUPO COVEM"

# Lista de Clientes do GRUPO COVEM
CARTEIRAS_COVEM = ["BraClean", "QV Energia Solar", "Elleven"]

# ---------------------------------------------------------
# PALETA COVEM & ESTILIZAÇÃO CSS (Identidade Visual Ciano/Azul COVEM)
# ---------------------------------------------------------
DEFAULT_COLORS = {
    "1. Contatado": "#EC4899",         # Rosa
    "2. Conversando": "#EAB308",        # Amarelo
    "3. Reunião Agendada": "#00A3FF",  # Azul Ciano COVEM
    "4. Proposta Enviada": "#3B82F6",  # Azul
    "5. Fechado": "#22C55E",           # Verde
    "6. Perdido": "#EF4444"            # Vermelho
}

CORES_PERDAS = {
    "Preço / Orçamento": "#EF4444",             # Vermelho
    "Concorrência": "#00A3FF",                  # Azul Ciano COVEM
    "Sem Resposta / Sumiu": "#EAB308",          # Amarelo
    "Produto / Serviço não Atende": "#3B82F6",  # Azul
    "Outros": "#D1D5DB"                         # Cinza Claro
}

if 'funnel_colors' not in st.session_state:
    st.session_state.funnel_colors = DEFAULT_COLORS.copy()

st.markdown("""
    <style>
        /* Importação da Fonte Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: #0B0F19 !important;
            color: #F1F5F9 !important;
        }

        .notranslate, [data-testid="stSidebar"], [data-baseweb="select"] {
            translate: no !important;
        }

        /* Ajuste do Fundo da Sidebar para combinar com o tema COVEM */
        [data-testid="stSidebar"] {
            background-color: #111827 !important;
            border-right: 1px solid #1F2937;
        }

        h1, h2, h3, h4 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.4px !important;
        }

        /* Título Principal Executivo Centralizado e Sofisticado */
        .title-covem-container {
            text-align: center;
            width: 100%;
            margin-top: -15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid #1F2937;
        }

        .title-covem {
            font-family: 'Inter', sans-serif;
            font-size: 44px;
            font-weight: 900;
            letter-spacing: 2px;
            color: #F8FAFC;
            text-transform: uppercase;
            margin: 0;
            text-shadow: 0 2px 10px rgba(0, 163, 255, 0.15);
        }

        .subtitle-covem {
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 500;
            color: #94A3B8;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-top: 5px;
        }

        /* Subtítulos */
        .section-header {
            font-family: 'Inter', sans-serif;
            font-size: 20px;
            font-weight: 600;
            color: #E2E8F0;
            letter-spacing: -0.3px;
            margin-top: 15px;
            margin-bottom: 12px;
        }

        /* Badges Unificadas com Fundo Azul Ciano COVEM e Detalhes de Alerta */
        .badge-covem-base {
            background-color: rgba(0, 163, 255, 0.12);
            border: 1px solid #00A3FF;
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
            text-align: center;
            width: 100%;
        }

        .badge-atrasada {
            color: #FCA5A5;
        }

        .badge-hoje {
            color: #FDE047;
        }

        .badge-sucesso {
            color: #86EFAC;
        }

        .phone-highlight {
            color: #00A3FF;
            font-weight: 600;
        }

        div[data-testid="stVerticalBlock"] > div {
            gap: 0.15rem !important;
        }

        div[data-testid="stMetricValue"] {
            font-family: 'Inter', sans-serif !important;
            font-size: 22px !important;
            font-weight: 700 !important;
            color: #00A3FF !important;
        }

        div[data-testid="stMetricLabel"] {
            font-family: 'Inter', sans-serif !important;
            font-size: 12px !important;
        }
    </style>
""", unsafe_allow_html=True)

PROB_MAP = {
    "1. Contatado": 0.20,
    "2. Conversando": 0.40,
    "3. Reunião Agendada": 0.60,
    "4. Proposta Enviada": 0.80,
    "5. Fechado": 1.00,
    "6. Perdido": 0.00
}

MOTIVOS_PERDA_PADRAO = list(CORES_PERDAS.keys())

# ---------------------------------------------------------
# ESTADO DA SESSÃO (CRM, TAREFAS, HISTÓRICO E FINANCEIRO)
# ---------------------------------------------------------
if 'df_crm' not in st.session_state:
    st.session_state.df_crm = pd.DataFrame([
        {
            "id": 1, "Empresa": "Grupo Delta", "Cliente": "BraClean", "Etapa": "1. Contatado", 
            "Contato": "Roberto Alves", "Cargo": "Diretor Comercial", "Telefone": "(16) 99876-5432", 
            "Email": "roberto@grupodelta.com.br", "Cidade": "Sertãozinho / SP", "Valor": 50000.0, 
            "Prob": 0.20, "Vendedor": "Lucas Mendes", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today() - timedelta(days=2)), "Followup_Nota": "Enviar apresentação institucional atualizada.", 
            "Historico": "01/09: Primeiro contato realizado."
        },
        {
            "id": 2, "Empresa": "Sistemas Sigma", "Cliente": "QV Energia Solar", "Etapa": "1. Contatado", 
            "Contato": "Patricia Lima", "Cargo": "Gerente de Compras", "Telefone": "(16) 99765-4321", 
            "Email": "patricia@sigmasistemas.com.br", "Cidade": "Ribeirão Preto / SP", "Valor": 35000.0, 
            "Prob": 0.20, "Vendedor": "Lucas Mendes", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today()), "Followup_Nota": "Ligar para confirmar se recebeu o e-mail.", 
            "Historico": "02/09: E-mail enviado."
        },
        {
            "id": 3, "Empresa": "Indústria Omega", "Cliente": "Elleven", "Etapa": "2. Conversando", 
            "Contato": "Fernando Souza", "Cargo": "Sócio-Proprietário", "Telefone": "(11) 98123-4567", 
            "Email": "fernando@omegaind.com.br", "Cidade": "São Paulo / SP", "Valor": 80000.0, 
            "Prob": 0.40, "Vendedor": "Gabriel Silva", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today() + timedelta(days=3)), "Followup_Nota": "Alinhar escopo do projeto técnico.", 
            "Historico": "30/08: Reunião inicial."
        },
        {
            "id": 4, "Empresa": "Tecnologia Beta", "Cliente": "BraClean", "Etapa": "6. Perdido", 
            "Contato": "Carlos Eduardo", "Cargo": "Comprador", "Telefone": "(16) 98888-7777", 
            "Email": "carlos@betatech.com", "Cidade": "Sertãozinho / SP", "Valor": 25000.0, 
            "Prob": 0.00, "Vendedor": "Lucas Mendes", "Perda": "Preço / Orçamento",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": "", "Followup_Nota": "", 
            "Historico": "25/08: Achou o valor acima do orçamento."
        }
    ])

if 'df_tarefas' not in st.session_state:
    st.session_state.df_tarefas = pd.DataFrame([
        {
            "Titulo": "Enviar proposta comercial",
            "Descricao": "Elaborar minuta contratual e enviar em PDF",
            "Cliente": "Grupo Delta",
            "Data_Vencimento": str(date.today() - timedelta(days=1)),
            "Prioridade": "Alta",
            "Status": "Pendente",
            "Data_Criacao": str(date.today() - timedelta(days=3))
        },
        {
            "Titulo": "Reunião de Alinhamento",
            "Descricao": "Validar requisitos técnicos",
            "Cliente": "Indústria Omega",
            "Data_Vencimento": str(date.today()),
            "Prioridade": "Urgente",
            "Status": "Pendente",
            "Data_Criacao": str(date.today() - timedelta(days=1))
        }
    ])

if 'df_historico_executivo' not in st.session_state:
    st.session_state.df_historico_executivo = pd.DataFrame([
        {"Mês/Ano": "Out/25", "Leads Qualificados": 12, "Reuniões Agendadas": 4, "Propostas Enviadas": 2, "Projetos Fechados": 1},
        {"Mês/Ano": "Nov/25", "Leads Qualificados": 15, "Reuniões Agendadas": 6, "Propostas Enviadas": 4, "Projetos Fechados": 2},
        {"Mês/Ano": "Dez/25", "Leads Qualificados": 13, "Reuniões Agendadas": 7, "Propostas Enviadas": 5, "Projetos Fechados": 3},
        {"Mês/Ano": "Jan/26", "Leads Qualificados": 25, "Reuniões Agendadas": 9, "Propostas Enviadas": 7, "Projetos Fechados": 4},
        {"Mês/Ano": "Fev/26", "Leads Qualificados": 15, "Reuniões Agendadas": 12, "Propostas Enviadas": 10, "Projetos Fechados": 6}
    ])

if 'df_historico_financeiro' not in st.session_state:
    st.session_state.df_historico_financeiro = pd.DataFrame([
        {"Mês/Ano": "Out/25", "Pipeline Total (R$)": 180000.0, "Receita Fechada (R$)": 90000.0},
        {"Mês/Ano": "Nov/25", "Pipeline Total (R$)": 140000.0, "Receita Fechada (R$)": 80000.0},
        {"Mês/Ano": "Dez/25", "Pipeline Total (R$)": 310000.0, "Receita Fechada (R$)": 200000.0},
        {"Mês/Ano": "Jan/26", "Pipeline Total (R$)": 120000.0, "Receita Fechada (R$)": 55000.0},
        {"Mês/Ano": "Fev/26", "Pipeline Total (R$)": 525000.0, "Receita Fechada (R$)": 285000.0}
    ])

if 'manual_counts' not in st.session_state:
    st.session_state.manual_counts = {}

if 'manual_perdas' not in st.session_state:
    st.session_state.manual_perdas = None

df = st.session_state.df_crm

# ---------------------------------------------------------
# FUNÇÕES DE LÓGICA DE CORES DO FOLLOW-UP
# ---------------------------------------------------------
def calcular_status_followup(data_str):
    if not data_str or pd.isna(data_str) or str(data_str).strip() == "":
        return "sem_data", "Sem Follow-up", "⚪"
    try:
        dt_follow = dt.strptime(str(data_str), "%Y-%m-%d").date()
        hoje = date.today()
        if dt_follow < hoje:
            return "atrasado", "Atrasado", "🔴"
        elif dt_follow == hoje:
            return "hoje", "Atenção (Hoje)", "🟡"
        else:
            return "em_dia", "Em Dia", "🟢"
    except:
        return "sem_data", "Sem Follow-up", "⚪"

# ---------------------------------------------------------
# BARRA LATERAL (COM A LOGO DA COVEM NO TOPO)
# ---------------------------------------------------------
logo_path = BASE_DIR / "covem logo vert.png"

if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #00A3FF; margin-bottom: 0px;'>GRUPO COVEM</h2>", unsafe_allow_html=True)

st.sidebar.divider()

opcoes_filtro = ["TODOS"] + CARTEIRAS_COVEM

# Seletor de clientes posicionado logo abaixo da logo na barra lateral
cliente_sel = st.sidebar.selectbox("Clientes COVEM:", opcoes_filtro)

if cliente_sel != "TODOS":
    df_filtered = df[df["Cliente"] == cliente_sel]
    titulo_dinamico = f"CRM — {cliente_sel}"
else:
    df_filtered = df
    titulo_dinamico = COVEM_NAME

st.sidebar.divider()

with st.sidebar.expander("Personalizar Cores das Etapas", expanded=False):
    st.caption("Altere as cores das etapas do funil:")
    for etapa_nome in PROB_MAP.keys():
        cor_atual = st.session_state.funnel_colors.get(etapa_nome, "#00A3FF")
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
# 1. TÍTULO PRINCIPAL: GRUPO COVEM (CENTRALIZADO E SOFISTICADO)
# ---------------------------------------------------------
st.markdown(
    f"""
    <div class="title-covem-container">
        <div class="title-covem">{COVEM_NAME}</div>
        <div class="subtitle-covem">Plataforma Executiva de Gestão Comercial e Operacional</div>
    </div>
    """, 
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# FUNÇÃO DE RENDERIZAÇÃO DA AGENDA DA SEMANA
# ---------------------------------------------------------
def exibir_agenda_semana(df_tarefas, df_crm):
    st.markdown('<div class="section-header">Agenda da Semana</div>', unsafe_allow_html=True)
    
    tab_alertas_tarefas, tab_alertas_crm = st.tabs(["Tarefas", "Follow-ups (CRM)"])

    with tab_alertas_tarefas:
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
                st.markdown(f'<div class="badge-covem-base badge-atrasada">🔴 {len(atrasadas)} Tarefas Atrasadas</div>', unsafe_allow_html=True)
                with st.expander("Ver Tarefas Atrasadas"):
                    if not atrasadas.empty:
                        for _, row in atrasadas.iterrows():
                            st.write(f"• **{row['Titulo']}** | Cliente: `{row.get('Cliente', 'N/A')}` | Vencimento: {row['Data_Vencimento'].strftime('%d/%m/%Y')}")
                    else:
                        st.write("Nenhuma tarefa atrasada.")

            with col_hoje:
                st.markdown(f'<div class="badge-covem-base badge-hoje">🟡 {len(hoje_tarefas)} Tarefas para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Tarefas para Hoje"):
                    if not hoje_tarefas.empty:
                        for _, row in hoje_tarefas.iterrows():
                            st.write(f"• **{row['Titulo']}** | Cliente: `{row.get('Cliente', 'N/A')}`")
                    else:
                        st.write("Nenhuma tarefa para hoje.")

    with tab_alertas_crm:
        if df_crm.empty:
            st.info("Nenhum cliente no CRM.")
        else:
            crm_temp = df_crm.copy()
            
            status_list = []
            for _, r in crm_temp.iterrows():
                st_code, st_label, st_icon = calcular_status_followup(r.get("Followup_Data", ""))
                status_list.append(st_code)
            crm_temp["status_fu"] = status_list

            c_atrasados = crm_temp[crm_temp["status_fu"] == "atrasado"]
            c_hoje = crm_temp[crm_temp["status_fu"] == "hoje"]

            col_c_atraso, col_c_hoje = st.columns(2)

            with col_c_atraso:
                st.markdown(f'<div class="badge-covem-base badge-atrasada">🔴 {len(c_atrasados)} Follow-ups Atrasados</div>', unsafe_allow_html=True)
                with st.expander("Ver Follow-ups Atrasados"):
                    if not c_atrasados.empty:
                        for _, row in c_atrasados.iterrows():
                            dt_f_br = dt.strptime(str(row['Followup_Data']), "%Y-%m-%d").strftime("%d/%m/%Y") if row['Followup_Data'] else "Sem Data"
                            st.write(f"• 🔴 **{row['Empresa']}** | Contato: `{row['Contato']}` | Data: {dt_f_br}")
                    else:
                        st.write("Nenhum follow-up atrasado.")

            with col_c_hoje:
                st.markdown(f'<div class="badge-covem-base badge-hoje">🟡 {len(c_hoje)} Follow-ups para Hoje</div>', unsafe_allow_html=True)
                with st.expander("Ver Follow-ups para Hoje"):
                    if not c_hoje.empty:
                        for _, row in c_hoje.iterrows():
                            dt_f_br = dt.strptime(str(row['Followup_Data']), "%Y-%m-%d").strftime("%d/%m/%Y") if row['Followup_Data'] else "Sem Data"
                            st.write(f"• 🟡 **{row['Empresa']}** | Contato: `{row['Contato']}`")
                    else:
                        st.write("Nenhum follow-up para hoje.")

    st.divider()

# ---------------------------------------------------------
# NAVEGAÇÃO POR ABAS
# ---------------------------------------------------------
aba_tarefas, aba_crm, aba_dash, aba_relatorio, aba_novo = st.tabs([
    "Gerenciador de Tarefas",
    "Funil de Vendas", 
    "Dashboard", 
    "Relatório Executivo", 
    "➕ Novo Cadastro"
])

def criar_link_google_agenda(empresa, contato, nota_followup, data_str):
    if not data_str:
        return "#"
    try:
        dt_obj = dt.strptime(data_str, "%Y-%m-%d")
        dt_formatada = dt_obj.strftime("%Y%m%dT090000Z/%Y%m%dT100000Z")
        params = {
            "action": "TEMPLATE",
            "text": f"Follow-up CRM: {empresa}",
            "details": f"Contato: {contato}\n\nAção / Lembrete:\n{nota_followup}",
            "dates": dt_formatada
        }
        return f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
    except:
        return "#"

# =========================================================
# ABA 1: GERENCIADOR DE TAREFAS
# =========================================================
with aba_tarefas:
    exibir_agenda_semana(st.session_state.df_tarefas, st.session_state.df_crm)
    
    st.subheader("Gerenciador de Tarefas")

    lista_clientes = (
        ["Nenhum / Tarefa Geral"] + st.session_state.df_crm["Empresa"].dropna().tolist()
        if not st.session_state.df_crm.empty
        else ["Nenhum / Tarefa Geral"]
    )

    with st.expander("➕ Criar Nova Tarefa", expanded=False):
        with st.form(key="form_nova_tarefa_crm", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                titulo_tarefa = st.text_input("Título da Tarefa / Ação")
                descricao = st.text_area("Descrição / Detalhes")

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

            if submit_tarefa and titulo_tarefa:
                nova_linha_tarefa = {
                    "Titulo": titulo_tarefa,
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
                st.success(f"Tarefa '{titulo_tarefa}' vinculada a '{cliente_vinculado}' com sucesso!")
                st.rerun()

    st.markdown("#### Lista Geral de Tarefas")
    if not st.session_state.df_tarefas.empty:
        st.dataframe(st.session_state.df_tarefas, use_container_width=True)
    else:
        st.info("Nenhuma tarefa pendente.")

# =========================================================
# ABA 2: FUNIL DE VENDAS
# =========================================================
with aba_crm:
    st.subheader(f"Funil de Vendas — {titulo_dinamico}")

    etapas = list(PROB_MAP.keys())
    cols = st.columns(len(etapas))
    
    for idx, etapa in enumerate(etapas):
        cor_header = st.session_state.funnel_colors.get(etapa, "#00A3FF")
        
        with cols[idx]:
            st.markdown(
                f"""
                <div style="background-color: {cor_header}; padding: 6px; border-radius: 6px; text-align: center; margin-bottom: 8px;">
                    <b style="color: #FFFFFF; font-size: 12px;">{etapa}</b>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            sub_df = df_filtered[df_filtered["Etapa"] == etapa]
            
            for _, row in sub_df.iterrows():
                st_code, st_label, st_icon = calcular_status_followup(row.get("Followup_Data", ""))
                
                with st.expander(f"{st_icon} {row['Empresa']}"):
                    dt_f_exib = row.get('Followup_Data', '')
                    dt_f_str = dt.strptime(str(dt_f_exib), "%Y-%m-%d").strftime("%d/%m/%Y") if dt_f_exib else "Não agendado"
                    
                    st.markdown(
                        f"""
                        <div style="line-height: 1.25; margin-bottom: 2px;">
                            <span style="font-size: 13px;"><b>{st_icon} {row['Empresa']}</b></span><br>
                            <span style="font-size: 12px; color: #94A3B8;">{row['Contato']}</span><br>
                            <span class="phone-highlight" style="font-size: 12px;">{row.get('Telefone', 'Não informado')}</span><br>
                            <span style="font-size: 11px; color: #CBD5E1;">Follow-up: {dt_f_str} ({st_label})</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

# =========================================================
# ABA 3: DASHBOARD
# =========================================================
with aba_dash:
    st.markdown(f'<div class="notranslate"><h3>1. DISTRIBUIÇÃO DO FUNIL DE VENDAS ({COVEM_NAME})</h3></div>', unsafe_allow_html=True)
    
    col_f1, _ = st.columns([2, 2])
    with col_f1:
        periodo_sel = st.selectbox(
            "Visualizar Período:", 
            ["Todos os Registros", "Esta Semana", "15 Dias", "1 Mês", "2 Meses", "3 Meses"]
        )
    
    df_dash = df_filtered.copy()
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
        contagem_calculada[etapa] = st.session_state.manual_counts.get(etapa, count_real)
        
    total_leads = sum(contagem_calculada.values())

    cols_m = st.columns(len(etapas_crm) + 1)
    
    for i, etapa in enumerate(etapas_crm):
        cor_header = st.session_state.funnel_colors.get(etapa, "#00A3FF")
        qtd = contagem_calculada[etapa]
        
        with cols_m[i]:
            st.markdown(
                f"""
                <div style="background-color: {cor_header}; padding: 4px; border-radius: 4px; text-align: center; margin-bottom: 4px;">
                    <b style="color: #FFFFFF; font-size: 11px;">{etapa}</b>
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.metric(label="", value=qtd)

    with cols_m[-1]:
        st.markdown(
            """
            <div style="background-color: #0F172A; padding: 4px; border-radius: 4px; text-align: center; margin-bottom: 4px;">
                <b style="color: #FFFFFF; font-size: 11px;">TOTAL</b>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.metric(label="", value=total_leads)

    with st.expander("Editar Números das Etapas Manualmente (Ajuste Rápido)"):
        st.caption("Ajuste a quantidade de cada etapa caso queira simular os totais diretamente no painel:")
        cols_input = st.columns(len(etapas_crm))
        
        for idx, etapa in enumerate(etapas_crm):
            val_atual = contagem_calculada[etapa]
            novo_val = cols_input[idx].number_input(
                etapa, 
                min_value=0, 
                value=int(val_atual), 
                key=f"edit_dash_{etapa}"
            )
            st.session_state.manual_counts[etapa] = novo_val
        
        if st.button("Resetar para Dados Reais do CRM"):
            st.session_state.manual_counts = {}
            st.rerun()

    st.divider()

    st.markdown(f'<div class="notranslate"><h3>Funil de Vendas — {COVEM_NAME}</h3></div>', unsafe_allow_html=True)
    df_pizza = pd.DataFrame(list(contagem_calculada.items()), columns=["Etapa", "Quantidade"])
    df_pizza_valida = df_pizza[df_pizza["Quantidade"] > 0]

    if not df_pizza_valida.empty:
        fig_pizza = px.pie(
            df_pizza_valida, 
            values="Quantidade", 
            names="Etapa",
            color="Etapa",
            color_discrete_map=st.session_state.funnel_colors,
            hole=0.0
        )
        fig_pizza.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1E293B",
            plot_bgcolor="#1E293B",
            font=dict(color="#FFFFFF", size=13),
            height=440
        )
        fig_pizza.update_traces(textinfo="percent+value")
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para o período selecionado.")

    st.divider()

    st.subheader("2. ANÁLISE DE MOTIVOS DE PERDA")

    df_perdidos = df_dash[df_dash["Etapa"] == "6. Perdido"]
    perdas_reais = {m: 0 for m in MOTIVOS_PERDA_PADRAO}
    for p in df_perdidos["Perda"]:
        p_str = str(p).strip()
        if p_str in perdas_reais:
            perdas_reais[p_str] += 1
        elif p_str != "":
            perdas_reais["Outros"] += 1

    if st.session_state.manual_perdas is None:
        st.session_state.manual_perdas = perdas_reais.copy()

    with st.expander("Tabela Editável: Ajustar Quantidade por Motivo de Perda", expanded=True):
        cols_p = st.columns(len(MOTIVOS_PERDA_PADRAO))
        for idx, motivo in enumerate(MOTIVOS_PERDA_PADRAO):
            val_motivo = st.session_state.manual_perdas.get(motivo, 0)
            novo_val_m = cols_p[idx].number_input(
                motivo, 
                min_value=0, 
                value=int(val_motivo), 
                key=f"perda_input_{motivo}"
            )
            st.session_state.manual_perdas[motivo] = novo_val_m
            
        c_p1, _ = st.columns([1, 4])
        with c_p1:
            if st.button("Sincronizar com CRM", key="reset_perdas"):
                st.session_state.manual_perdas = perdas_reais.copy()
                st.rerun()

    df_graf_perdas = pd.DataFrame(
        list(st.session_state.manual_perdas.items()), 
        columns=["Motivo de Perda", "Quantidade"]
    )
    total_perdas_num = df_graf_perdas["Quantidade"].sum()

    if total_perdas_num > 0:
        fig_barras_perda = px.bar(
            df_graf_perdas,
            x="Motivo de Perda",
            y="Quantidade",
            text="Quantidade",
            title=f"Motivos de Perda — {COVEM_NAME} (Total: {total_perdas_num})",
            color="Motivo de Perda",
            color_discrete_map=CORES_PERDAS
        )
        fig_barras_perda.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1E293B",
            plot_bgcolor="#1E293B",
            font=dict(color="#FFFFFF", size=13),
            xaxis_title="MOTIVO",
            yaxis_title="QUANTIDADE DE OPORTUNIDADES",
            showlegend=False,
            height=420
        )
        fig_barras_perda.update_traces(textposition="outside")
        st.plotly_chart(fig_barras_perda, use_container_width=True)
    else:
        st.info("Nenhuma perda registrada no momento.")

# =========================================================
# ABA 4: RELATÓRIO EXECUTIVO
# =========================================================
with aba_relatorio:
    st.title("Relatório Executivo")
    st.caption("Acompanhamento histórico de atividades operacionais e evolução financeira.")

    st.subheader("1. Histórico de Evolução de Atividades & Prospecção")

    with st.expander("Exibir / Ocultar Tabela de Histórico de Atividades", expanded=True):
        df_hist = st.session_state.df_historico_executivo.copy()

        def estilizar_atividades(val):
            return [
                'background-color: #FEF08A; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #00A3FF; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #FACC15; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #FB923C; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #4ADE80; color: #000000; font-weight: bold; text-align: center;'  
            ]

        df_styled = df_hist.style.apply(estilizar_atividades, axis=1)
        st.dataframe(df_styled, use_container_width=True, hide_index=True)

        st.caption("Adicionar ou remover meses da tabela de atividades:")
        c_add1, c_add2, c_add3, c_add4, c_add5 = st.columns(5)
        with c_add1:
            novo_mes_atv = st.text_input("Mês/Ano", value="Mar/26", key="atv_mes")
        with c_add2:
            n_leads = st.number_input("Leads Qualificados", min_value=0, value=20, key="atv_leads")
        with c_add3:
            n_reunioes = st.number_input("Reuniões Agendadas", min_value=0, value=14, key="atv_reun")
        with c_add4:
            n_propostas = st.number_input("Propostas Enviadas", min_value=0, value=11, key="atv_prop")
        with c_add5:
            n_fechados = st.number_input("Projetos Fechados", min_value=0, value=7, key="atv_fech")

        c_b1, c_b2 = st.columns([1.5, 4])
        with c_b1:
            if st.button("Adicionar Mês (Atividades)", use_container_width=True):
                nova_linha_hist = {
                    "Mês/Ano": novo_mes_atv,
                    "Leads Qualificados": n_leads,
                    "Reuniões Agendadas": n_reunioes,
                    "Propostas Enviadas": n_propostas,
                    "Projetos Fechados": n_fechados
                }
                st.session_state.df_historico_executivo = pd.concat([
                    st.session_state.df_historico_executivo, 
                    pd.DataFrame([nova_linha_hist])
                ], ignore_index=True)
                st.rerun()
        with c_b2:
            if st.button("Remover Último Mês (Atividades)"):
                if len(st.session_state.df_historico_executivo) > 1:
                    st.session_state.df_historico_executivo = st.session_state.df_historico_executivo.iloc[:-1]
                    st.rerun()

    if not st.session_state.df_historico_executivo.empty:
        df_melted_atv = st.session_state.df_historico_executivo.melt(
            id_vars=["Mês/Ano"], 
            value_vars=["Leads Qualificados", "Reuniões Agendadas", "Propostas Enviadas", "Projetos Fechados"],
            var_name="Métrica", 
            value_name="Quantidade"
        )
        
        cores_atv = {
            "Leads Qualificados": "#00A3FF",   
            "Reuniões Agendadas": "#FACC15",   
            "Propostas Enviadas": "#FB923C",   
            "Projetos Fechados": "#4ADE80"    
        }

        fig_linha_atv = px.line(
            df_melted_atv,
            x="Mês/Ano",
            y="Quantidade",
            color="Métrica",
            text="Quantidade",
            markers=True,
            title=f"Evolução Mensal de Atividades & Prospecção — {COVEM_NAME}",
            color_discrete_map=cores_atv
        )
        fig_linha_atv.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1E293B",
            plot_bgcolor="#1E293B",
            font=dict(color="#FFFFFF", size=13),
            xaxis_title="MÊS / ANO",
            yaxis_title="QUANTIDADE",
            height=440,
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
        )
        fig_linha_atv.update_traces(textposition="top center")
        st.plotly_chart(fig_linha_atv, use_container_width=True)

    st.divider()

    st.subheader("2. Histórico de Evolução Financeira")

    with st.expander("Exibir / Ocultar Tabela de Histórico Financeiro", expanded=True):
        df_fin = st.session_state.df_historico_financeiro.copy()

        def estilizar_financeiro(val):
            return [
                'background-color: #FEF08A; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #00A3FF; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #4ADE80; color: #000000; font-weight: bold; text-align: center;'  
            ]

        df_fin_formated = df_fin.copy()
        df_fin_formated["Pipeline Total (R$)"] = df_fin_formated["Pipeline Total (R$)"].apply(lambda x: f"R$ {x:,.2f}")
        df_fin_formated["Receita Fechada (R$)"] = df_fin_formated["Receita Fechada (R$)"].apply(lambda x: f"R$ {x:,.2f}")

        df_fin_styled = df_fin_formated.style.apply(estilizar_financeiro, axis=1)
        st.dataframe(df_fin_styled, use_container_width=True, hide_index=True)

        st.caption("Adicionar ou remover meses da tabela financeira:")
        cf_1, cf_2, cf_3 = st.columns(3)
        with cf_1:
            novo_mes_fin = st.text_input("Mês/Ano", value="Mar/26", key="fin_mes")
        with cf_2:
            v_pipeline = st.number_input("Pipeline Total (R$)", min_value=0.0, value=450000.0, step=10000.0, key="fin_pip")
        with cf_3:
            v_receita = st.number_input("Receita Fechada (R$)", min_value=0.0, value=220000.0, step=10000.0, key="fin_rec")

        cf_b1, cf_b2 = st.columns([1.5, 4])
        with cf_b1:
            if st.button("Adicionar Mês (Financeiro)", use_container_width=True):
                nova_linha_fin = {
                    "Mês/Ano": novo_mes_fin,
                    "Pipeline Total (R$)": v_pipeline,
                    "Receita Fechada (R$)": v_receita
                }
                st.session_state.df_historico_financeiro = pd.concat([
                    st.session_state.df_historico_financeiro, 
                    pd.DataFrame([nova_linha_fin])
                ], ignore_index=True)
                st.rerun()
        with cf_b2:
            if st.button("Remover Último Mês (Financeiro)"):
                if len(st.session_state.df_historico_financeiro) > 1:
                    st.session_state.df_historico_financeiro = st.session_state.df_historico_financeiro.iloc[:-1]
                    st.rerun()

    if not st.session_state.df_historico_financeiro.empty:
        df_melted_fin = st.session_state.df_historico_financeiro.melt(
            id_vars=["Mês/Ano"], 
            value_vars=["Pipeline Total (R$)", "Receita Fechada (R$)"],
            var_name="Métrica", 
            value_name="Valor"
        )
        
        cores_fin = {
            "Pipeline Total (R$)": "#00A3FF",   
            "Receita Fechada (R$)": "#4ADE80"   
        }

        fig_linha_fin = px.line(
            df_melted_fin,
            x="Mês/Ano",
            y="Valor",
            color="Métrica",
            text="Valor",
            markers=True,
            title=f"Trajetória de Crescimento Financeiro (R$) — {COVEM_NAME}",
            color_discrete_map=cores_fin
        )
        
        fig_linha_fin.update_traces(
            texttemplate='R$ %{y:,.0f}',
            textposition="top center"
        )
        
        fig_linha_fin.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1E293B",
            plot_bgcolor="#1E293B",
            font=dict(color="#FFFFFF", size=13),
            xaxis_title="MÊS / ANO",
            yaxis_title="VALOR (R$)",
            height=440,
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_linha_fin, use_container_width=True)

# =========================================================
# ABA 5: ➕ NOVO CADASTRO
# =========================================================
with aba_novo:
    st.subheader("➕ Novo Cadastro Rápido")
    st.caption("Cadastre rapidamente uma nova empresa informando apenas os dados fundamentais.")

    with st.form("form_cadastro_rapido", clear_on_submit=True):
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            rapido_empresa = st.text_input("Nome da Empresa *")
            rapido_telefone = st.text_input("Telefone *")

        with col_r2:
            rapido_carteira = st.selectbox(
                "Carteira *", 
                CARTEIRAS_COVEM, 
                key="rapido_carteira"
            )
            rapido_etapa = st.selectbox(
                "Etapa da Venda *", 
                list(PROB_MAP.keys()), 
                key="rapido_etapa"
            )

        btn_salvar_rapido = st.form_submit_button("Cadastrar Rapidamente", use_container_width=True)

        if btn_salvar_rapido:
            if not rapido_empresa or not rapido_telefone:
                st.error("Por favor, preencha o Nome da Empresa e o Telefone.")
            else:
                novo_id = df["id"].max() + 1 if not df.empty else 1
                nova_linha_rapida = {
                    "id": novo_id,
                    "Empresa": rapido_empresa,
                    "Cliente": rapido_carteira,
                    "Etapa": rapido_etapa,
                    "Contato": "Não informado",
                    "Cargo": "Não informado",
                    "Telefone": rapido_telefone,
                    "Email": "Não informado",
                    "Cidade": "Não informado",
                    "Valor": 0.0,
                    "Prob": PROB_MAP[rapido_etapa],
                    "Vendedor": "Não informado",
                    "Perda": "",
                    "Data_Cadastro": str(date.today()),
                    "Followup_Data": str(date.today()),
                    "Followup_Nota": "Novo cadastro rápido efetuado.",
                    "Historico": f"Cadastro rápido realizado em {dt.now().strftime('%d/%m/%Y')}"
                }
                st.session_state.df_crm = pd.concat(
                    [st.session_state.df_crm, pd.DataFrame([nova_linha_rapida])], 
                    ignore_index=True
                )
                st.success(f"Empresa '{rapido_empresa}' cadastrada com sucesso via Cadastro Rápido!")
                st.rerun()

    st.write("---")

    st.subheader("Cadastrar Oportunidade Completa")
    
    with st.form("form_oportunidade", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            nova_empresa = st.text_input("Nome da Empresa / Cliente *")
            novo_cliente = st.selectbox("Marca / Carteira *", CARTEIRAS_COVEM)
            novo_contato = st.text_input("Contato / Nome")
            novo_cargo = st.text_input("Cargo")
            novo_telefone = st.text_input("Telefone de Contato *")
            novo_email = st.text_input("E-mail Comercial")
            
        with col_f2:
            nova_cidade = st.text_input("Cidade / Estado")
            novo_vendedor = st.text_input("Vendedor / Responsável")
            novo_valor = st.number_input("Valor da Oportunidade (R$)", min_value=0.0, step=1000.0, format="%.2f")
            nova_etapa = st.selectbox("Etapa Inicial *", list(PROB_MAP.keys()))
            motivo_perda = st.selectbox("Motivo de Perda (Se for '6. Perdido')", [""] + MOTIVOS_PERDA_PADRAO)
            
        st.divider()
        st.markdown("**Dados Iniciais de Follow-up:**")
        f_data_ini = st.date_input("Data do Primeiro Follow-up", value=date.today())
        f_nota_ini = st.text_input("Lembrete / Ação de Follow-up")

        btn_salvar = st.form_submit_button("Salvar Oportunidade Completa")
        
        if btn_salvar:
            if not nova_empresa:
                st.error("Preencha o Nome da Empresa.")
            else:
                novo_id = df["id"].max() + 1 if not df.empty else 1
                nova_linha = {
                    "id": novo_id,
                    "Empresa": nova_empresa,
                    "Cliente": novo_cliente,
                    "Etapa": nova_etapa,
                    "Contato": novo_contato if novo_contato else "Não informado",
                    "Cargo": novo_cargo if novo_cargo else "Não informado",
                    "Telefone": novo_telefone if novo_telefone else "Não informado",
                    "Email": novo_email if novo_email else "Não informado",
                    "Cidade": nova_cidade if nova_cidade else "Não informado",
                    "Valor": novo_valor,
                    "Prob": PROB_MAP[nova_etapa],
                    "Vendedor": novo_vendedor if novo_vendedor else "Não informado",
                    "Perda": motivo_perda if "Perdido" in nova_etapa else "",
                    "Data_Cadastro": str(date.today()),
                    "Followup_Data": str(f_data_ini) if f_nota_ini else "",
                    "Followup_Nota": f_nota_ini,
                    "Historico": f"Cadastrado em {dt.now().strftime('%d/%m/%Y')}"
                }
                st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha])], ignore_index=True)
                
                if nova_etapa == "6. Perdido" and motivo_perda in st.session_state.manual_perdas:
                    st.session_state.manual_perdas[motivo_perda] += 1
                
                st.success("Cadastrado com sucesso!")
                st.rerun()
