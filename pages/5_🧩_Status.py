
import streamlit as st
import pandas as pd
from db import fetch_all, execute
from utils import number_input_nullable, text_input_nullable

st.set_page_config(page_title="Status", page_icon="🧩", layout="wide")
st.title("🧩 Status")

aba_listar, aba_editar = st.tabs(["📋 Listar", "✏️ Incluir/Editar"]) 

with aba_listar:
    rows = fetch_all("SELECT codigo, descricao FROM status ORDER BY codigo")
    st.dataframe(pd.DataFrame(rows))

with aba_editar:
    c1, c2 = st.columns(2)
    with c1:
        codigo = st.text_input("Código (PK, obrigatório)")
    with c2:
        descricao = st.text_input("Descrição")
    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("➕ Incluir"):
            if not codigo:
                st.error("Informe o código (inteiro).")
            else:
                try:
                    execute("INSERT INTO status (codigo, descricao) VALUES (%s, %s)", (int(codigo), descricao or None))
                    st.success("Incluído.")
                except Exception as e:
                    st.error(f"Erro: {e}")
    with colB:
        if st.button("💾 Atualizar"):
            if not codigo:
                st.error("Informe o código.")
            else:
                try:
                    execute("UPDATE status SET descricao=%s WHERE codigo=%s", (descricao or None, int(codigo)))
                    st.success("Atualizado.")
                except Exception as e:
                    st.error(f"Erro: {e}")
    with colC:
        if st.button("🗑️ Excluir"):
            if not codigo:
                st.error("Informe o código.")
            else:
                try:
                    execute("DELETE FROM status WHERE codigo=%s", (int(codigo),))
                    st.success("Excluído.")
                except Exception as e:
                    st.error(f"Erro: {e}")
