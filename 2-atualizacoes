import streamlit as st
import pandas as pd
from db import fetch_all, execute

# ---------------------- Page config ----------------------
st.set_page_config(page_title="Atualizações", page_icon="📈", layout="wide")

# ---------------------- State ----------------------
if "atu_open_modal" not in st.session_state:
    st.session_state["atu_open_modal"] = False

def _fechar_modal():
    st.session_state["atu_open_modal"] = False

# ---------------------- Visual / CSS ----------------------
st.markdown(
    """
<style>
/* ---- Layout base ---- */
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
div[data-testid="stToolbar"] { visibility: hidden; height: 0px; }
section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* ---- Header ---- */
.app-header{
  display:flex; align-items:center; justify-content:space-between;
  padding: .9rem 1rem; border: 1px solid rgba(49,51,63,.15);
  border-radius: 16px; background: rgba(255,255,255,.6);
  backdrop-filter: blur(6px);
  margin-bottom: 1rem;
}
.app-title{ display:flex; align-items:center; gap:.6rem; }
.app-title h1{ font-size:1.25rem; margin:0; }
.app-sub{ color: rgba(49,51,63,.7); font-size:.9rem; margin-top:.1rem; }

/* ---- Cards ---- */
.card{
  border: 1px solid rgba(49,51,63,.15);
  border-radius: 16px;
  background: rgba(255,255,255,.65);
  padding: 1rem 1rem .8rem 1rem;
}
.card + .card{ margin-top: .9rem; }
.card-title{ font-weight:700; font-size:1rem; margin-bottom:.6rem; }

/* ---- Badges ---- */
.dep-badge {
  display:inline-flex; align-items:center; gap:.55rem;
  padding:.35rem .65rem;
  border-radius: 999px;
  background:#eef6ff; color:#0f3c73; border:1px solid #cfe6ff;
  white-space:nowrap; max-width:100%; overflow:hidden; text-overflow:ellipsis;
  font-weight:650;
}
.dep-badge .code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.dep-badge.bad { background:#fff2f0; color:#8a120e; border-color:#ffd1cc; }

/* ---- Inputs ---- */
.stTextInput > div > div > input,
.stNumberInput input,
.stTextArea textarea { border-radius: 12px !important; }

.stTextInput > div > div > input { height: 2.2rem; padding:.25rem .6rem; }
.stSelectbox > div > div { border-radius: 12px !important; }
.stDateInput > div > div { border-radius: 12px !important; }

/* ---- Buttons ---- */
.stButton > button, .stFormSubmitButton > button{
  border-radius: 12px !important;
  padding:.45rem .7rem;
}

/* ---- Dataframe ---- */
div[data-testid="stDataFrame"]{
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(49,51,63,.15);
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------- Header ----------------------
st.markdown(
    """
<div class="app-header">
  <div class="app-title">
    <div style="font-size:1.35rem;">📈</div>
    <div>
      <h1>Atualizações</h1>
      <div class="app-sub">Histórico de status • inclusão, consulta e manutenção</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------- Select helpers ----------------------
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

# ---------------------- Dependências cache ----------------------
@st.cache_data(ttl=300, show_spinner=False)
def cache_dependencias():
    rows = fetch_all(
        "SELECT prefixo, subordinada, nome FROM dependencia ORDER BY prefixo, subordinada"
    )
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["prefixo", "subordinada", "nome"])

    df["prefixo"] = df["prefixo"].astype(str).str.strip()
    df["subordinada"] = df["subordinada"].astype(str).str.strip()
    df["nome"] = df["nome"].astype(str).fillna("").str.strip()

    key_set = set(zip(df["prefixo"], df["subordinada"]))
    lookup_nome = {(p, s): n for p, s, n in zip(df["prefixo"], df["subordinada"], df["nome"])}

    options = [
        f"{p}-{s} — {n}" if n else f"{p}-{s}"
        for p, s, n in zip(df["prefixo"], df["subordinada"], df["nome"])
    ]
    display_map = {opt: (p, s) for opt, p, s in zip(options, df["prefixo"], df["subordinada"])}

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

# ---------------------- Carregar registro p/ edição ----------------------
@st.cache_data(ttl=120, show_spinner=False)
def load_atualizacao_by_id(_id: int):
    rows = fetch_all(
        """
        SELECT id, prefixo, subordinada, cod_status, cod_produto, quantidade, data_status, descricao
        FROM atualizacoes
        WHERE id=%s
        """,
        (_id,),
    )
    return rows[0] if rows else None

def label_from_code(code, options: list[str]):
    if code is None:
        return "(vazio)"
    prefix = f"{int(code)} -"
    for opt in options:
        if opt.startswith(prefix):
            return opt
    return "(vazio)"

def carregar_para_edicao(_id: int):
    row = load_atualizacao_by_id(int(_id))
    if not row:
        st.toast("ID não encontrado.", icon="⚠️")
        return

    st.session_state["atu_ed_id"] = str(row["id"])
    st.session_state["atu_ed_prefixo"] = str(row["prefixo"]).strip()
    st.session_state["atu_ed_sub"] = str(row["subordinada"]).strip()
    st.session_state["atu_ed_qtde"] = "" if row["quantidade"] is None else str(row["quantidade"])
    st.session_state["atu_ed_desc"] = "" if row["descricao"] is None else str(row["descricao"])

    st.session_state["atu_ed_data"] = (
        pd.to_datetime(row["data_status"]).date() if row["data_status"] else None
    )

    st_opts, _ = load_status_for_select()
    p_opts, _ = load_produtos_for_select()
    st.session_state["atu_ed_status_label"] = label_from_code(row["cod_status"], st_opts)
    st.session_state["atu_ed_prod_label"] = label_from_code(row["cod_produto"], p_opts)

    st.toast("Carregado no formulário de edição. Abra a aba ✏️ Editar.", icon="✅")

# ---------------------- Modal (dialog) ----------------------
@st.dialog("🔍 Buscar dependência", width="large")
def abrir_busca_dependencia():
    df, _, _, _, display_map = cache_dependencias()

    q = st.text_input(
        "Pesquisar por Prefixo, Subordinada ou Nome",
        placeholder="Ex.: 0080, 00, PETRÓPOLIS",
        key="atu_inc_q",
    )
    colf1, colf2 = st.columns([1, 1])
    with colf1:
        pref_match = st.checkbox("Prefixo começa com", value=True)
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
    opts = [
        f"{p}-{s} — {n}" if n else f"{p}-{s}"
        for p, s, n in zip(df_view["prefixo"], df_view["subordinada"], df_view["nome"])
    ]

    sel = st.selectbox(
        "Resultados",
        options=opts if opts else ["(nenhum encontrado)"],
        index=0 if opts else None,
        placeholder="Digite para filtrar",
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("✅ Selecionar e aplicar", use_container_width=True):
            if sel and sel in display_map:
                pfx, sub = display_map[sel]
                st.session_state["atu_inc_prefixo"] = pfx
                st.session_state["atu_inc_sub"] = sub
                st.session_state["atu_open_modal"] = False
                st.toast(f"Selecionado: {pfx}-{sub}", icon="🔎")
                st.rerun()
    with c2:
        if st.button("✖️ Fechar", use_container_width=True):
            st.session_state["atu_open_modal"] = False
            st.rerun()

# ---------------------- Tabs ----------------------
aba_incluir, aba_listar, aba_editar = st.tabs(["➕ Incluir", "📋 Listar", "✏️ Editar"])

# ================================= INCLUIR =================================
with aba_incluir:
    st.markdown('<div class="card"><div class="card-title">Inclusão</div>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns([1, 1, 0.28, 3], vertical_alignment="bottom")
    with r1:
        st.caption("Prefixo (4)")
        sel_prefixo = st.text_input(
            "",
            key="atu_inc_prefixo",
            max_chars=4,
            label_visibility="collapsed",
            placeholder="0000",
            on_change=_fechar_modal,
        )

    with r2:
        st.caption("Subordinada (2)")
        sel_sub = st.text_input(
            "",
            key="atu_inc_sub",
            max_chars=2,
            label_visibility="collapsed",
            placeholder="00",
            on_change=_fechar_modal,
        )

    with r3:
        st.caption(" ")
        if st.button("🔍", key="atu_inc_btn_lupa", help="Buscar dependência", use_container_width=True):
            st.session_state["atu_open_modal"] = True

    with r4:
        st.caption(" ")
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

    if st.session_state.get("atu_open_modal"):
        abrir_busca_dependencia()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">Detalhes do status</div>', unsafe_allow_html=True)
    with st.form("atu_form_incluir", clear_on_submit=True):
        c1b, c2b, c3b = st.columns(3)

        with c1b:
            st_opts, st_map = load_status_for_select()
            st_label = st.selectbox("Status", options=st_opts, index=0, key="atu_inc_status_label")
            cod_status = st_map.get(st_label)

        with c2b:
            prod_opts, prod_map = load_produtos_for_select()
            prod_label = st.selectbox("Produto", options=prod_opts, index=0, key="atu_inc_prod_label")
            cod_produto = prod_map.get(prod_label)

        with c3b:
            quantidade = st.text_input("Quantidade", key="atu_inc_qtde", placeholder="Ex.: 10")

        dt = st.date_input("Data do status", value=None, format="DD/MM/YYYY", key="atu_inc_data")
        data_status = dt.isoformat() if dt else None

        descricao = st.text_area("Descrição", key="atu_inc_desc", placeholder="Detalhe do que mudou / observações...")

        b1, b2, _ = st.columns([1, 1, 6])
        with b1:
            salvar = st.form_submit_button("💾 Salvar", use_container_width=True)
        with b2:
            st.form_submit_button("↩️ Limpar", use_container_width=True)

        if salvar:
            if not sel_prefixo or not sel_sub:
                st.error("Informe Prefixo e Subordinada, ou use a busca para selecionar uma dependência.")
            else:
                if not dependencia_existe(sel_prefixo, sel_sub):
                    st.error("Dependência não encontrada. Cadastre primeiro em 📌 Dependências (mesmo prefixo/subordinada).")
                else:
                    try:
                        execute(
                            """
                            INSERT INTO atualizacoes
                            (prefixo, subordinada, cod_status, cod_produto, quantidade, data_status, descricao)
                            VALUES (%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                sel_prefixo.strip(),
                                sel_sub.strip(),
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

    st.markdown("</div>", unsafe_allow_html=True)

# ================================= LISTAR =================================
with aba_listar:
    st.markdown('<div class="card"><div class="card-title">Filtros</div>', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns([1, 1, 1, 2])
    with f1:
        f_prefixo = st.text_input("Prefixo (4)", max_chars=4, key="atu_f_prefixo", placeholder="0000")
    with f2:
        f_sub = st.text_input("Subordinada (2)", max_chars=2, key="atu_f_sub", placeholder="00")
    with f3:
        f_status = st.text_input("Código do status", key="atu_f_status", placeholder="Ex.: 1")
    with f4:
        prod_opts, prod_map = load_produtos_for_select()
        f_prod_label = st.selectbox("Produto", options=prod_opts, index=0, key="atu_f_prod_label")

    f_prod_codigo = prod_map.get(f_prod_label)

    a1, a2, _ = st.columns([1, 1, 6])
    with a1:
        st.button("🔎 Aplicar filtros", use_container_width=True)  # rerun natural
    with a2:
        if st.button("🧹 Limpar filtros", use_container_width=True):
            for k in ["atu_f_prefixo", "atu_f_sub", "atu_f_status", "atu_f_prod_label"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

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
    df = pd.DataFrame(rows)

    st.markdown('<div class="card"><div class="card-title">Resultados</div>', unsafe_allow_html=True)
    st.caption(f"{len(df):,} registro(s)")

    sel_id = None

    if df.empty:
        st.info("Nenhum registro para exibir.")
    else:
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
        )

        rows_sel = event.selection.rows if event and hasattr(event, "selection") else []
        if rows_sel:
            i = rows_sel[0]
            sel_id = int(df.iloc[i]["id"])

    cA, cB, _ = st.columns([1.2, 1, 7])
    with cA:
        if st.button("➡️ Carregar no Editar", use_container_width=True, disabled=(sel_id is None)):
            carregar_para_edicao(sel_id)
    with cB:
        if sel_id is not None:
            st.write(f"Selecionado: **ID {sel_id}**")

    st.markdown("</div>", unsafe_allow_html=True)

# ================================= EDITAR =================================
with aba_editar:
    st.markdown('<div class="card"><div class="card-title">Manutenção</div>', unsafe_allow_html=True)

    id_edit = st.text_input("ID", key="atu_ed_id", placeholder="Ex.: 123")

    r1, r2, r3, r4 = st.columns([1, 1, 0.28, 3], vertical_alignment="bottom")
    with r1:
        st.caption("Prefixo (4)")
        prefixo = st.text_input("", max_chars=4, key="atu_ed_prefixo", label_visibility="collapsed", placeholder="0000")
    with r2:
        st.caption("Subordinada (2)")
        subordinada = st.text_input("", max_chars=2, key="atu_ed_sub", label_visibility="collapsed", placeholder="00")
    with r3:
        st.caption(" ")
        st.button("🔍", type="secondary", disabled=True, use_container_width=True)
    with r4:
        st.caption(" ")
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
        quantidade = st.text_input("Quantidade", key="atu_ed_qtde", placeholder="Ex.: 10")
        dt = st.date_input("Data do status", value=None, format="DD/MM/YYYY", key="atu_ed_data")

    data_status = dt.isoformat() if dt else None
    descricao = st.text_area("Descrição", key="atu_ed_desc")

    colA, colB, _ = st.columns([1, 1, 9], gap="small")
    with colA:
        if st.button("💾 Atualizar", key="atu_bt_atualizar", use_container_width=True):
            if not id_edit.strip():
                st.error("Informe o ID para atualizar.")
            else:
                if not dependencia_existe(prefixo, subordinada):
                    st.error("Dependência não encontrada. Ajuste prefixo/subordinada ou cadastre em 📌 Dependências.")
                else:
                    try:
                        execute(
                            """
                            UPDATE atualizacoes
                            SET prefixo=%s, subordinada=%s, cod_status=%s, cod_produto=%s,
                                quantidade=%s, data_status=%s, descricao=%s
                            WHERE id=%s
                            """,
                            (
                                prefixo.strip(),
                                subordinada.strip(),
                                cod_status if cod_status is not None else None,
                                cod_produto if cod_produto is not None else None,
                                int(quantidade) if str(quantidade).strip() else None,
                                data_status,
                                descricao or None,
                                int(id_edit),
                            ),
                        )
                        st.success("Atualizado.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    with colB:
        if st.button("🗑️ Excluir", key="atu_bt_excluir", use_container_width=True):
            if not id_edit.strip():
                st.error("Informe o ID para excluir.")
            else:
                try:
                    execute("DELETE FROM atualizacoes WHERE id=%s", (int(id_edit),))
                    st.success("Excluído.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
