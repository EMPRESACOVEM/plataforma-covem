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

# Limite de dias padrão para considerar um lead estagnado (Vermelho)
DIAS_ESTAGNACAO_LIMITE = 10

# ---------------------------------------------------------
# PALETA COVEM & ESTILIZAÇÃO CSS
# ---------------------------------------------------------
DEFAULT_COLORS = {
    "1. Contatado": "#0284C7",         # Azul Claro
    "2. Conversando": "#CA8A04",        # Amarelo
    "3. Reunião Agendada": "#EA580C",  # Laranja
    "4. Proposta Enviada": "#0891B2",  # Ciano
    "5. Fechado": "#16A34A",           # Verde
    "6. Perdido": "#DC2626"            # Vermelho
}

CORES_PERDAS = {
    "Preço / Orçamento": "#FF0000",             # Vermelho
    "Concorrência": "#FF8C00",                  # Laranja
    "Sem Resposta / Sumiu": "#FFD700",          # Amarelo
    "Produto / Serviço não Atende": "#3B82F6",  # Azul
    "Outros": "#D1D5DB"                         # Cinza Claro
}

if 'funnel_colors' not in st.session_state:
    st.session_state.funnel_colors = DEFAULT_COLORS.copy()

st.markdown("""
    <style>
        .notranslate, [data-testid="stSidebar"], [data-baseweb="select"] {
            translate: no !important;
        }
        h1, h2, h3 {
            font-family: 'Inter', sans-serif !important;
            font-weight: 800 !important;
        }
        .bloco-detalhes-retangular {
            background-color: #0F172A;
            border: 2px solid #334155;
            border-radius: 10px;
            padding: 18px 22px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        }
        .phone-highlight {
            color: #38BDF8;
            font-weight: bold;
        }
        div[data-testid="stVerticalBlock"] > div {
            gap: 0.3rem !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 20px !important;
            font-weight: 700 !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 12px !important;
        }
        
        /* Estilização para o Kanban Inteligente */
        .kanban-card {
            background-color: #1E293B;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 12px;
            border-left: 5px solid #64748B;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .kanban-card-green {
            border-left: 6px solid #22C55E !important;
            background-color: #064E3B22;
        }
        .kanban-card-yellow {
            border-left: 6px solid #EAB308 !important;
            background-color: #713F1222;
        }
        .kanban-card-red {
            border-left: 6px solid #EF4444 !important;
            background-color: #7F1D1D22;
        }
        .kanban-tag {
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
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
            "Data_Cadastro": str(date.today() - timedelta(days=12)),
            "Data_Ultima_Movimentacao": str(date.today() - timedelta(days=2)),
            "Followup_Data": str(date.today() + timedelta(days=1)), 
            "Followup_Nota": "Enviar apresentação institucional atualizada.", 
            "Historico": "01/09: Primeiro contato realizado."
        },
        {
            "id": 2, "Empresa": "Sistemas Sigma", "Cliente": "QV Energia Solar", "Etapa": "1. Contatado", 
            "Contato": "Patricia Lima", "Cargo": "Gerente de Compras", "Telefone": "(16) 99765-4321", 
            "Email": "patricia@sigmasistemas.com.br", "Cidade": "Ribeirão Preto / SP", "Valor": 35000.0, 
            "Prob": 0.20, "Vendedor": "Lucas Mendes", "Perda": "",
            "Data_Cadastro": str(date.today() - timedelta(days=15)),
            "Data_Ultima_Movimentacao": str(date.today() - timedelta(days=12)),
            "Followup_Data": "", "Followup_Nota": "", 
            "Historico": "02/09: E-mail enviado."
        },
        {
            "id": 3, "Empresa": "Indústria Omega", "Cliente": "Elleven", "Etapa": "2. Conversando", 
            "Contato": "Fernando Souza", "Cargo": "Sócio-Proprietário", "Telefone": "(11) 98123-4567", 
            "Email": "fernando@omegaind.com.br", "Cidade": "São Paulo / SP", "Valor": 80000.0, 
            "Prob": 0.40, "Vendedor": "Gabriel Silva", "Perda": "",
            "Data_Cadastro": str(date.today() - timedelta(days=5)),
            "Data_Ultima_Movimentacao": str(date.today() - timedelta(days=1)),
            "Followup_Data": str(date.today()), "Followup_Nota": "Alinhar escopo do projeto técnico.", 
            "Historico": "30/08: Reunião inicial."
        },
        {
            "id": 4, "Empresa": "Tecnologia Beta", "Cliente": "BraClean", "Etapa": "6. Perdido", 
            "Contato": "Carlos Eduardo", "Cargo": "Comprador", "Telefone": "(16) 98888-7777", 
            "Email": "carlos@betatech.com", "Cidade": "Sertãozinho / SP", "Valor": 25000.0, 
            "Prob": 0.00, "Vendedor": "Lucas Mendes", "Perda": "Preço / Orçamento",
            "Data_Cadastro": str(date.today() - timedelta(days=20)),
            "Data_Ultima_Movimentacao": str(date.today() - timedelta(days=8)),
            "Followup_Data": "", "Followup_Nota": "", 
            "Historico": "25/08: Achou o valor acima do orçamento."
        }
    ])

if "Data_Ultima_Movimentacao" not in st.session_state.df_crm.columns:
    st.session_state.df_crm["Data_Ultima_Movimentacao"] = str(date.today())

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

if 'cliente_selecionado_id' not in st.session_state:
    st.session_state.cliente_selecionado_id = None

if 'modo_edicao' not in st.session_state:
    st.session_state.modo_edicao = False

if 'pending_stage_change' not in st.session_state:
    st.session_state.pending_stage_change = None

if 'manual_counts' not in st.session_state:
    st.session_state.manual_counts = {}

if 'manual_perdas' not in st.session_state:
    st.session_state.manual_perdas = None

df = st.session_state.df_crm

# ---------------------------------------------------------
# LÓGICA DO KANBAN INTELIGENTE (STATUS POR CORES)
# ---------------------------------------------------------
def calcular_status_kanban(row, df_tarefas):
    if row["Etapa"] in ["5. Fechado", "6. Perdido"]:
        return "GREEN", "Concluído", 0

    hoje = date.today()
    data_mov = row.get("Data_Ultima_Movimentacao", str(hoje))
    try:
        dt_mov = dt.strptime(str(data_mov), "%Y-%m-%d").date()
    except:
        dt_mov = hoje
    dias_na_etapa = (hoje - dt_mov).days

    empresa = row["Empresa"]
    tarefas_cliente = df_tarefas[(df_tarefas["Cliente"] == empresa) & (df_tarefas["Status"] != "Concluído")] if not df_tarefas.empty else pd.DataFrame()
    
    tem_followup_nota = bool(str(row.get("Followup_Nota", "")).strip())
    followup_data = row.get("Followup_Data", "")
    
    dt_followup = None
    if followup_data:
        try:
            dt_followup = dt.strptime(str(followup_data), "%Y-%m-%d").date()
        except:
            pass

    if dias_na_etapa >= DIAS_ESTAGNACAO_LIMITE:
        return "RED", f"Parado há {dias_na_etapa} dias", dias_na_etapa

    if dt_followup and dt_followup < hoje:
        return "RED", "Follow-up Atrasado!", dias_na_etapa

    if not tarefas_cliente.empty:
        for _, t in tarefas_cliente.iterrows():
            try:
                dt_venc = dt.strptime(str(t["Data_Vencimento"]), "%Y-%m-%d").date()
                if dt_venc < hoje:
                    return "RED", "Tarefa Atrasada!", dias_na_etapa
            except:
                pass

    if not tem_followup_nota and tarefas_cliente.empty:
        return "YELLOW", "Sem Próxima Ação", dias_na_etapa

    return "GREEN", "Em Dia", dias_na_etapa

# ---------------------------------------------------------
# CENTRAL DE ALERTAS OTIMIZADA E COMPACTA
# ---------------------------------------------------------
def exibir_alertas_tarefas(df_tarefas):
    if df_tarefas.empty or "Data_Vencimento" not in df_tarefas.columns:
        return

    hoje = datetime.date.today()
    df_temp = df_tarefas.copy()
    df_temp["Data_Vencimento"] = pd.to_datetime(
        df_temp["Data_Vencimento"], errors="coerce"
    ).dt.date

    pendentes = df_temp[df_temp["Status"] != "Concluído"]
    atrasadas = pendentes[pendentes["Data_Vencimento"] < hoje]
    hoje_tarefas = pendentes[pendentes["Data_Vencimento"] == hoje]

    if not atrasadas.empty or not hoje_tarefas.empty:
        c_status1, c_status2, c_detalhes, _ = st.columns([1.5, 1.5, 1.2, 3])

        with c_status1:
            if not atrasadas.empty:
                st.markdown(
                    f"<div style='background-color: #7F1D1D; color: #FECACA; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; text-align: center; border: 1px solid #EF4444;'>"
                    f"⚠️ {len(atrasadas)} Atrasada(s)</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<div style='background-color: #064E3B; color: #A7F3D0; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; text-align: center; border: 1px solid #10B981;'>"
                    "✅ Nenhuma Atrasada</div>",
                    unsafe_allow_html=True
                )

        with c_status2:
            if not hoje_tarefas.empty:
                st.markdown(
                    f"<div style='background-color: #1E3A8A; color: #BFDBFE; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; text-align: center; border: 1px solid #3B82F6;'>"
                    f"📅 {len(hoje_tarefas)} Para Hoje</div>",
                    unsafe_allow_html=True
                )

        with c_detalhes:
            with st.popover("🔔 Ver Detalhes", use_container_width=True):
                st.caption("**Resumo de Pendências Urgentíssimas**")
                if not atrasadas.empty:
                    st.markdown("🚨 **Atrasadas:**")
                    for _, row in atrasadas.iterrows():
                        st.write(f"• **{row['Titulo']}** ({row.get('Cliente', 'N/A')}) — *Venceu: {row['Data_Vencimento'].strftime('%d/%m')}*")
                if not hoje_tarefas.empty:
                    st.markdown("📅 **Hoje:**")
                    for _, row in hoje_tarefas.iterrows():
                        st.write(f"• **{row['Titulo']}** ({row.get('Cliente', 'N/A')})")

        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# BARRA LATERAL (FILTROS)
# ---------------------------------------------------------
st.sidebar.title("🎯 Filtros & Configurações")
opcoes_filtro = ["TODOS"] + CARTEIRAS_COVEM
cliente_sel = st.sidebar.selectbox("Filtrar por Carteira:", opcoes_filtro)

if cliente_sel != "TODOS":
    df_filtered = df[df["Cliente"] == cliente_sel]
    titulo_dinamico = f"CRM - {cliente_sel}"
else:
    df_filtered = df
    titulo_dinamico = COVEM_NAME

st.sidebar.divider()

with st.sidebar.expander("🎨 Personalizar Cores das Etapas", expanded=False):
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
    label="📊 Baixar Excel",
    data=buffer,
    file_name="crm_covem.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

# =========================================================
# 1. TÍTULO PRINCIPAL ABSOLUTO (NO TOPO)
# =========================================================
st.markdown(f'<div class="notranslate"><h1 style="margin:0; padding:0 0 10px 0;">{titulo_dinamico}</h1></div>', unsafe_allow_html=True)

# =========================================================
# 2. BARRA DE ALERTAS SLIM
# =========================================================
exibir_alertas_tarefas(st.session_state.df_tarefas)

# =========================================================
# 3. NAVEGAÇÃO PRINCIPAL (ABAS)
# =========================================================
aba_crm, aba_dash, aba_relatorio, aba_novo = st.tabs([
    "📌 CRM (Funil & Tarefas)", 
    "📊 DASHBOARD", 
    "📄 RELATÓRIO EXECUTIVO", 
    "➕ NOVO CADASTRO"
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
# ABA 1: GERENCIADOR DE TAREFAS SLIM + CRM KANBAN
# =========================================================
with aba_crm:
    c_tit, c_btn_add, c_btn_ver = st.columns([3, 1, 1])
    
    with c_tit:
        st.markdown("<h4 style='margin:0; padding:0;'>📌 Tarefas & Próximas Ações</h4>", unsafe_allow_html=True)
    
    with c_btn_add:
        with st.popover("➕ Nova Tarefa", use_container_width=True):
            lista_clientes = (
                ["Nenhum / Tarefa Geral"] + st.session_state.df_crm["Empresa"].dropna().tolist()
                if not st.session_state.df_crm.empty
                else ["Nenhum / Tarefa Geral"]
            )
            with st.form(key="form_nova_tarefa_popover", clear_on_submit=True):
                st.caption("Criar Tarefa / Lembrete")
                titulo_tarefa = st.text_input("Título *")
                descricao = st.text_area("Descrição / Observação", height=60)
                cliente_vinculado = st.selectbox("Cliente", options=lista_clientes)
                data_vencimento = st.date_input("Vencimento", min_value=datetime.date.today())
                prioridade = st.selectbox("Prioridade", options=["Baixa", "Média", "Alta", "Urgente"], index=1)
                
                if st.form_submit_button("Salvar Tarefa", use_container_width=True):
                    if titulo_tarefa:
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
                        st.success("Tarefa salva!")
                        st.rerun()

    with c_btn_ver:
        with st.popover("📋 Tabela Geral", use_container_width=True):
            st.caption("Lista Completa de Tarefas Cadastradas")
            if not st.session_state.df_tarefas.empty:
                st.dataframe(
                    st.session_state.df_tarefas[["Titulo", "Cliente", "Data_Vencimento", "Prioridade", "Status"]], 
                    use_container_width=True,
                    height=200
                )
            else:
                st.info("Nenhuma tarefa pendente.")

    st.markdown("<hr style='margin: 8px 0 16px 0;'/>", unsafe_allow_html=True)

    # MODAL DE TRANSITION DE ETAPA
    if st.session_state.pending_stage_change is not None:
        change_info = st.session_state.pending_stage_change
        c_id = change_info["id"]
        nova_et = change_info["nova_etapa"]
        
        idx_lead = st.session_state.df_crm.index[st.session_state.df_crm["id"] == c_id].tolist()[0]
        lead_data = st.session_state.df_crm.loc[idx_lead]

        st.warning(f"⚡ **Gatilho de Etapa:** Atualizando '{lead_data['Empresa']}' para **{nova_et}**")
        
        with st.form(key=f"modal_gatilho_{c_id}"):
            if nova_et == "4. Proposta Enviada":
                novo_val = st.number_input("Valor Final da Proposta (R$)", value=float(lead_data["Valor"]), step=1000.0)
                dt_prev = st.date_input("Data Prevista para Fechamento", value=date.today() + timedelta(days=15))
                nota_prop = st.text_input("Observação / Detalhes da Proposta", value="Proposta comercial enviada.")
                
            elif nova_et == "6. Perdido":
                motivo_p = st.selectbox("Motivo Principal da Perda *", MOTIVOS_PERDA_PADRAO)
                nota_prop = st.text_area("Justificativa do Feedback", placeholder="Detalhe o motivo da perda...")
                novo_val = 0.0
                
            else:
                nota_prop = st.text_input("Próximo Passo / Nota de Acompanhamento", value=f"Movido para {nova_et}")
                novo_val = float(lead_data["Valor"])
                dt_prev = None

            c_mod1, c_mod2 = st.columns(2)
            with c_mod1:
                btn_confirmar_gatilho = st.form_submit_button("✅ Confirmar Transição", use_container_width=True)
            with c_mod2:
                btn_cancelar_gatilho = st.form_submit_button("❌ Cancelar", use_container_width=True)

            if btn_confirmar_gatilho:
                st.session_state.df_crm.loc[idx_lead, "Etapa"] = nova_et
                st.session_state.df_crm.loc[idx_lead, "Prob"] = PROB_MAP[nova_et]
                st.session_state.df_crm.loc[idx_lead, "Data_Ultima_Movimentacao"] = str(date.today())
                st.session_state.df_crm.loc[idx_lead, "Valor"] = novo_val
                
                if nova_et == "6. Perdido":
                    st.session_state.df_crm.loc[idx_lead, "Perda"] = motivo_p
                
                if nota_prop:
                    st.session_state.df_crm.loc[idx_lead, "Followup_Nota"] = nota_prop
                    st.session_state.df_crm.loc[idx_lead, "Followup_Data"] = str(date.today())

                hist_ant = str(lead_data.get("Historico", ""))
                st.session_state.df_crm.loc[idx_lead, "Historico"] = f"{hist_ant}\n[{date.today().strftime('%d/%m')}] Movido para {nova_et}. {nota_prop}".strip()

                st.session_state.pending_stage_change = None
                st.success("Transição concluída!")
                st.rerun()

            if btn_cancelar_gatilho:
                st.session_state.pending_stage_change = None
                st.rerun()

    # FICHA DO CLIENTE SELECIONADO
    if st.session_state.cliente_selecionado_id is not None:
        cliente_dado = df[df["id"] == st.session_state.cliente_selecionado_id]
        
        if not cliente_dado.empty:
            c = cliente_dado.iloc[0]
            idx_cliente = st.session_state.df_crm.index[st.session_state.df_crm["id"] == c["id"]].tolist()[0]
            cliente_nome_atual = c['Empresa']
            
            col_titulo, col_acoes_top = st.columns([3, 2])
            with col_titulo:
                st.markdown(f"### 📄 Ficha do Cliente: **{cliente_nome_atual}**")
            with col_acoes_top:
                c_btn_ed, c_btn_cx = st.columns([2, 1])
                with c_btn_ed:
                    if not st.session_state.modo_edicao:
                        if st.button("✏️ Editar Dados", key="btn_ativar_edicao", use_container_width=True):
                            st.session_state.modo_edicao = True
                            st.rerun()
                    else:
                        if st.button("❌ Cancelar Edição", key="btn_cancelar_edicao", use_container_width=True):
                            st.session_state.modo_edicao = False
                            st.rerun()
                with c_btn_cx:
                    if st.button("✖ Fechar", help="Fechar ficha"):
                        st.session_state.cliente_selecionado_id = None
                        st.session_state.modo_edicao = False
                        st.rerun()

            with st.container():
                st.markdown('<div class="bloco-detalhes-retangular">', unsafe_allow_html=True)
                
                if not st.session_state.modo_edicao:
                    aba_historico_f, aba_tarefas_f, aba_perda_f = st.tabs(
                        ["📜 Histórico Geral", "📅 Tarefas Associadas", "❌ Registrar Perda"]
                    )

                    with aba_historico_f:
                        col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.2, 1.8])
                        with col1:
                            st.markdown(f"🏢 **Empresa:** {c['Empresa']}")
                            st.markdown(f"👤 **Contato:** {c['Contato']} ({c.get('Cargo', 'Não informado')})")
                        with col2:
                            st.markdown(f"📞 **Telefone:** <span class='phone-highlight'>{c.get('Telefone', 'Não informado')}</span>", unsafe_allow_html=True)
                            st.markdown(f"✉️ **E-mail:** {c.get('Email', 'Não informado')}")
                        with col3:
                            st.markdown(f'<div class="notranslate">💼 <b>Carteira:</b> {c["Cliente"]}</div>', unsafe_allow_html=True)
                            st.markdown(f"💰 **Valor:** R$ {c['Valor']:,.2f}")
                        with col4:
                            etapas_list = list(PROB_MAP.keys())
                            idx_etapa = etapas_list.index(c['Etapa']) if c['Etapa'] in etapas_list else 0
                            nova_etapa = st.selectbox("Etapa Atual:", options=etapas_list, index=idx_etapa, key=f"etapa_vis_{c['id']}")
                            if nova_etapa != c['Etapa']:
                                st.session_state.pending_stage_change = {"id": c['id'], "nova_etapa": nova_etapa}
                                st.rerun()

                        st.divider()
                        st.write("**Histórico de Interações:**")
                        st.info(c.get("Historico", "Nenhum histórico registrado."))

                        col_nota, col_dt_f = st.columns([2.5, 1.5])
                        with col_nota:
                            nova_nota = st.text_area("📝 Lembrete / Nota de Follow-up:", value=str(c.get("Followup_Nota", "")), height=70, key=f"nota_vis_{c['id']}")
                        with col_dt_f:
                            dt_val = date.today()
                            if c["Followup_Data"]:
                                try:
                                    dt_val = dt.strptime(str(c["Followup_Data"]), "%Y-%m-%d").date()
                                except:
                                    pass
                            nova_dt = st.date_input("Data do Follow-up:", value=dt_val, key=f"dt_vis_{c['id']}")
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("💾 Salvar Nota", key=f"salvar_nota_{c['id']}", use_container_width=True):
                                    st.session_state.df_crm.loc[idx_cliente, "Followup_Data"] = str(nova_dt)
                                    st.session_state.df_crm.loc[idx_cliente, "Followup_Nota"] = nova_nota
                                    st.success("Salvo!")
                                    st.rerun()
                            with b2:
                                if nova_nota.strip():
                                    link_gcal = criar_link_google_agenda(c["Empresa"], c["Contato"], nova_nota, str(nova_dt))
                                    st.markdown(f"[📅 Agenda]({link_gcal})")

                    with aba_tarefas_f:
                        st.subheader(f"Tarefas Agendadas para {cliente_nome_atual}")
                        if not st.session_state.df_tarefas.empty:
                            tarefas_cliente = st.session_state.df_tarefas[
                                st.session_state.df_tarefas["Cliente"] == cliente_nome_atual
                            ]
                            if not tarefas_cliente.empty:
                                st.dataframe(
                                    tarefas_cliente[["Titulo", "Data_Vencimento", "Prioridade", "Status"]],
                                    use_container_width=True,
                                )
                            else:
                                st.info("Não há tarefas específicas associadas a este cliente.")
                        else:
                            st.info("Nenhuma tarefa cadastrada na plataforma.")

                    with aba_perda_f:
                        st.subheader("Registrar Oportunidade Perdida")
                        with st.form(key=f"form_perda_{cliente_nome_atual}"):
                            motivo_perda = st.selectbox("Motivo Principal da Perda", options=MOTIVOS_PERDA_PADRAO)
                            obs_tecnica = st.text_area("Observação Técnica / Feedback do Cliente", placeholder="Detalhes...")
                            btn_salvar_perda = st.form_submit_button("Confirmar Perda do Negócio")

                            if btn_salvar_perda:
                                st.session_state.df_crm.loc[idx_cliente, "Etapa"] = "6. Perdido"
                                st.session_state.df_crm.loc[idx_cliente, "Prob"] = 0.00
                                st.session_state.df_crm.loc[idx_cliente, "Perda"] = motivo_perda
                                st.session_state.df_crm.loc[idx_cliente, "Data_Ultima_Movimentacao"] = str(date.today())
                                
                                historico_antigo = str(c.get("Historico", ""))
                                novo_hist = f"{historico_antigo}\n[{date.today().strftime('%d/%m/%Y')}] Perda registrada ({motivo_perda}): {obs_tecnica}".strip()
                                st.session_state.df_crm.loc[idx_cliente, "Historico"] = novo_hist
                                
                                st.error(f"Oportunidade de '{cliente_nome_atual}' marcada como PERDIDA.")
                                st.rerun()

                else:
                    st.markdown("#### ✏️ **Editar Informações do Cliente**")
                    with st.form(key=f"form_edicao_{c['id']}"):
                        e_col1, e_col2, e_col3 = st.columns(3)
                        
                        with e_col1:
                            edit_empresa = st.text_input("Nome da Empresa", value=c['Empresa'])
                            edit_contato = st.text_input("Contato", value=c['Contato'])
                            edit_cargo = st.text_input("Cargo", value=c.get('Cargo', ''))
                        
                        with e_col2:
                            edit_telefone = st.text_input("Telefone", value=c.get('Telefone', ''))
                            edit_email = st.text_input("E-mail", value=c.get('Email', ''))
                            edit_cidade = st.text_input("Cidade/UF", value=c.get('Cidade', ''))

                        with e_col3:
                            idx_cart = CARTEIRAS_COVEM.index(c['Cliente']) if c['Cliente'] in CARTEIRAS_COVEM else 0
                            edit_carteira = st.selectbox("Carteira", CARTEIRAS_COVEM, index=idx_cart)
                            edit_valor = st.number_input("Valor (R$)", value=float(c['Valor']), step=1000.0, format="%.2f")
                            edit_vendedor = st.text_input("Vendedor", value=c.get('Vendedor', ''))

                        st.divider()
                        btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)

                        if btn_salvar_edicao:
                            st.session_state.df_crm.loc[idx_cliente, "Empresa"] = edit_empresa
                            st.session_state.df_crm.loc[idx_cliente, "Contato"] = edit_contato
                            st.session_state.df_crm.loc[idx_cliente, "Cargo"] = edit_cargo
                            st.session_state.df_crm.loc[idx_cliente, "Telefone"] = edit_telefone
                            st.session_state.df_crm.loc[idx_cliente, "Email"] = edit_email
                            st.session_state.df_crm.loc[idx_cliente, "Cidade"] = edit_cidade
                            st.session_state.df_crm.loc[idx_cliente, "Cliente"] = edit_carteira
                            st.session_state.df_crm.loc[idx_cliente, "Valor"] = edit_valor
                            st.session_state.df_crm.loc[idx_cliente, "Vendedor"] = edit_vendedor
                            
                            st.session_state.modo_edicao = False
                            st.success("✅ Dados atualizados!")
                            st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()

    # KANBAN VISUAL
    st.caption("🟢 **Em dia** | 🟡 **Sem ação** | 🔴 **Atrasado/Parado**")
    
    etapas = list(PROB_MAP.keys())
    cols = st.columns(len(etapas))
    
    for idx, etapa in enumerate(etapas):
        cor_header = st.session_state.funnel_colors.get(etapa, "#3B82F6")
        
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
                status_cor, msg_status, dias_ret = calcular_status_kanban(row, st.session_state.df_tarefas)
                icon = "🟢" if status_cor == "GREEN" else ("🟡" if status_cor == "YELLOW" else "🔴")
                
                with st.container():
                    st.markdown(
                        f"""
                        <div class="kanban-card kanban-card-{status_cor.lower()}">
                            <div style="display:flex; justify-between; align-items:center;">
                                <span style="font-size:11px; color:#94A3B8;">{row['Cliente']}</span>
                                <span style="font-size:12px;">{icon}</span>
                            </div>
                            <strong style="font-size:14px; color:#F8FAFC;">{row['Empresa']}</strong><br/>
                            <span style="font-size:12px; color:#38BDF8; font-weight:bold;">R$ {row['Valor']:,.2f}</span>
                            <hr style="margin:4px 0; border-color:#334155;"/>
                            <div style="font-size:10px; color:#CBD5E1;">
                                ⏱️ {dias_ret}d nesta etapa<br/>
                                📌 <i>{msg_status}</i>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    c_btn_a, c_btn_b = st.columns([2, 1])
                    with c_btn_a:
                        if st.button("📄 Ficha", key=f"btn_card_{row['id']}", use_container_width=True):
                            st.session_state.cliente_selecionado_id = row['id']
                            st.session_state.modo_edicao = False
                            st.rerun()
                    with c_btn_b:
                        proximas_etapas = [e for e in etapas if e != etapa]
                        prox_et = st.selectbox(
                            "Mover", 
                            ["Mover..."] + proximas_etapas, 
                            key=f"move_quick_{row['id']}",
                            label_visibility="collapsed"
                        )
                        if prox_et != "Mover...":
                            st.session_state.pending_stage_change = {"id": row['id'], "nova_etapa": prox_et}
                            st.rerun()

# =========================================================
# ABA 2: DASHBOARD
# =========================================================
with aba_dash:
    st.markdown(f'<div class="notranslate"><h3>1. DISTRIBUIÇÃO DO FUNIL DE VENDAS ({COVEM_NAME})</h3></div>', unsafe_allow_html=True)
    
    col_f1, _ = st.columns([2, 2])
    with col_f1:
        periodo_sel = st.selectbox(
            "📅 Visualizar Período:", 
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
        cor_header = st.session_state.funnel_colors.get(etapa, "#3B82F6")
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

    with st.expander("✏️ Editar Números das Etapas Manualmente (Ajuste Rápido)"):
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
        
        if st.button("🔄 Resetar para Dados Reais do CRM"):
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

    with st.expander("📝 Tabela Editável: Ajustar Quantidade por Motivo de Perda", expanded=True):
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
            if st.button("🔄 Sincronizar com CRM", key="reset_perdas"):
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
# ABA 3: RELATÓRIO EXECUTIVO
# =========================================================
with aba_relatorio:
    st.title("📄 Relatório Executivo")
    st.caption("Acompanhamento histórico de atividades operacionais e evolução financeira.")

    st.subheader("1. Histórico de Evolução de Atividades & Prospecção")

    with st.expander("📋 Exibir / Ocultar Tabela de Histórico de Atividades", expanded=True):
        df_hist = st.session_state.df_historico_executivo.copy()

        def estilizar_atividades(val):
            return [
                'background-color: #FEF08A; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #38BDF8; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #FACC15; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #FB923C; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #4ADE80; color: #000000; font-weight: bold; text-align: center;'  
            ]

        df_styled = df_hist.style.apply(estilizar_atividades, axis=1)
        st.dataframe(df_styled, use_container_width=True, hide_index=True)

        st.caption("➕ Adicionar ou remover meses da tabela de atividades:")
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
            if st.button("➕ Adicionar Mês (Atividades)", use_container_width=True):
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
            if st.button("🗑️ Remover Último Mês (Atividades)"):
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
            "Leads Qualificados": "#38BDF8",   
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

    with st.expander("📋 Exibir / Ocultar Tabela de Histórico Financeiro", expanded=True):
        df_fin = st.session_state.df_historico_financeiro.copy()

        def estilizar_financeiro(val):
            return [
                'background-color: #FEF08A; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #FACC15; color: #000000; font-weight: bold; text-align: center;', 
                'background-color: #4ADE80; color: #000000; font-weight: bold; text-align: center;'  
            ]

        df_fin_formated = df_fin.copy()
        df_fin_formated["Pipeline Total (R$)"] = df_fin_formated["Pipeline Total (R$)"].apply(lambda x: f"R$ {x:,.2f}")
        df_fin_formated["Receita Fechada (R$)"] = df_fin_formated["Receita Fechada (R$)"].apply(lambda x: f"R$ {x:,.2f}")

        df_fin_styled = df_fin_formated.style.apply(estilizar_financeiro, axis=1)
        st.dataframe(df_fin_styled, use_container_width=True, hide_index=True)

        st.caption("➕ Adicionar ou remover meses da tabela financeira:")
        cf_1, cf_2, cf_3 = st.columns(3)
        with cf_1:
            novo_mes_fin = st.text_input("Mês/Ano", value="Mar/26", key="fin_mes")
        with cf_2:
            v_pipeline = st.number_input("Pipeline Total (R$)", min_value=0.0, value=450000.0, step=10000.0, key="fin_pip")
        with cf_3:
            v_receita = st.number_input("Receita Fechada (R$)", min_value=0.0, value=220000.0, step=10000.0, key="fin_rec")

        cf_b1, cf_b2 = st.columns([1.5, 4])
        with cf_b1:
            if st.button("➕ Adicionar Mês (Financeiro)", use_container_width=True):
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
            if st.button("🗑️ Remover Último Mês (Financeiro)"):
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
            "Pipeline Total (R$)": "#FACC15",   
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
# ABA 4: NOVO CADASTRO
# =========================================================
with aba_novo:
    st.subheader("⚡ Cadastro Rápido")
    st.caption("Cadastre rapidamente uma nova empresa informando apenas os dados fundamentais.")

    with st.form("form_cadastro_rapido", clear_on_submit=True):
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            rapido_empresa = st.text_input("Nome da Empresa *")
            rapido_telefone = st.text_input("Telefone *")

        with col_r2:
            rapido_carteira = st.selectbox("Carteira *", CARTEIRAS_COVEM, key="rapido_carteira")
            rapido_etapa = st.selectbox("Etapa da Venda *", list(PROB_MAP.keys()), key="rapido_etapa")

        btn_salvar_rapido = st.form_submit_button("⚡ Cadastrar Rapidamente", use_container_width=True)

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
                    "Data_Ultima_Movimentacao": str(date.today()),
                    "Followup_Data": "",
                    "Followup_Nota": "",
                    "Historico": f"Cadastro rápido realizado em {dt.now().strftime('%d/%m/%Y')}"
                }
                st.session_state.df_crm = pd.concat(
                    [st.session_state.df_crm, pd.DataFrame([nova_linha_rapida])], 
                    ignore_index=True
                )
                st.success(f"✅ Empresa '{rapido_empresa}' cadastrada com sucesso!")
                st.rerun()

    st.write("---")

    st.subheader("➕ Cadastrar Oportunidade Completa")
    
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
        st.markdown("**📅 Dados Iniciais de Follow-up:**")
        f_data_ini = st.date_input("Data do Primeiro Follow-up", value=date.today())
        f_nota_ini = st.text_input("Lembrete / Ação de Follow-up")

        btn_salvar = st.form_submit_button("💾 Salvar Oportunidade Completa")
        
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
                    "Data_Ultima_Movimentacao": str(date.today()),
                    "Followup_Data": str(f_data_ini) if f_nota_ini else "",
                    "Followup_Nota": f_nota_ini,
                    "Historico": f"Cadastrado em {dt.now().strftime('%d/%m/%Y')}"
                }
                st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha])], ignore_index=True)
                
                if nova_etapa == "6. Perdido" and motivo_perda in st.session_state.manual_perdas:
                    st.session_state.manual_perdas[motivo_perda] += 1
                
                st.success("✅ Cadastrado com sucesso!")
                st.rerun()
