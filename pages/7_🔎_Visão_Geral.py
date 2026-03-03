
import streamlit as st
import pandas as pd
from db import fetch_all

st.set_page_config(page_title="Visão Geral", page_icon="🔎", layout="wide")
st.title("🔎 Visão Geral")

st.write("Resumo das dependências com status (join em `status`).")

sql = """
SELECT d.prefixo, d.subordinada, d.uor, d.cod_condominio, d.tipo_ramal, d.ramais_controle, d.ramais_manter,
       d.cod_status, s.descricao AS status_descricao, d.lote
  FROM dependencia d
  LEFT JOIN status s ON s.codigo = d.cod_status
 ORDER BY d.prefixo, d.subordinada
"""
rows = fetch_all(sql)

st.dataframe(pd.DataFrame(rows))
