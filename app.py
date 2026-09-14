import json
import os
import streamlit as st

ARQUIVO_DADOS = "clientes.json"


# Função para carregar os clientes do arquivo
def carregar_clientes():
  if os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except json.JSONDecodeError:
        return []
  return []


# Função para salvar os clientes no arquivo
def salvar_clientes(lista_clientes):
  with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
      json.dump(lista_clientes, f, ensure_ascii=False, indent=4)


# Inicializa o session_state com os dados salvos no disco
if "clientes" not in st.session_state:
  st.session_state.clientes = carregar_clientes()

st.title("Meu CRM Simples")

# Formulário para cadastrar novo cliente
with st.form("form_cliente", clear_on_submit=True):
  nome = st.text_input("Nome do Cliente")
  email = st.text_input("E-mail")
  botao_enviar = st.form_submit_button("Salvar Cliente")

  if botao_enviar:
    if nome:
      novo_cliente = {"nome": nome, "email": email}
      st.session_state.clientes.append(novo_cliente)
      # Salva permanentemente no arquivo JSON
      salvar_clientes(st.session_state.clientes)
      st.success(f"Cliente {nome} salvo com sucesso!")
    else:
      st.error("O nome do cliente é obrigatório.")

# Exibição dos clientes cadastrados
st.subheader("Clientes Cadastrados")
if st.session_state.clientes:
  for i, cliente in enumerate(st.session_state.clientes, 1):
    st.write(f"**{i}.** {cliente['nome']} - {cliente['email']}")
else:
  st.info("Nenhum cliente cadastrado ainda.")
