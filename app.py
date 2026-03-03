import streamlit as st
from db import fetch_one

st.set_page_config(page_title="Portal Telefonia", page_icon="📞", layout="wide")
st.title("📞 Portal Telefonia")

st.write(
    """
    Bem-vindo! Use o menu lateral para acessar os cadastros e históricos:
    - **Dependências**: cadastro principal da unidade (prefixo + subordinada)
    - **Status**: tabela de referência de status
    - **Comunicação**: histórico de envios e respostas
    - **BBTS**: registros de chamados/OS
    - **Atualizações**: histórico de status (sincroniza `dependencia.cod_status`)
    """
)

with st.sidebar:
    st.header("⚙️ Conexão")
    try:
        row = fetch_one("SELECT DATABASE() AS db")
        st.success(f"Conectado ao MySQL • DB: {row['db']}")
    except Exception as e:
        st.error(f"Erro de conexão: {e!r}")
