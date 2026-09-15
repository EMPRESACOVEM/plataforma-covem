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
    layout="wide"
)

# Caminho do diretório base e arquivos de persistência local
BASE_DIR = Path(__file__).parent if "__file__" in locals() else Path.cwd()
ARQUIVO_DADOS = BASE_DIR / "banco_crm_covem.xlsx"
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
    "1. Contatado": "#F472B6",         # Rosa Pastel suave
    "2. Conversando": "#FDE047",        # Amarelo Pastel suave
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
            margin-bottom: 4px !important;
            border: 1px solid #334155 !important;
            background-color: #0F172A !important;
        }

        div[data-testid="stExpander"] details summary {
            padding-top: 6px !important;
            padding-bottom: 6px !important;
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
    "1. Contatado": 0.20,
    "2. Conversando": 0.40,
    "3. Reunião Agendada": 0.60,
    "4. Proposta Enviada": 0.80,
    "5. Fechado": 1.00,
    "6. Perdido": 0.00
}

MOTIVOS_PERDA_PADRAO = list(CORES_PERDAS.keys())

# ---------------------------------------------------------
# FUNÇÕES DE PERSISTÊNCIA
# ---------------------------------------------------------
def carregar_dados_crm():
    if ARQUIVO_DADOS.exists():
        try:
            df_loaded = pd.read_excel(ARQUIVO_DADOS)
            for col in ["id", "Empresa", "Cliente", "Etapa", "Contato", "Cargo", "Telefone", "Email", "Cidade", "Valor", "Prob", "Vendedor", "Perda", "Data_Cadastro", "Followup_Data", "Followup_Nota", "Historico"]:
                if col not in df_loaded.columns:
                    df_loaded[col] = ""
            return df_loaded
        except Exception:
            pass
            
    df_inicial = pd.DataFrame([
        {
            "id": 1, "Empresa": "Grupo Delta", "Cliente": "BraClean", "Etapa": "1. Contatado", 
            "Contato": "Roberto Alves", "Cargo": "Diretor Comercial", "Telefone": "(16) 99876-5432", 
            "Email": "roberto@grupodelta.com.br", "Cidade": "Sertãozinho / SP", "Valor": 50000.0, 
            "Prob": 0.20, "Vendedor": "Lucas Mendes", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today() - timedelta(days=2)), "Followup_Nota": "Enviar apresentação institucional atualizada.", 
            "Historico": "[01/09/2026 10:00] Primeiro contato realizado."
        },
        {
            "id": 2, "Empresa": "Sistemas Sigma", "Cliente": "QV Energia Solar", "Etapa": "1. Contatado", 
            "Contato": "Patricia Lima", "Cargo": "Gerente de Compras", "Telefone": "(16) 99765-4321", 
            "Email": "patricia@sigmasistemas.com.br", "Cidade": "Ribeirão Preto / SP", "Valor": 35000.0, 
            "Prob": 0.20, "Vendedor": "Lucas Mendes", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today()), "Followup_Nota": "Ligar para confirmar se recebeu o e-mail.", 
            "Historico": "[02/09/2026 14:30] E-mail enviado."
        },
        {
            "id": 3, "Empresa": "Indústria Omega", "Cliente": "Elleven", "Etapa": "2. Conversando", 
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
    df_inicial.to_excel(ARQUIVO_DADOS, index=False)
    return df_inicial

def salvar_dados_crm(df):
    df.to_excel(ARQUIVO_DADOS, index=False)

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
    titulo_dinamico = f"CRM — {cliente_sel}"
else:
    df_filtered = df
    titulo_dinamico = COVEM_NAME

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

# ---------------------------------------------------------
# NAVEGAÇÃO POR ABAS
# ---------------------------------------------------------
aba_tarefas, aba_crm, aba_dash, aba_relatorio, aba_novo = st.tabs([
    "Gerenciador de Tarefas",
    "Funil de Vendas", 
    "Dashboard", 
    "Relatório Executivo", 
    "+ Novo Cadastro"
])

# =========================================================
# ABA 1: GERENCIADOR DE TAREFAS & CALENDÁRIO FUTURO
# =========================================================
with aba_tarefas:
    exibir_agenda_semana(st.session_state.df_tarefas, st.session_state.df_crm)
    
    st.subheader("Gerenciador de Tarefas")

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

    st.markdown("#### Lista Geral de Tarefas")
    if not st.session_state.df_tarefas.empty:
        with st.container():
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                tarefas_opcoes = st.session_state.df_tarefas["Titulo"].tolist()
                tarefa_escolhida_exclusao = st.selectbox(
                    "Selecione a tarefa para excluir:", 
                    options=tarefas_opcoes, 
                    label_visibility="collapsed"
                )
            with col_btn:
                if st.button("Excluir Tarefa", use_container_width=True):
                    st.session_state.df_tarefas = st.session_state.df_tarefas[
                        st.session_state.df_tarefas["Titulo"] != tarefa_escolhida_exclusao
                    ].reset_index(drop=True)
                    salvar_dados_tarefas(st.session_state.df_tarefas)
                    st.success("Tarefa excluída com sucesso!")
                    st.rerun()

        st.dataframe(st.session_state.df_tarefas, use_container_width=True)
    else:
        st.info("Nenhuma tarefa pendente.")

    st.divider()

    st.subheader("Calendário de Tarefas e Follow-ups Futuros")
    st.caption("Visualize em formato de tabela cronológica todas as entregas, reuniões e interações planejadas para os próximos dias.")

    col_h1, col_h2 = st.columns([2, 2])
    with col_h1:
        horizonte = st.selectbox(
            "Horizonte de Visualização:",
            ["Próximos 7 Dias", "Próximos 15 Dias", "Próximos 30 Dias", "Todos os Registros Futuros"]
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

    if not st.session_state.df_tarefas.empty:
        for _, t in st.session_state.df_tarefas.iterrows():
            if pd.notna(t.get("Data_Vencimento")):
                try:
                    dt_v = dt.strptime(str(t["Data_Vencimento"])[:10], "%Y-%m-%d").date()
                    if hoje <= dt_v <= limite_data:
                        eventos_futuros.append({
                            "Data": dt_v,
                            "Tipo": "Tarefa",
                            "Título / Ação": t["Titulo"],
                            "Vinculado a": t.get("Cliente", "Geral"),
                            "Prioridade / Status": f"Prioridade: {t.get('Prioridade', 'Normal')}"
                        })
                except:
                    pass

    if not df_filtered.empty:
        for _, c in df_filtered.iterrows():
            f_dat = c.get("Followup_Data", "")
            if pd.notna(f_dat) and str(f_dat).strip() not in ["", "nan", "NaT"]:
                try:
                    dt_f = dt.strptime(str(f_dat)[:10], "%Y-%m-%d").date()
                    if hoje <= dt_f <= limite_data:
                        eventos_futuros.append({
                            "Data": dt_f,
                            "Tipo": "Follow-up CRM",
                            "Título / Ação": c.get("Followup_Nota", "Contato Comercial"),
                            "Vinculado a": f"Empresa: {c['Empresa']} ({c['Contato']})",
                            "Prioridade / Status": f"Etapa: {c['Etapa']}"
                        })
                except:
                    pass

    if eventos_futuros:
        df_futuro = pd.DataFrame(eventos_futuros)
        df_futuro = df_futuro.sort_values(by="Data", ascending=True)
        df_futuro["Data_Formatada"] = pd.to_datetime(df_futuro["Data"]).dt.strftime("%d/%m/%Y")

        with st.expander(f"Ver compromissos no período ({len(df_futuro)} encontrados)", expanded=False):
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric("Total de Ações no Período", len(df_futuro))
            c_m2.metric("Tarefas Pendentes", len(df_futuro[df_futuro["Tipo"] == "Tarefa"]))
            c_m3.metric("Follow-ups de CRM", len(df_futuro[df_futuro["Tipo"] == "Follow-up CRM"]))

            st.divider()

            st.dataframe(
                df_futuro[["Data_Formatada", "Tipo", "Título / Ação", "Vinculado a", "Prioridade / Status"]],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("Nenhuma tarefa ou follow-up agendado para este horizonte de tempo.")

# =========================================================
# ABA 2: FUNIL DE VENDAS
# =========================================================
with aba_crm:
    st.subheader(f"Funil de Vendas — {titulo_dinamico}")
    st.caption("Dica: Use o seletor em cada card para mover rapidamente o cliente de etapa, ou clique em EDITAR para abrir a ficha completa em destaque abaixo.")

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
                
                edit_perda = row_edit.get("Perda", "")
                edit_motivo_perda = st.selectbox(
                    "Motivo de Perda (Se aplicável)", 
                    options=[""] + MOTIVOS_PERDA_PADRAO,
                    index=(MOTIVOS_PERDA_PADRAO.index(edit_perda) + 1) if edit_perda in MOTIVOS_PERDA_PADRAO else 0
                )
                
                st.divider()
                st.markdown("**Adicionar Nota Rápida na Linha do Tempo:**")
                col_t1, col_t2 = st.columns([3, 1])
                with col_t1:
                    nova_nota_timeline = st.text_input("Escreva o que foi conversado / alinhado:", placeholder="Ex: Cliente pediu para retornar na próxima terça para fechar o contrato.")
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
                    
                idx_df = st.session_state.df_crm[st.session_state.df_crm["id"] == cliente_edit_id].index
                
                if adicionar_timeline_btn and nova_nota_timeline.strip():
                    timestamp_atual = dt.now().strftime("%d/%m/%Y %H:%M")
                    novo_registro_timeline = f"[{timestamp_atual}] {nova_nota_timeline.strip()}"
                    
                    if historico_atual.strip():
                        historico_atualizado = novo_registro_timeline + "\n" + historico_atual
                    else:
                        historico_atualizado = novo_registro_timeline
                        
                    st.session_state.df_crm.loc[idx_df, "Historico"] = historico_atualizado
                    salvar_dados_crm(st.session_state.df_crm)
                    st.success("Nota adicionada na linha do tempo com sucesso!")
                    st.rerun()

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
                    st.session_state.df_crm.loc[idx_df, "Perda"] = edit_motivo_perda
                    
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

    etapas = list(PROB_MAP.keys())
    cols = st.columns(len(etapas))
    
    for idx, etapa in enumerate(etapas):
        cor_header = st.session_state.funnel_colors.get(etapa, "#3B82F6")
        
        with cols[idx]:
            # Cabeçalho da etapa
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #334155; border-top: 4px solid {cor_header}; padding: 8px; border-radius: 6px; text-align: center; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
                    <b style="color: #F8FAFC; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">{etapa}</b>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            sub_df = df_filtered[df_filtered["Etapa"] == etapa]
            
            for _, row in sub_df.iterrows():
                st_code, st_label, st_icon = calcular_status_followup(row.get("Followup_Data", ""))
                cliente_id = row['id']
                
                # Card do cliente com bordinha lateral da cor da etapa e fundo levemente tingido com a cor da etapa
                st.markdown(f"""
                    <div style="border-left: 4px solid {cor_header}; background-color: #111C31; border-top: 1px solid #1E293B; border-right: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-radius: 4px; margin-bottom: 6px; padding: 2px;">
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
                            <span style="font-size: 12px; color: #94A3B8;">Contato: {row['Contato']}</span><br>
                            <span class="phone-highlight" style="font-size: 12px;">{row.get('Telefone', 'Não informado')}</span><br>
                            <hr style="margin: 6px 0; border-color: #334155;">
                            <span style="font-size: 12px; color: #E2E8F0;"><b>Follow-up:</b> {st_icon} {dt_f_str}</span>
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
                        if nova_etapa_card == "6. Perdido":
                            st.session_state.df_crm.loc[idx_df, "Perda"] = "Outros"
                        
                        salvar_dados_crm(st.session_state.df_crm)
                        st.success(f"Movido para {nova_etapa_card}!")
                        st.rerun()

                    st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
                    if st.button("EDITAR", key=f"btn_edit_{cliente_id}", use_container_width=True):
                        st.session_state.cliente_editando_id = cliente_id
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# ABA 3: DASHBOARD
# =========================================================
with aba_dash:
    st.markdown(f'<div class="notranslate"><h3>1. DISTRIBUIÇÃO DO FUNIL DE VENDAS ({titulo_dinamico})</h3></div>', unsafe_allow_html=True)
    
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
        contagem_calculada[etapa] = count_real
        
    total_leads = sum(contagem_calculada.values())
    cols_m = st.columns(len(etapas_crm) + 1)
    
    for i, etapa in enumerate(etapas_crm):
        cor_header = st.session_state.funnel_colors.get(etapa, "#3B82F6")
        qtd = contagem_calculada[etapa]
        
        with cols_m[i]:
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #334155; border-top: 4px solid {cor_header}; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <b style="color: #F8FAFC; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">{etapa}</b>
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.metric(label="", value=qtd)

    with cols_m[-1]:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #334155; border-top: 4px solid #FFFFFF; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <b style="color: #F8FAFC; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">TOTAL</b>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.metric(label="", value=total_leads)

    st.divider()

    st.markdown(f'<div class="notranslate"><h3>Funil de Vendas — {titulo_dinamico}</h3></div>', unsafe_allow_html=True)
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

    st.markdown(f'<div class="notranslate"><h3>Motivos de Perda de Vendas — {titulo_dinamico}</h3></div>', unsafe_allow_html=True)
    df_perdidos = df_dash[df_dash["Etapa"] == "6. Perdido"]
    
    if not df_perdidos.empty and "Perda" in df_perdidos.columns:
        df_motivos = df_perdidos[df_perdidos["Perda"].str.strip() != ""].groupby("Perda").size().reset_index(name="Quantidade")
        if not df_motivos.empty:
            fig_perda = px.pie(
                df_motivos,
                values="Quantidade",
                names="Perda",
                color="Perda",
                color_discrete_map=CORES_PERDAS,
                hole=0.4
            )
            fig_perda.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1E293B",
                plot_bgcolor="#1E293B",
                font=dict(color="#FFFFFF", size=13),
                height=380
            )
            fig_perda.update_traces(textinfo="percent+value")
            st.plotly_chart(fig_perda, use_container_width=True)
        else:
            st.info("Nenhum motivo de perda especificado para os leads perdidos.")
    else:
        st.info("Nenhum lead registrado na etapa '6. Perdido' no momento.")

# =========================================================
# ABA 4: RELATÓRIO EXECUTIVO
# =========================================================
with aba_relatorio:
    st.title("Relatório Executivo")
    st.caption("Acompanhamento histórico de atividades operacionais e evolução financeira.")

    st.subheader("Historico de Atividades")

    df_historico_salvo = carregar_dados_historico()
    df_crm_base = df_filtered.copy()

    mes_atual_str = dt.now().strftime("%b/%y").capitalize()
    meses_map = {"Jan": "Jan", "Feb": "Fev", "Mar": "Mar", "Apr": "Abr", "May": "Mai", "Jun": "Jun", "Jul": "Jul", "Aug": "Ago", "Sep": "Set", "Oct": "Out", "Nov": "Nov", "Dec": "Dez"}
    for eng, pt in meses_map.items():
        mes_atual_str = mes_atual_str.replace(eng, pt)

    if not df_crm_base.empty and "Data_Cadastro" in df_crm_base.columns:
        df_crm_base["Data_Datetime"] = pd.to_datetime(df_crm_base["Data_Cadastro"], errors="coerce")
        df_crm_base["Mês/Ano"] = df_crm_base["Data_Datetime"].dt.strftime("%b/%y").str.capitalize()
        for eng, pt in meses_map.items():
            df_crm_base["Mês/Ano"] = df_crm_base["Mês/Ano"].str.replace(eng, pt, regex=False)

        sub_m = df_crm_base[df_crm_base["Mês/Ano"] == mes_atual_str]
        
        leads_q = len(sub_m[sub_m["Etapa"].isin(["1. Contatado", "2. Conversando", "3. Reunião Agendada", "4. Proposta Enviada", "5. Fechado"])])
        reunioes = len(sub_m[sub_m["Etapa"] == "3. Reunião Agendada"])
        propostas = len(sub_m[sub_m["Etapa"] == "4. Proposta Enviada"])
        fechados = len(sub_m[sub_m["Etapa"] == "5. Fechado"])

        if df_historico_salvo.empty:
            df_historico_salvo = pd.DataFrame([{
                "Mês/Ano": mes_atual_str,
                "Leads Qualificados": leads_q,
                "Reuniões Agendadas": reunioes,
                "Propostas Enviadas": propostas,
                "Projetos Fechados": fechados
            }])
        else:
            if mes_atual_str in df_historico_salvo["Mês/Ano"].values:
                idx = df_historico_salvo[df_historico_salvo["Mês/Ano"] == mes_atual_str].index[0]
                df_historico_salvo.loc[idx, "Leads Qualificados"] = leads_q
                df_historico_salvo.loc[idx, "Reuniões Agendadas"] = reunioes
                df_historico_salvo.loc[idx, "Propostas Enviadas"] = propostas
                df_historico_salvo.loc[idx, "Projetos Fechados"] = fechados
            else:
                nova_linha_hist = pd.DataFrame([{
                    "Mês/Ano": mes_atual_str,
                    "Leads Qualificados": leads_q,
                    "Reuniões Agendadas": reunioes,
                    "Propostas Enviadas": propostas,
                    "Projetos Fechados": fechados
                }])
                df_historico_salvo = pd.concat([df_historico_salvo, nova_linha_hist], ignore_index=True)
        
        salvar_dados_historico(df_historico_salvo)

    with st.expander("Exibir / Ocultar Tabela de Histórico de Atividades", expanded=True):
        if not df_historico_salvo.empty:
            def colorir_tabela_historico(val, col_name):
                if col_name == "Mês/Ano":
                    return "background-color: #FDE047; color: #1E293B; font-weight: bold;"
                elif col_name == "Leads Qualificados":
                    return "background-color: #F472B6; color: #1E293B; font-weight: bold;"
                elif col_name == "Reuniões Agendadas":
                    return "background-color: #FDBA74; color: #1E293B; font-weight: bold;"
                elif col_name == "Propostas Enviadas":
                    return "background-color: #93C5FD; color: #1E293B; font-weight: bold;"
                elif col_name == "Projetos Fechados":
                    return "background-color: #86EFAC; color: #1E293B; font-weight: bold;"
                return ""

            df_estilizado = df_historico_salvo.style.apply(lambda col: [colorir_tabela_historico(v, col.name) for v in col], axis=0)
            st.dataframe(df_estilizado, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado cadastrado para gerar o histórico de atividades.")

    if not df_historico_salvo.empty:
        df_melted_atv = df_historico_salvo.melt(
            id_vars=["Mês/Ano"], 
            value_vars=["Leads Qualificados", "Reuniões Agendadas", "Propostas Enviadas", "Projetos Fechados"],
            var_name="Métrica", 
            value_name="Quantidade"
        )
        
        cores_atv = {
            "Leads Qualificados": "#F472B6",   
            "Reuniões Agendadas": "#FDBA74",   
            "Propostas Enviadas": "#93C5FD",   
            "Projetos Fechados": "#86EFAC"    
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

    st.subheader("Historico Financeiro")

    df_financeiro_salvo = carregar_dados_financeiro()

    if not df_crm_base.empty and "Data_Cadastro" in df_crm_base.columns:
        sub_m_prop = df_crm_base[(df_crm_base["Mês/Ano"] == mes_atual_str) & (df_crm_base["Etapa"] == "4. Proposta Enviada")]
        sub_m_fech = df_crm_base[(df_crm_base["Mês/Ano"] == mes_atual_str) & (df_crm_base["Etapa"] == "5. Fechado")]

        val_prop = float(sub_m_prop["Valor"].sum()) if not sub_m_prop.empty else 0.0
        qtd_prop = int(len(sub_m_prop))

        val_fech = float(sub_m_fech["Valor"].sum()) if not sub_m_fech.empty else 0.0
        qtd_fech = int(len(sub_m_fech))

        total_mes = val_prop + val_fech

        str_prop_fmt = f"R$ {val_prop:,.2f} ({qtd_prop} un)".replace(",", "X").replace(".", ",").replace("X", ".")
        str_fech_fmt = f"R$ {val_fech:,.2f} ({qtd_fech} un)".replace(",", "X").replace(".", ",").replace("X", ".")
        str_total_fmt = f"R$ {total_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        if df_financeiro_salvo.empty:
            df_financeiro_salvo = pd.DataFrame([{
                "Mês/Ano": mes_atual_str,
                "Propostas Enviadas": str_prop_fmt,
                "Projetos Fechados": str_fech_fmt,
                "Total": str_total_fmt
            }])
        else:
            if mes_atual_str in df_financeiro_salvo["Mês/Ano"].values:
                idx = df_financeiro_salvo[df_financeiro_salvo["Mês/Ano"] == mes_atual_str].index[0]
                df_financeiro_salvo.loc[idx, "Propostas Enviadas"] = str_prop_fmt
                df_financeiro_salvo.loc[idx, "Projetos Fechados"] = str_fech_fmt
                df_financeiro_salvo.loc[idx, "Total"] = str_total_fmt
            else:
                nova_linha_fin = pd.DataFrame([{
                    "Mês/Ano": mes_atual_str,
                    "Propostas Enviadas": str_prop_fmt,
                    "Projetos Fechados": str_fech_fmt,
                    "Total": str_total_fmt
                }])
                df_financeiro_salvo = pd.concat([df_financeiro_salvo, nova_linha_fin], ignore_index=True)

        salvar_dados_financeiro(df_financeiro_salvo)

    with st.expander("Exibir / Ocultar Tabela de Histórico Financeiro", expanded=True):
        if not df_financeiro_salvo.empty:
            def colorir_tabela_financeiro(val, col_name):
                if col_name == "Mês/Ano":
                    return "background-color: #FDE047; color: #1E293B; font-weight: bold;"
                elif col_name == "Propostas Enviadas":
                    return "background-color: #93C5FD; color: #1E293B; font-weight: bold;"
                elif col_name == "Projetos Fechados":
                    return "background-color: #86EFAC; color: #1E293B; font-weight: bold;"
                elif col_name == "Total":
                    return "background-color: #F1F5F9; color: #1E293B; font-weight: bold;"
                return ""

            df_fin_estilizado = df_financeiro_salvo.style.apply(lambda col: [colorir_tabela_financeiro(v, col.name) for v in col], axis=0)
            st.dataframe(df_fin_estilizado, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado cadastrado para gerar o histórico financeiro.")

    if not df_crm_base.empty and "Data_Cadastro" in df_crm_base.columns:
        df_graf_fin = df_crm_base[df_crm_base["Etapa"].isin(["4. Proposta Enviada", "5. Fechado"])].copy()
        if not df_graf_fin.empty:
            df_graf_fin["Tipo"] = df_graf_fin["Etapa"].apply(lambda x: "Propostas Enviadas" if "Proposta" in x else "Projetos Fechados")
            df_agrupado_fin = df_graf_fin.groupby(["Mês/Ano", "Tipo"])["Valor"].sum().reset_index()

            cores_fin_graf = {
                "Propostas Enviadas": "#93C5FD",
                "Projetos Fechados": "#86EFAC"
            }

            fig_linha_fin = px.line(
                df_agrupado_fin,
                x="Mês/Ano",
                y="Valor",
                color="Tipo",
                text="Valor",
                markers=True,
                title=f"Evolução Financeira Mensal (R$) — {COVEM_NAME}",
                color_discrete_map=cores_fin_graf
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
            fig_linha_fin.update_traces(texttemplate='R$ %{text:,.2f}', textposition="top center")
            st.plotly_chart(fig_linha_fin, use_container_width=True)
        else:
            st.info("Nenhum valor em propostas ou projetos fechados para exibir no gráfico financeiro.")

# =========================================================
# ABA 5: + NOVO CADASTRO
# =========================================================
with aba_novo:
    st.subheader("+ Novo Cadastro Rápido")
    st.caption("Cadastre rapidamente uma nova empresa informando apenas os dados fundamentais.")

    with st.form("form_cadastro_rapido", clear_on_submit=True):
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            rapido_empresa = st.text_input("Nome da Empresa *")
            rapido_telefone = st.text_input("Telefone *")

        with col_r2:
            rapido_carteira = st.selectbox("Carteira *", CARTEIRAS_COVEM, key="rapido_carteira")
            rapido_etapa = st.selectbox("Etapa da Venda *", list(PROB_MAP.keys()), key="rapido_etapa")

        btn_salvar_rapido = st.form_submit_button("Cadastrar Rapidamente", use_container_width=True)

        if btn_salvar_rapido:
            if not rapido_empresa or not rapido_telefone:
                st.error("Por favor, preencha o Nome da Empresa e o Telefone.")
            else:
                novo_id = int(df["id"].max() + 1) if not df.empty and pd.notna(df["id"].max()) else 1
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
                    "Historico": f"[{dt.now().strftime('%d/%m/%Y %H:%M')}] Cadastro rápido realizado."
                }
                st.session_state.df_crm = pd.concat(
                    [st.session_state.df_crm, pd.DataFrame([nova_linha_rapida])], 
                    ignore_index=True
                )
                salvar_dados_crm(st.session_state.df_crm)
                st.success(f"Empresa '{rapido_empresa}' cadastrada e salva com sucesso!")
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
            nova_email = st.text_input("E-mail Comercial")
            
        with col_f2:
            nova_cidade = st.text_input("Cidade / Estado")
            novo_vendedor = st.text_input("Vendedor / Responsável")
            nova_valor = st.number_input("Valor da Oportunidade (R$)", min_value=0.0, step=1000.0, format="%.2f")
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
                novo_id = int(df["id"].max() + 1) if not df.empty and pd.notna(df["id"].max()) else 1
                nova_linha = {
                    "id": novo_id,
                    "Empresa": nova_empresa,
                    "Cliente": novo_cliente,
                    "Etapa": nova_etapa,
                    "Contato": nova_contato if nova_contato else "Não informado",
                    "Cargo": novo_cargo if novo_cargo else "Não informado",
                    "Telefone": nova_telefone if nova_telefone else "Não informado",
                    "Email": nova_email if nova_email else "Não informado",
                    "Cidade": nova_cidade if nova_cidade else "Não informado",
                    "Valor": nova_valor,
                    "Prob": PROB_MAP[nova_etapa],
                    "Vendedor": novo_vendedor if novo_vendedor else "Não informado",
                    "Perda": motivo_perda if "Perdido" in nova_etapa else "",
                    "Data_Cadastro": str(date.today()),
                    "Followup_Data": str(f_data_ini) if f_nota_ini else "",
                    "Followup_Nota": f_nota_ini,
                    "Historico": f"[{dt.now().strftime('%d/%m/%Y %H:%M')}] Oportunidade cadastrada."
                }
                st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha])], ignore_index=True)
                salvar_dados_crm(st.session_state.df_crm)
                st.success("Oportunidade cadastrada e salva com sucesso!")
                st.rerun()
