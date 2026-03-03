import streamlit as st
import pandas as pd
from db import fetch_all, execute

st.set_page_config(page_title="Atualizações", page_icon="📈", layout="wide")
st.title("📈 Atualizações (Histórico de Status)")

# ---------------------- Estilos globais ----------------------
st.markdown(
    """
<style>
/* Badge do nome */
.dep-badge {
  display:inline-flex; align-items:center; gap:.5rem; padding:.25rem .5rem;
  border-radius:.6rem; background:#eef6ff; color:#0f3c73; border:1px solid #cfe6ff;
  white-space:nowrap; max-width:100%; overflow:hidden; text-overflow:ellipsis; font-weight:600;
}
.dep-badge .code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.dep-badge.bad { background:#fff2f0; color:#8a120e; border-color:#ffd1cc; }

/* Inputs compactos */
.stTextInput > div > div > input { height:2rem; padding:.2rem .5rem; font-size:.9rem; }

/* Botão menor (secondary) */
.stButton > button[kind="secondary"], .stButton > button[type="submit"] { padding:.35rem .55rem; font-size:.95rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- utils: carregar listas para select ----------
@st.cache_data(show_spinner=False)
def load_produtos_for_select():
    rows = fetch_all("SELECT codigo, descricao FROM produtos ORDER BY descricao")
    options = ["(vazio)"]
    display_map = {"(vazio)": None}
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
    options = ["(vazio)"]
    display_map = {"(vazio)": None}
    for r in rows:
        codigo = r["codigo"]
        desc = r["descricao"] or ""
        label = f"{codigo} - {desc}".strip()
        options.append(label)
        display_map[label] = int(codigo)
    return options, display_map

@st.cache_data(show_spinner=False)
def load_dependencias_for_select():
    rows = fetch_all(
        "SELECT prefixo, subordinada, nome FROM dependencia ORDER BY prefixo, subordinada"
    )
    options = ["(selecione)"]
    display_map = {"(selecione)": (None, None)}
    for r in rows:
        p = (r.get("prefixo") or "").strip()
        s = (r.get("subordinada") or "").strip()
        nome = (r.get("nome") or "").strip()
        label = f"{p}-{s} — {nome}" if nome else f"{p}-{s}"
        options.append(label)
        display_map[label] = (p, s)
    return options, display_map

@st.cache_data(show_spinner=False)
def load_dependencias(prefixo_filter: str = ""):
    sql = "SELECT prefixo, subordinada, nome FROM dependencia WHERE 1=1"
    params = []
    if prefixo_filter and prefixo_filter.strip():
        sql += " AND prefixo LIKE %s"
        params.append(prefixo_filter.strip() + '%')
    sql += " ORDER BY prefixo, subordinada"
    return fetch_all(sql, tuple(params))

# ---------- Cache otimizado: carrega todas dependências 1x e pesquisa local ----------
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
    options = [f"{p}-{s} — {n}" if n else f"{p}-{s}" for p, s, n in zip(df["prefixo"], df["subordinada"], df["nome"])]
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

# -------------------------------- util: modal de busca --------------------------------
@st.dialog("🔍 Buscar dependência", width="large")
def abrir_busca_dependencia():
    df, _, _, options, display_map = cache_dependencias()
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

# --------------------------- ABAS: Incluir | Listar | Editar ---------------------------
aba_incluir, aba_listar, aba_editar = st.tabs(["➕ Incluir", "📋 Listar", "✏️ Editar"])

# -------------------------------- INCLUIR -----------------------------------
with aba_incluir:
    st.subheader("Nova atualização")

    # ===== Faixa superior em duas linhas dentro de um form (labels na 1ª linha, widgets na 2ª) =====
    with st.form("form_dep_row"):
        # Linha 1: labels
        l1, l2, l3, l4 = st.columns([1, 1, 0.3, 3])
        with l1:
            st.caption("Prefixo (4)")
        with l2:
            st.caption("Subordinada (2)")
        with l3:
            st.caption("\u00A0")
        with l4:
            st.caption("\u00A0")

        # Linha 2: widgets
        c1, c2, c3, c4 = st.columns([1, 1, 0.3, 3])
        with c1:
            sel_prefixo = st.text_input(
                "",
                key="atu_inc_prefixo",
                max_chars=4,
                label_visibility="collapsed",
                placeholder="0000"
            )
        with c2:
            sel_sub = st.text_input(
                "",
                key="atu_inc_sub",
                max_chars=2,
                label_visibility="collapsed",
                placeholder="00"
            )
        with c3:
            abrir = st.form_submit_button("🔍")
        with c4:
            # badge do nome
            if (sel_prefixo and len(sel_prefixo.strip()) == 4) and (sel_sub and len(sel_sub.strip()) == 2):
                _nome = nome_da_dependencia(sel_prefixo, sel_sub)
                if _nome:
                    st.markdown(
                        f"<div class='dep-badge'>🏷 <span class='code'>{sel_prefixo}-{sel_sub}</span> — {_nome}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div class='dep-badge bad'>❓ <span class='code'>{sel_prefixo}-{sel_sub}</span> — não encontrada</div>",
                        unsafe_allow_html=True,
                    )
        if abrir:
            st.session_state['atu_open_modal'] = True

    # Abre modal se flag estiver setada (evita problemas de submit dentro do dialog)
    if st.session_state.get('atu_open_modal'):
        abrir_busca_dependencia()

    # Campos principais
    c1, c2, c3 = st.columns(3)
    with c1:
        st_opts, st_map = load_status_for_select()
        st_label = st.selectbox("Status", options=st_opts, index=0, key="atu_inc_status_label")
        cod_status = st_map.get(st_label)
    with c2:
        prod_opts, prod_map = load_produtos_for_select()
        prod_label = st.selectbox("Produto", options=prod_opts, index=0, key="atu_inc_prod_label")
        cod_produto = prod_map.get(prod_label)
    with c3:
        quantidade = st.text_input("Quantidade", key="atu_inc_qtde")
        dt = st.date_input("Data do status", value=None, format="DD/MM/YYYY", key="atu_inc_data")
    data_status = dt.isoformat() if dt else None

    descricao = st.text_area("Descrição", key="atu_inc_desc")

    if st.button("➕ Incluir", key="atu_bt_incluir_tab"):
        if not sel_prefixo or not sel_sub:
            st.error("Informe Prefixo e Subordinada, ou use a busca para selecionar uma dependência.")
        else:
            if not dependencia_existe(sel_prefixo, sel_sub):
                st.error("Dependência não encontrada. Cadastre primeiro em 📌 Dependências (mesmo prefixo/subordinada).")
            else:
                try:
                    execute(
                        "INSERT INTO atualizacoes (prefixo, subordinada, cod_status, cod_produto, quantidade, data_status, descricao) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (
                            sel_prefixo.strip(), sel_sub.strip(),
                            cod_status if cod_status is not None else None,
                            cod_produto if cod_produto is not None else None,
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
        f_status = st.text_input("Código do status", key="atu_f_status")
        prod_opts, prod_map = load_produtos_for_select()
        f_prod_label = st.selectbox("Produto", options=prod_opts, index=0, key="atu_f_prod_label")
        f_prod_codigo = prod_map.get(f_prod_label)

    sql = """
    SELECT id, prefixo, subordinada, cod_status, cod_produto, quantidade, data_status,
           LEFT(descricao, 120) AS descricao
    FROM atualizacoes
    WHERE 1=1
    """
    params = []
    if f_prefixo.strip():
        sql += " AND prefixo=%s"; params.append(f_prefixo.strip())
    if f_sub.strip():
        sql += " AND subordinada=%s"; params.append(f_sub.strip())
    if f_status.strip():
        sql += " AND cod_status=%s"; params.append(int(f_status))
    if f_prod_codigo is not None:
        sql += " AND cod_produto=%s"; params.append(int(f_prod_codigo))
    sql += " ORDER BY (data_status IS NOT NULL) DESC, data_status DESC, id DESC"

    rows = fetch_all(sql, tuple(params))
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# -------------------------------- EDITAR -----------------------------------
with aba_editar:
    st.subheader("Selecionar / Editar")
    id_edit = st.text_input("ID (somente para editar ou excluir)", key="atu_ed_id")

    # linha compacta coerente com a de Incluir
    e1, e2, e3, e4 = st.columns([1, 1, 0.3, 3])
    with e1:
        st.caption("Prefixo (4)")
        prefixo = st.text_input("", max_chars=4, key="atu_ed_prefixo", label_visibility="collapsed", placeholder="0000")
    with e2:
        st.caption("Subordinada (2)")
        subordinada = st.text_input("", max_chars=2, key="atu_ed_sub", label_visibility="collapsed", placeholder="00")
    with e3:
        st.caption("\u00A0")
        st.button("🔍", key="atu_ed_btn_dummy", type="secondary", disabled=True)
    with e4:
        st.caption("\u00A0")
        if (prefixo and len(prefixo.strip()) == 4) and (subordinada and len(subordinada.strip()) == 2):
            _nome = nome_da_dependencia(prefixo, subordinada)
            if _nome:
                st.markdown(
                    f"<div class='dep-badge'>🏷 <span class='code'>{prefixo}-{subordinada}</span> — {_nome}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='dep-badge bad'>❓ <span class='code'>{prefixo}-{subordinada}</span> — não encontrada</div>",
                    unsafe_allow_html=True,
                )

    c1, c2, c3 = st.columns(3)
    with c1:
        st_opts, st_map = load_status_for_select()
        st_label = st.selectbox("Status", options=st_opts, index=0, key="atu_ed_status_label")
        cod_status = st_map.get(st_label)
    with c2:
        prod_opts, prod_map = load_produtos_for_select()
        prod_label = st.selectbox("Produto", options=prod_opts, index=0, key="atu_ed_prod_label")
        cod_produto = prod_map.get(prod_label)
    with c3:
        quantidade = st.text_input("Quantidade", key="atu_ed_qtde")
        dt = st.date_input("Data do status", value=None, format="DD/MM/YYYY", key="atu_ed_data")
    data_status = dt.isoformat() if dt else None

    descricao = st.text_area("Descrição", key="atu_ed_desc")

    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("➕ Incluir", key="atu_bt_incluir_legacy"):
            if id_edit.strip():
                st.error("Para incluir, deixe o ID em branco. (Use a aba 'Incluir' para a experiência recomendada)")
            else:
                if not dependencia_existe(prefixo, subordinada):
                    st.error("Dependência não encontrada. Cadastre primeiro em 📌 Dependências (mesmo prefixo/subordinada).")
                else:
                    try:
                        execute(
                            "INSERT INTO atualizacoes (prefixo, subordinada, cod_status, cod_produto, quantidade, data_status, descricao) "
                            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                            (
                                prefixo.strip(), subordinada.strip(),
                                cod_status if cod_status is not None else None,
                                cod_produto if cod_produto is not None else None,
                                int(quantidade) if str(quantidade).strip() else None,
                                data_status,
                                descricao or None,
                            ),
                        )
                        st.success("Incluído com sucesso! (cod_status da dependência será sincronizado pelo trigger)")
                    except Exception as e:
                        st.error(f"Erro: {e}")
    with colB:
        if st.button("💾 Atualizar", key="atu_bt_atualizar"):
            if not id_edit.strip():
                st.error("Informe o ID para atualizar.")
            else:
                if not dependencia_existe(prefixo, subordinada):
                    st.error("Dependência não encontrada. Ajuste prefixo/subordinada ou cadastre em 📌 Dependências.")
                else:
                    try:
                        execute(
                            "UPDATE atualizacoes SET prefixo=%s, subordinada=%s, cod_status=%s, cod_produto=%s, quantidade=%s, data_status=%s, descricao=%s WHERE id=%s",
                            (
                                prefixo.strip(), subordinada.strip(),
                                cod_status if cod_status is not None else None,
                                cod_produto if cod_produto is not None else None,
                                int(quantidade) if str(quantidade).strip() else None,
                                data_status, descricao or None, int(id_edit)
                            )
                        )
                        st.success("Atualizado.")
                    except Exception as e:
                        st.error(f"Erro: {e}")
    with colC:
        if st.button("🗑️ Excluir", key="atu_bt_excluir"):
            if not id_edit.strip():
                st.error("Informe o ID para excluir.")
            else:
                try:
                    execute("DELETE FROM atualizacoes WHERE id=%s", (int(id_edit),))
                    st.success("Excluído. (cod_status da dependência pode ser atualizado pelo trigger)")
                except Exception as e:
                    st.error(f"Erro: {e}")
