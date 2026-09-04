import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import urllib.parse
from datetime import datetime, date, timedelta
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Plataforma Executiva COVEM",
    page_icon="🏢",
    layout="wide"
)

# Caminho do diretório base
BASE_DIR = Path(__file__).parent if "__file__" in locals() else Path.cwd()

# Proteção contra tradução automática (Zero-Width Space)
COVEM_NAME = "C\u200Bo\u200Bv\u200Be\u200Bm"

# Lista oficial das carteiras do grupo COVEM
CARTEIRAS_OFICIAIS = ["BraClean", "QV Energia Solar", "Elleven"]

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
        /* Desativa estritamente a tradução automática */
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
# ESTADO DA SESSÃO (CRM, PERDAS, HISTÓRICO ATIVIDADES E FINANCEIRO)
# ---------------------------------------------------------
if 'df_crm' not in st.session_state:
    st.session_state.df_crm = pd.DataFrame([
        {
            "id": 1, "Empresa": "Grupo Delta", "Cliente": "BraClean", "Etapa": "1. Contatado", 
            "Contato": "Roberto Alves", "Cargo": "Diretor Comercial", "Telefone": "(16) 99876-5432", 
            "Email": "roberto@grupodelta.com.br", "Cidade": "Sertãozinho / SP", "Valor": 50000.0, 
            "Prob": 0.20, "Vendedor": "Lucas Mendes", "Perda": "",
            "Data_Cadastro": str(date.today()),
            "Followup_Data": str(date.today()), "Followup_Nota": "Enviar apresentação institucional atualizada.", 
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
            "Followup_Data": str(date.today()), "Followup_Nota": "Alinhar escopo do projeto técnico.", 
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

if 'manual_counts' not in st.session_state:
    st.session_state.manual_counts = {}

if 'manual_perdas' not in st.session_state:
    st.session_state.manual_perdas = None

df = st.session_state.df_crm

# ---------------------------------------------------------
# BARRA LATERAL (FILTROS E CONFIGURAÇÕES)
# ---------------------------------------------------------
st.sidebar.title("🎯 Filtros & Configurações")

# Opções fixas de filtragem por carteira
opcoes_filtro = [f"{COVEM_NAME} (Consolidado)"] + CARTEIRAS_OFICIAIS

cliente_sel = st.sidebar.selectbox("Filtrar por Carteira:", opcoes_filtro)

if cliente_sel != f"{COVEM_NAME} (Consolidado)":
    df_filtered = df[df["Cliente"] == cliente_sel]
    titulo_dinamico = f"CRM {cliente_sel}"
else:
    df_filtered = df
    titulo_dinamico = f"CRM - Grupo {COVEM_NAME}"

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

# ---------------------------------------------------------
# CABEÇALHO SIMPLIFICADO
# ---------------------------------------------------------
st.markdown(f'<div class="notranslate"><h1 style="margin:0; padding:0;">{titulo_dinamico}</h1></div>', unsafe_allow_html=True)
st.divider()

# ---------------------------------------------------------
# NAVEGAÇÃO POR ABAS
# ---------------------------------------------------------
aba_crm, aba_dash, aba_relatorio, aba_novo = st.tabs([
    "📌 CRM (Funil)", 
    "📊 DASHBOARD", 
    "📄 RELATÓRIO EXECUTIVO", 
    "➕ NOVO CADASTRO"
])

def criar_link_google_agenda(empresa, contato, nota_followup, data_str):
    if not data_str:
        return "#"
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        dt_formatada = dt.strftime("%Y%m%dT090000Z/%Y%m%dT100000Z")
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
# ABA 1: CRM (MINIMALISTA)
# =========================================================
with aba_crm:
    st.subheader("Gestão Visual do Funil de Vendas")
    
    if st.session_state.cliente_selecionado_id is not None:
        cliente_dado = df[df["id"] == st.session_state.cliente_selecionado_id]
        
        if not cliente_dado.empty:
            c = cliente_dado.iloc[0]
            idx_cliente = st.session_state.df_crm.index[st.session_state.df_crm["id"] == c["id"]].tolist()[0]
            
            col_titulo, col_acoes_top = st.columns([3, 2])
            with col_titulo:
                st.markdown(f"### 📋 Ficha do Cliente: **{c['Empresa']}**")
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
                            st.session_state.df_crm.loc[idx_cliente, "Etapa"] = nova_etapa
                            st.session_state.df_crm.loc[idx_cliente, "Prob"] = PROB_MAP[nova_etapa]
                            st.rerun()

                    st.divider()

                    col_nota, col_dt_f = st.columns([2.5, 1.5])
                    with col_nota:
                        nova_nota = st.text_area("📝 Lembrete / Nota de Follow-up:", value=str(c.get("Followup_Nota", "")), height=70, key=f"nota_vis_{c['id']}")
                    
                    with col_dt_f:
                        dt_val = date.today()
                        if c["Followup_Data"]:
                            try:
                                dt_val = datetime.strptime(str(c["Followup_Data"]), "%Y-%m-%d").date()
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

                else:
                    st.markdown("#### ✏️ **Editar Informações do Cliente**")
                    with st.form(key=f"form_edicao_{c['id']}"):
                        e_col1, e_col2, e_col3 = st.columns(3)
                        
                        with e_col1:
                            edit_empresa = st.text_input("Nome da Empresa", value=c['Empresa'])
                            edit_contato = st.text_input("Nome do Funcionário / Contato", value=c['Contato'])
                            edit_cargo = st.text_input("Cargo", value=c.get('Cargo', ''))
                        
                        with e_col2:
                            edit_telefone = st.text_input("Telefone / WhatsApp", value=c.get('Telefone', ''))
                            edit_email = st.text_input("E-mail Comercial", value=c.get('Email', ''))
                            edit_cidade = st.text_input("Cidade / Estado", value=c.get('Cidade', ''))

                        with e_col3:
                            carteiras_edicao = CARTEIRAS_OFICIAIS
                            idx_cart = carteiras_edicao.index(c['Cliente']) if c['Cliente'] in carteiras_edicao else 0
                            edit_carteira = st.selectbox("Carteira", carteiras_edicao, index=idx_cart)
                            edit_valor = st.number_input("Valor (R$)", value=float(c['Valor']), step=1000.0, format="%.2f")
                            edit_vendedor = st.text_input("Vendedor / Responsável", value=c.get('Vendedor', ''))

                        st.divider()
                        btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações e Atualizar CRM", use_container_width=True)

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
                            st.success("✅ Dados atualizados com sucesso!")
                            st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)
                st.divider()

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
                tem_followup = bool(str(row.get("Followup_Nota", "")).strip())
                status_tag = "🔴 Follow-up" if tem_followup else "⚪ Sem Ação"
                btn_label = f"🏢 {row['Empresa']}\n({status_tag})"
                
                if st.button(btn_label, key=f"btn_card_{row['id']}", use_container_width=True):
                    st.session_state.cliente_selecionado_id = row['id']
                    st.session_state.modo_edicao = False
                    st.rerun()

# =========================================================
# ABA 2: DASHBOARD
# =========================================================
with aba_dash:
    nome_exibicao_dash = cliente_sel if cliente_sel != f"{COVEM_NAME} (Consolidado)" else COVEM_NAME
    st.markdown(f'<div class="notranslate"><h3>1. DISTRIBUIÇÃO DO FUNIL DE VENDAS ({nome_exibicao_dash})</h3></div>', unsafe_allow_html=True)
    
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

    st.markdown(f'<div class="notranslate"><h3>Funil de Vendas — {nome_exibicao_dash}</h3></div>', unsafe_allow_html=True)
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
            title=f"Motivos de Perda — {nome_exibicao_dash} (Total: {total_perdas_num})",
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
            title=f"Evolução Mensal de Atividades & Prospecção — {nome_exibicao_dash}",
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
            title=f"Trajetória de Crescimento Financeiro (R$) — {nome_exibicao_dash}",
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
# ABA 4: NOVO CADASTRO E ADIÇÃO RÁPIDA DE CLIENTES
# =========================================================
with aba_novo:
    st.subheader("⚡ Adição Rápida de Novo Cliente")
    
    # BARRA DE ADIÇÃO RÁPIDA
    col_add1, col_add2, col_add3 = st.columns([3, 1.5, 1])
    with col_add1:
        novo_nome_rapido = st.text_input("Nome da Empresa / Futuro Cliente", placeholder="Ex: Indústria Metalúrgica Sertãozinho", key="input_rapido_nome")
    with col_add2:
        nova_marca_rapida = st.selectbox("Marca / Carteira", CARTEIRAS_OFICIAIS, key="input_rapido_carteira")
    with col_add3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_add_rapido = st.button("➕ Adicionar Cliente", use_container_width=True)

    if btn_add_rapido:
        if novo_nome_rapido.strip():
            novo_id_rapido = df["id"].max() + 1 if not df.empty else 1
            nova_linha_rapida = {
                "id": novo_id_rapido,
                "Empresa": novo_nome_rapido.strip(),
                "Cliente": nova_marca_rapida,
                "Etapa": "1. Contatado",
                "Contato": "Não informado",
                "Cargo": "Não informado",
                "Telefone": "Não informado",
                "Email": "Não informado",
                "Cidade": "Não informado",
                "Valor": 0.0,
                "Prob": PROB_MAP["1. Contatado"],
                "Vendedor": "Não informado",
                "Perda": "",
                "Data_Cadastro": str(date.today()),
                "Followup_Data": str(date.today()),
                "Followup_Nota": "Lead adicionado via Adição Rápida.",
                "Historico": f"Cadastrado em {datetime.now().strftime('%d/%m/%Y')}"
            }
            st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha_rapida])], ignore_index=True)
            st.success(f"✅ '{novo_nome_rapido}' adicionado com sucesso na carteira {nova_marca_rapida}!")
            st.rerun()
        else:
            st.warning("⚠️ Digite o nome da empresa para adicionar.")

    st.divider()
    
    # FORMULÁRIO COMPLETO
    st.subheader("📋 Cadastro Detalhado de Oportunidade")
    
    with st.form("form_oportunidade", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            nova_empresa = st.text_input("Nome da Empresa / Cliente *")
            novo_cliente = st.selectbox("Marca / Carteira *", CARTEIRAS_OFICIAIS)
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
                    "Followup_Data": str(f_data_ini) if f_nota_ini else "",
                    "Followup_Nota": f_nota_ini,
                    "Historico": f"Cadastrado em {datetime.now().strftime('%d/%m/%Y')}"
                }
                st.session_state.df_crm = pd.concat([st.session_state.df_crm, pd.DataFrame([nova_linha])], ignore_index=True)
                
                if nova_etapa == "6. Perdido" and motivo_perda in st.session_state.manual_perdas:
                    st.session_state.manual_perdas[motivo_perda] += 1
                
                st.success("✅ Cadastrado com sucesso!")
                st.rerun()