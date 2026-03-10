import streamlit as st
import pandas as pd
from db import fetch_all, execute

st.set_page_config(page_title="Atualizações", page_icon="📒", layout="wide")
st.title("📒 Atualizações")

# --- controle do modal ---
if 'atu_open_modal' not in st.session_state:
    st.session_state['atu_open_modal'] = False

# ---------- utils ----------
@st.cache_data(show_spinner=False)
def load_produtos_for_select():
    rows = fetch_all("SELECT codigo, descricao FROM produtos ORDER BY codigo")
    options = ["(selecione)"]
    display_map = {"(selecione)": None}
    for r in rows:
        codigo = r["codigo"]
        desc = r["descricao"] or ""
        label = f"{codigo} - {desc}".strip()
        options.append(label)
        display_map[label] = int(codigo)
    return options, display_map

@st.cache_data(show_spinner=False)
def load_status_for_select():
    rows = fetch_all("SELECT codigo, descricao FROM status ORDER BY codigo")
    options = ["(selecione)"]
    display_map = {"(selecione)": None}
    for r in rows:
        codigo = r["codigo"]
        desc = r["descricao"] or ""
        label = f"{codigo} - {desc}".strip()
        options.append(label)
        display_map[label] = int(codigo)
    return options, display_map

@st.cache_data(ttl=300, show_spinner=False)
def cache_dependencias():
    rows = fetch_all("SELECT prefixo, subordinada, nome FROM dependencia ORDER BY prefixo, subordinada")
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["prefixo", "subordinada", "nome"])
    df["prefixo"] = df["prefixo"].astype(str).str.strip()
    df["subordinada"] = df["subordinada"].astype(str).str.strip()
    df["nome"] = df["nome"].astype(str).fillna("").str.strip()
    key_set = set(zip(df["prefixo"], df["subordinada"]))
    lookup_nome = {(p, s): n for p, s, n in zip(df["prefixo"], df["subordinada"], df["nome"])}
    options = [f"{p}-{s} — {n}" if n else f"{p}-{s}" for p, s, n in zip(df["prefixo"], df["subordinada"], df["nome"]) ]
    display_map = {opt: (p, s) for opt, p, s in zip(options, df["prefixo"], df["subordinada"]) }
    return df, key_set, lookup_nome, options, display_map

def dependencia_existe(prefixo: str, subordinada: str):
    if not prefixo or not subordinada:
        return False
    _, key_set, _, _, _ = cache_dependencias()
    return (prefixo.strip(), subordinada.strip()) in key_set

def nome_da_dependencia(prefixo: str, subordinada: str):
    if not prefixo or not subordinada:
        return None
    _, _, lookup_nome, _, _ = cache_dependencias()
    return lookup_nome.get((prefixo.strip(), subordinada.strip()))

# ---- helpers ----
@st.dialog("🔍 Buscar dependência", width="large")
def abrir_busca_dependencia():
    df, _, _, _, display_map = cache_dependencias()
    q = st.text_input("Pesquisar por Prefixo, Subordinada ou Nome", placeholder="Ex.: 0080, 00, PETROPOLIS", key="atu_inc_q")
    colf1, colf2 = st.columns([1, 1])
    with colf1:
        pref_match = st.checkbox("Buscar por prefixo (começa com)", value=True)
    with colf2:
        limit = st.select_slider("Máx. resultados", options=[20, 50, 100, 200, 500], value=100)

    if q and q.strip():
        qs = q.strip().lower()
        m_prefixo = df["prefixo"].str.lower().str.startswith(qs) if pref_match else df["prefixo"].str.contains(qs, case=False, na=False)
        m_sub = df["subordinada"].str.contains(qs, case=False, na=False)
        m_nome = df["nome"].str.contains(qs, case=False, na=False)
        df_view = df.loc[(m_prefixo | m_sub | m_nome)].copy()
    else:
        df_view = df.copy()

    df_view = df_view.head(int(limit))
    opts = [f"{p}-{s} — {n}" if n else f"{p}-{s}" for p, s, n in zip(df_view["prefixo"], df_view["subordinada"], df_view["nome"])]
    sel = st.selectbox("Resultados", options=opts if opts else ["(nenhum encontrado)"], index=0 if opts else None, placeholder="Digite para filtrar")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("✅ Selecionar e aplicar", use_container_width=True):
            if sel and sel in display_map:
                pfx, sub = display_map[sel]
                st.session_state['atu_inc_prefixo'] = pfx
                st.session_state['atu_inc_sub'] = sub
                st.session_state['atu_open_modal'] = False
                st.toast(f"Selecionado: {pfx}-{sub}", icon="🔎")
                st.rerun()
    with c2:
        if st.button("✖️ Fechar", use_container_width=True):
            st.session_state['atu_open_modal'] = False
            st.rerun()



# ---- confirmação de exclusão ----
@st.dialog("🗑️ Confirmar exclusão", width="large")
def abrir_confirm_exclusao():
    ids = st.session_state.get('atu_del_ids', [])
    if not ids:
        st.info("Nenhum registro selecionado.")
        if st.button("Fechar", use_container_width=True):
            st.session_state['atu_open_confirm'] = False
            st.rerun()
        return

    st.warning(f"Confirma a exclusão de **{len(ids)}** registro(s)?")
    with st.expander("Visualizar IDs selecionados", expanded=False):
        st.code(", ".join(map(str, ids)), language=None)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Confirmar exclusão", type="primary", use_container_width=True):
            try:
                for _id in ids:
                    execute("DELETE FROM atualizacoes WHERE id=%s", (int(_id),))
                st.toast(f"Excluídos: {ids}", icon="✅")
                st.cache_data.clear()
                st.session_state['atu_open_confirm'] = False
                st.session_state.pop('atu_del_ids', None)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
    with c2:
        if st.button("✖️ Cancelar", use_container_width=True):
            st.session_state['atu_open_confirm'] = False
            st.rerun()
# --------------------------- ABAS: Incluir | Listar ---------------------------
aba_incluir, aba_listar = st.tabs(["➕ Incluir", "📋 Listar"])

# -------------------------------- INCLUIR -----------------------------------
with aba_incluir:
    st.subheader("Inclusão")
    l1, l2, l3, l4 = st.columns([1, 1, 0.3, 3])
    with l1:
        st.caption("Prefixo (4)")
    with l2:
        st.caption("Subordinada (2)")
    with l3:
        st.caption(" ")
    with l4:
        st.caption(" ")

    c1, c2, c3, c4 = st.columns([1, 1, 0.3, 3])
    with c1:
        sel_prefixo = st.text_input("Prefixo (4)", key="atu_inc_prefixo", max_chars=4, label_visibility="collapsed", placeholder="0000", on_change=lambda: st.session_state.update({'atu_open_modal': False}))
    with c2:
        sel_sub = st.text_input("Subordinada (2)", key="atu_inc_sub", max_chars=2, label_visibility="collapsed", placeholder="00", on_change=lambda: st.session_state.update({'atu_open_modal': False}))
    with c3:
        if st.button("🔍", key="atu_inc_btn_lupa", help="Buscar dependência"):
            st.session_state['atu_open_modal'] = True
    with c4:
        if (sel_prefixo and len(sel_prefixo.strip()) == 4) and (sel_sub and len(sel_sub.strip()) == 2):
            _nome = nome_da_dependencia(sel_prefixo, sel_sub)
            if _nome:
                st.markdown(f"<div style='padding:6px 10px;background:#F0F2F6;border-radius:6px;display:inline-block'>🏷 {sel_prefixo}-{sel_sub} — {_nome}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding:6px 10px;background:#FFF3CD;border-radius:6px;display:inline-block'>❓ {sel_prefixo}-{sel_sub} — não encontrada</div>", unsafe_allow_html=True)

    if st.session_state.get('atu_open_modal'):
        abrir_busca_dependencia()

    with st.form("atu_form_incluir", clear_on_submit=True):
        c1b, c2b, c3b = st.columns(3)
        with c1b:
            st_opts, st_map = load_status_for_select()
            if st.session_state.get("atu_inc_status_label") not in st_opts:
                st.session_state["atu_inc_status_label"] = None
            st_label = st.selectbox("Status", options=st_opts, index=None, placeholder="Selecione...", key="atu_inc_status_label")
            cod_status = st_map.get(st_label)
        with c2b:
            prod_opts, prod_map = load_produtos_for_select()
            if st.session_state.get("atu_inc_prod_label") not in prod_opts:
                st.session_state["atu_inc_prod_label"] = None
            prod_label = st.selectbox("Produto", options=prod_opts, index=None, placeholder="Selecione...", key="atu_inc_prod_label")
            cod_produto = prod_map.get(prod_label)
        with c3b:
            quantidade = st.text_input("Quantidade", key="atu_inc_qtde")
            dt = st.date_input("Data do status", value=None, format="DD/MM/YYYY", key="atu_inc_data")
            data_status = dt.isoformat() if dt else None
            descricao = st.text_area("Descrição", key="atu_inc_desc")

        salvar = st.form_submit_button("💾 Salvar")
        if salvar:
            if not sel_prefixo or not sel_sub:
                st.error("Informe Prefixo e Subordinada, ou use a busca para selecionar uma dependência.")
            elif not dependencia_existe(sel_prefixo, sel_sub):
                st.error("Dependência não encontrada. Cadastre primeiro em 📌 Dependências (mesmo prefixo/subordinada).")
            elif cod_status is None:
                st.error("Selecione um Status.")
            elif cod_produto is None:
                st.error("Selecione um Produto.")
            else:
                try:
                    execute(
                        "INSERT INTO atualizacoes (prefixo, subordinada, cod_status, cod_produto, quantidade, data_status, descricao) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (
                            sel_prefixo.strip(),
                            sel_sub.strip(),
                            cod_status,
                            cod_produto,
                            int(quantidade) if str(quantidade).strip() else None,
                            data_status,
                            descricao or None,
                        ),
                    )
                    st.toast("Incluído com sucesso!", icon="✅")
                    st.cache_data.clear()
                except Exception as e:
                    st.toast(f"Erro ao incluir: {e}", icon="❌")

# -------------------------------- LISTAR -----------------------------------
with aba_listar:
    with st.expander("Filtros", expanded=True):
        f_prefixo = st.text_input("Prefixo (4)", max_chars=4, key="atu_f_prefixo")
        f_sub = st.text_input("Subordinada (2)", max_chars=2, key="atu_f_sub")
        st_opts, st_map = load_status_for_select()
        f_status_label = st.selectbox("Status", options=st_opts, index=0, key="atu_f_status_label")
        f_status_codigo = st_map.get(f_status_label)

        prod_opts, prod_map = load_produtos_for_select()
        f_prod_label = st.selectbox("Produto", options=prod_opts, index=0, key="atu_f_prod_label")
        f_prod_codigo = prod_map.get(f_prod_label)

    sql = """
    SELECT id, prefixo, subordinada, cod_status, cod_produto, quantidade, data_status, LEFT(descricao, 120) AS descricao
    FROM atualizacoes
    WHERE 1=1
    """
    params = []
    if f_prefixo.strip():
        sql += " AND prefixo=%s"; params.append(f_prefixo.strip())
    if f_sub.strip():
        sql += " AND subordinada=%s"; params.append(f_sub.strip())
    if f_status_codigo is not None:
        sql += " AND cod_status=%s"; params.append(int(f_status_codigo))
    if f_prod_codigo is not None:
        sql += " AND cod_produto=%s"; params.append(int(f_prod_codigo))
    sql += " ORDER BY id DESC"

    rows = fetch_all(sql, tuple(params))
    df = pd.DataFrame(rows)

    st.write(":mag: **Resultados** (clique na coluna 'Excluir' para marcar e excluir)")

    if df is None or df.empty:
        st.info("Nenhum registro encontrado.")
    else:
        # adiciona coluna de seleção
        df_view = df.copy()
        df_view["Excluir"] = False

        edited = st.data_editor(
            df_view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Excluir": st.column_config.CheckboxColumn(
                    label="Excluir",
                    help="Selecione as linhas que deseja excluir",
                    default=False
                )
            }
        )

        # capta IDs marcados
        if "Excluir" in edited.columns:
            ids_marcados = edited.loc[edited["Excluir"] == True, "id"].tolist()
        else:
            ids_marcados = []

        col_del1, col_del2 = st.columns([1,3])
with col_del1:
    btn_del = st.button(f'🗑️ Excluir selecionados ({len(ids_marcados)})', disabled=(len(ids_marcados)==0))
with col_del2:
    st.caption("")

if btn_del:
    st.session_state['atu_del_ids'] = ids_marcados
    st.session_state['atu_open_confirm'] = True
    st.rerun()

# abrir modal de confirmação se sinalizado
if st.session_state.get('atu_open_confirm'):
    abrir_confirm_exclusao()
