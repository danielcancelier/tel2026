import streamlit as st
import pandas as pd
from db import fetch_all, fetch_one, execute
from utils import text_input_nullable, number_input_nullable
from typing import Dict, Any

st.set_page_config(page_title="Dependências", page_icon="🏦", layout="wide")
st.title("🏦 Dependências")

# ---------------------- Utilidades de exibição ----------------------
def _fmt(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return "—"
    return str(v)

def _sel_to_bool_no_null(opt: str) -> int:
    """Mapeia 'Sim'/'Não' para 1/0. (sem '(vazio)')"""
    return 1 if opt == "Sim" else 0

def _to_bool_from_str(opt: str):
    """Mapeia '(qualquer)'/Sim/Não para None/True/False no Filtro da Listar."""
    if opt == "(qualquer)":
        return None
    return True if opt == "Sim" else False

def _to_int_or_none(v: str):
    v = (v or "").strip()
    if v == "" or v == "—":
        return None
    try:
        return int(v)
    except:
        return None

# ---------------------- Cache de listas auxiliares ----------------------
@st.cache_data(ttl=300, show_spinner=False)
def cache_lookup_nomes():
    rows = fetch_all("SELECT prefixo, subordinada, nome FROM dependencia ORDER BY prefixo, subordinada")
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["prefixo","subordinada","nome"])
    df['prefixo'] = df['prefixo'].astype(str).str.strip()
    df['subordinada'] = df['subordinada'].astype(str).str.strip()
    df['nome'] = df['nome'].astype(str).fillna("").str.strip()
    lookup = {(p,s): n for p,s,n in zip(df['prefixo'], df['subordinada'], df['nome'])}
    return lookup

# ---------------------- Dados ----------------------
def load_dependencia(prefixo: str, subordinada: str):
    sql = """
    SELECT prefixo, subordinada, nome, uor, condominio, cod_condominio, linha_necessaria,
           contato_matricula, contato_nome, contato_obs, tem_central_pvv,
           ramais_controle, ramais_manter, pendencias, observacoes, concluido, lote
    FROM dependencia
    WHERE prefixo=%s AND subordinada=%s
    """
    return fetch_one(sql, (prefixo, subordinada))

def save_dependencia(payload: Dict[str, Any], is_update: bool):
    """
    Insere ou atualiza um registro na tabela 'dependencia'.
    - is_update=False: INSERT
    - is_update=True : UPDATE (WHERE prefixo AND subordinada)
    """
    if not payload.get("prefixo") or not payload.get("subordinada"):
        raise ValueError("Prefixo e Subordinada são obrigatórios para salvar.")

    if is_update:
        sql = """
        UPDATE dependencia SET
            nome=%s, uor=%s, condominio=%s, cod_condominio=%s,
            linha_necessaria=%s, contato_matricula=%s, contato_nome=%s,
            contato_obs=%s, tem_central_pvv=%s, ramais_controle=%s,
            ramais_manter=%s, pendencias=%s, observacoes=%s,
            concluido=%s, lote=%s
        WHERE prefixo=%s AND subordinada=%s
        """
        params = (
            payload.get("nome"), payload.get("uor"), payload.get("condominio"),
            payload.get("cod_condominio"), payload.get("linha_necessaria"),
            payload.get("contato_matricula"), payload.get("contato_nome"),
            payload.get("contato_obs"), payload.get("tem_central_pvv"),
            payload.get("ramais_controle"), payload.get("ramais_manter"),
            payload.get("pendencias"), payload.get("observacoes"),
            payload.get("concluido"), payload.get("lote"),
            payload.get("prefixo"), payload.get("subordinada"),
        )
        execute(sql, params)
    else:
        sql = """
        INSERT INTO dependencia (
            prefixo, subordinada, nome, uor, condominio, cod_condominio,
            linha_necessaria, contato_matricula, contato_nome, contato_obs,
            tem_central_pvv, ramais_controle, ramais_manter, pendencias,
            observacoes, concluido, lote
        ) VALUES (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        )
        """
        params = (
            payload.get("prefixo"), payload.get("subordinada"), payload.get("nome"),
            payload.get("uor"), payload.get("condominio"), payload.get("cod_condominio"),
            payload.get("linha_necessaria"), payload.get("contato_matricula"),
            payload.get("contato_nome"), payload.get("contato_obs"),
            payload.get("tem_central_pvv"), payload.get("ramais_controle"),
            payload.get("ramais_manter"), payload.get("pendencias"),
            payload.get("observacoes"), payload.get("concluido"), payload.get("lote"),
        )
        execute(sql, params)

# ---------------------- Abas ----------------------
aba_incluir, aba_listar, aba_editar = st.tabs(["➕ Incluir", "📋 Listar", "✏️ Editar"])

# -------------------------------- LISTAR -----------------------------------
with aba_listar:
    with st.expander("Filtros", expanded=True):
        f_prefixo = st.text_input("Prefixo (4)", max_chars=4, key="dep_f_prefixo")
        f_sub = st.text_input("Subordinada (2)", max_chars=2, key="dep_f_sub")
        f_lote = st.text_input("Lote", max_chars=10, key="dep_f_lote")
        f_conc = st.selectbox("Concluído?", ["(qualquer)", "Sim", "Não"], index=0, key="dep_f_concluido")

        sql = (
            "SELECT prefixo, subordinada, nome, uor, cod_condominio, "
            "ramais_controle, ramais_manter, concluido, lote FROM dependencia WHERE 1=1"
        )
        params = []
        if f_prefixo.strip():
            sql += " AND prefixo=%s"; params.append(f_prefixo.strip())
        if f_sub.strip():
            sql += " AND subordinada=%s"; params.append(f_sub.strip())
        if f_lote.strip():
            try:
                params.append(int(f_lote.strip()))