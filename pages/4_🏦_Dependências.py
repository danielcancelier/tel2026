import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from db import fetch_all, fetch_one, execute
from utils import text_input_nullable, number_input_nullable

st.set_page_config(page_title="Dependências", page_icon="🏦", layout="wide")
st.title("🏦 Dependências")

# =========================================================
# Helpers
# =========================================================

def _status_label(codigo: Optional[int], mapa: Dict[int, Dict[str, Any]]) -> str:
    if codigo is None:
        return "(vazio)"
    if pd.isna(codigo):
        return "(vazio)"
    try:
        codigo_int = int(codigo)
    except Exception:
        return "(vazio)"
    meta = mapa.get(codigo_int)
    if not meta:
        return f"{codigo_int} - (não encontrado)"
    return f"{codigo_int} - {meta['descricao']}"

def _to_bool(opt: str):
    if opt == "(vazio)":
        return None
    return True if opt == "Sim" else False

def _bool_to_label(v):
    if v is None:
        return "(vazio)"
    return "Sim" if v else "Não"

# =========================================================
# Cache
# =========================================================

@st.cache_data(ttl=300)
def cache_status():
    rows = fetch_all("""
        SELECT codigo, descricao, finaliza_ciclo
        FROM status
        ORDER BY codigo
    """)
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["codigo","descricao","finaliza_ciclo"])
    mapa = {
        int(r["codigo"]):{
            "descricao":r["descricao"],
            "finaliza_ciclo":bool(r["finaliza_ciclo"])
        }
        for r in rows
    }
    return df, mapa

def clear_cache():
    st.cache_data.clear()

# =========================================================
# Queries
# =========================================================

def dependencia_existe(prefixo, subordinada):
    row = fetch_one(
        "SELECT 1 FROM dependencia WHERE prefixo=%s AND subordinada=%s",
        (prefixo, subordinada)
    )
    return row is not None

def insert_dependencia(payload):
    sql = """
    INSERT INTO dependencia (
        prefixo, subordinada, nome, uor, cidade, uf,
        condominio, cod_condominio, linha_necessaria, tipo_ramal,
        contato_matricula, contato_nome, contato_obs,
        tem_central_pvv, ramais_controle, ramais_manter,
        pendencias, observacoes, cod_status, lote, concluido
    )
    VALUES (
        %s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,
        %s,%s,%s,
        %s,%s,%s,
        %s,%s,%s,%s,%s
    )
    """
    execute(sql,(
        payload["prefixo"],
        payload["subordinada"],
        payload["nome"],
        payload["uor"],
        payload["cidade"],
        payload["uf"],
        payload["condominio"],
        payload["cod_condominio"],
        payload["linha_necessaria"],
        payload["tipo_ramal"],
        payload["contato_matricula"],
        payload["contato_nome"],
        payload["contato_obs"],
        payload["tem_central_pvv"],
        payload["ramais_controle"],
        payload["ramais_manter"],
        payload["pendencias"],
        payload["observacoes"],
        payload["cod_status"],
        payload["lote"],
        payload["concluido"]
    ))

def update_concluido_bulk(changes):
    for prefixo,sub,valor in changes:
        execute(
            "UPDATE dependencia SET concluido=%s WHERE prefixo=%s AND subordinada=%s",
            (1 if valor else 0, prefixo, sub)
        )

def delete_dependencias(keys):
    for prefixo,sub in keys:
        execute(
            "DELETE FROM dependencia WHERE prefixo=%s AND subordinada=%s",
            (prefixo,sub)
        )

def query_dependencias():
    rows = fetch_all("""
        SELECT
            prefixo,
            subordinada,
            nome,
            cidade,
            uf,
            uor,
            lote,
            cod_status,
            concluido
        FROM dependencia
        ORDER BY prefixo, subordinada
    """)
    return pd.DataFrame(rows)

# =========================================================
# Status
# =========================================================

df_status, mapa_status = cache_status()

status_options = ["(vazio)"] + [
    f"{int(r['codigo'])} - {r['descricao']}" +
    (" • finaliza ciclo" if bool(r["finaliza_ciclo"]) else "")
    for _, r in df_status.iterrows()
]

# =========================================================
# Abas
# =========================================================

aba_incluir, aba_listar = st.tabs(["➕ Incluir","📋 Listar"])

# =========================================================
# ABA INCLUIR
# =========================================================

with aba_incluir:
    st.subheader("Nova dependência")
    with st.form("form_dep"):
        c1,c2,c3 = st.columns([1,1,1])
        with c1:
            prefixo = st.text_input("Prefixo", max_chars=4)
        with c2:
            subordinada = st.text_input("Subordinada", max_chars=2)
        with c3:
            concluido = st.checkbox("Dependência concluída")
        nome = text_input_nullable("Nome", key="nome")
        cidade = text_input_nullable("Cidade", key="cidade")
        uf = text_input_nullable("UF", key="uf")
        status_sel = st.selectbox("Status", status_options)
        salvar = st.form_submit_button("Salvar")
        cod_status = None
        if status_sel != "(vazio)":
            cod_status = int(status_sel.split(" - ")[0])
        if salvar:
            payload = {
                "prefixo":prefixo,
                "subordinada":subordinada,
                "nome":nome,
                "cidade":cidade,
                "uf":uf,
                "cod_status":cod_status,
                "concluido":concluido
            }
            if dependencia_existe(prefixo, subordinada):
                st.error("Dependência já existe")
            else:
                insert_dependencia(payload)
                clear_cache()
                st.success("Dependência incluída")

# =========================================================
# ABA LISTAR
# =========================================================

with aba_listar:
    st.subheader("Listagem")
    df = query_dependencias()
    if df.empty:
        st.info("Nenhum registro")
    else:
        df["status_desc"] = df["cod_status"].apply(
            lambda x: _status_label(x, mapa_status)
        )
        df["concluido_atual"] = df["concluido"].fillna(False).astype(bool)
        df["novo_concluido"] = df["concluido_atual"]
        df["excluir"] = False

        editor = st.data_editor(
            df[[
                "prefixo",
                "subordinada",
                "nome",
                "cidade",
                "uf",
                "status_desc",
                "concluido_atual",
                "novo_concluido",
                "excluir"
            ]],
            use_container_width=True,
            hide_index=True
        )

        col1,col2 = st.columns(2)

        with col1:
            if st.button("Aplicar conclusão"):
                changes = []
                for _,row in editor.iterrows():
                    if row["concluido_atual"] != row["novo_concluido"]:
                        changes.append((
                            row["prefixo"],
                            row["subordinada"],
                            row["novo_concluido"]
                        ))
                if changes:
                    update_concluido_bulk(changes)
                    clear_cache()
                    st.success(f"{len(changes)} atualizadas")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração")

        with col2:
            if st.button("Excluir selecionadas"):
                keys = []
                for _,row in editor.iterrows():
                    if row["excluir"]:
                        keys.append((row["prefixo"],row["subordinada"]))
                if keys:
                    delete_dependencias(keys)
                    clear_cache()
                    st.success(f"{len(keys)} excluídas")
                    st.rerun()
                else:
                    st.info("Nada selecionado")
