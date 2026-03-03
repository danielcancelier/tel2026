import streamlit as st
import pandas as pd
from db import fetch_all, execute

st.set_page_config(page_title="Produtos", page_icon="🧾", layout="wide")
st.title("🧾 Produtos")

aba_listar, aba_editar = st.tabs(["📋 Listar", "✏️ Incluir/Editar"]) 

with aba_listar:
    with st.expander("Filtros", expanded=True):
        f_codigo = st.text_input("Código", key="prod_f_codigo")
        f_desc = st.text_input("Descrição contém", key="prod_f_desc")
        f_forn = st.text_input("Fornecedor contém", key="prod_f_forn")
    sql = "SELECT codigo, descricao, fornecedor FROM produtos WHERE 1=1"
    params = []
    if f_codigo.strip():
        sql += " AND codigo=%s"; params.append(int(f_codigo))
    if f_desc.strip():
        sql += " AND descricao LIKE %s"; params.append(f"%{f_desc}%")
    if f_forn.strip():
        sql += " AND fornecedor LIKE %s"; params.append(f"%{f_forn}%")
    sql += " ORDER BY codigo"
    rows = fetch_all(sql, tuple(params))
    st.dataframe(pd.DataFrame(rows))

with aba_editar:
    c1, c2, c3 = st.columns(3)
    with c1:
        codigo = st.text_input("Código (PK, obrigatório)", key="prod_ed_codigo")
    with c2:
        descricao = st.text_input("Descrição", key="prod_ed_descricao")
    with c3:
        fornecedor = st.text_input("Fornecedor", key="prod_ed_fornecedor")

    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("➕ Incluir", key="prod_bt_incluir"):
            if not codigo.strip():
                st.error("Informe o código (inteiro).")
            else:
                try:
                    execute(
                        "INSERT INTO produtos (codigo, descricao, fornecedor) VALUES (%s,%s,%s)",
                        (int(codigo), descricao or None, fornecedor or None)
                    )
                    st.success("Incluído.")
                except Exception as e:
                    st.error(f"Erro: {e}")
    with colB:
        if st.button("💾 Atualizar", key="prod_bt_atualizar"):
            if not codigo.strip():
                st.error("Informe o código.")
            else:
                try:
                    execute(
                        "UPDATE produtos SET descricao=%s, fornecedor=%s WHERE codigo=%s",
                        (descricao or None, fornecedor or None, int(codigo))
                    )
                    st.success("Atualizado.")
                except Exception as e:
                    st.error(f"Erro: {e}")
    with colC:
        if st.button("🗑️ Excluir", key="prod_bt_excluir"):
            if not codigo.strip():
                st.error("Informe o código.")
            else:
                try:
                    execute("DELETE FROM produtos WHERE codigo=%s", (int(codigo),))
                    st.success("Excluído.")
                except Exception as e:
                    st.error(f"Erro: {e}")
