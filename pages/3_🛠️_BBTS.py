
import streamlit as st
import pandas as pd
from datetime import date, datetime
from typing import Optional
from db import fetch_all, execute

st.set_page_config(page_title="BBTS", page_icon="🛠️", layout="wide")
st.title("🛠️ BBTS")

# ---------------------- Estado do modal (busca) ----------------------
if 'bbts_open_modal' not in st.session_state:
    st.session_state['bbts_open_modal'] = False
# Ao entrar na página, garanta fechado; só a lupa abre
st.session_state['bbts_open_modal'] = False

# ---------------------- Utilitários de data ----------------------
def date_to_iso(d: Optional[date]) -> Optional[str]:
    """Converte date (ou None) para string ISO 'YYYY-MM-DD' (ou None)."""
    return d.isoformat() if d else None

def fmt_br(x) -> str:
    """Formata data (string/objeto) como DD/MM/YYYY; retorna '' se vazio/nulo."""
    if x in (None, "", "0001-01-01"):
        return ""
    if isinstance(x, (datetime, date)):
        return x.strftime("%d/%m/%Y")
    try:
        return datetime.strptime(str(x), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(x)

# ---------------------- Cache de dependências ----------------------
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
    display_map = {opt: (p, s) for opt, p, s in zip(options, df["prefixo"], df["subordinada"])}
    return df, key_set, lookup_nome, options, display_map

def dependencia_existe(prefixo: str, subordinada: str) -> bool:
    if not prefixo or not subordinada:
        return False
    _, key_set, _, _, _ = cache_dependencias()
    return (prefixo.strip(), subordinada.strip()) in key_set

def nome_da_dependencia(prefixo: str, subordinada: str):
    if not prefixo or not subordinada:
        return None
    _, _, lookup_nome, _, _ = cache_dependencias()
    return lookup_nome.get((prefixo.strip(), subordinada.strip()))

# ---- helpers para estado do modal ----
def _fechar_modal():
    st.session_state['bbts_open_modal'] = False

# -------------------------------- Modal de busca --------------------------------
@st.dialog("🔍 Buscar dependência", width="large")
def abrir_busca_dependencia():
    df, _, _, options, display_map = cache_dependencias()

    q = st.text_input(
        "Pesquisar por Prefixo, Subordinada ou Nome",
        placeholder="Ex.: 0080, 00, PETROPOLIS",
        key="bbts_inc_q",
    )
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
                st.session_state['bbts_inc_prefixo'] = pfx
                st.session_state['bbts_inc_sub'] = sub
                st.session_state['bbts_open_modal'] = False
                st.toast(f"Selecionado: {pfx}-{sub}", icon="🔎")
                st.rerun()
    with c2:
        if st.button("✖️ Fechar", use_container_width=True):
            st.session_state['bbts_open_modal'] = False
            st.rerun()

# --------------------------- ABAS ---------------------------
aba_incluir, aba_listar, aba_editar = st.tabs(["➕ Incluir", "📋 Listar", "✏️ Editar"])

# -------------------------------- INCLUIR -----------------------------------
with aba_incluir:
    st.subheader("Inclusão")

    # Linha 1: labels
    l1, l2, l3, l4 = st.columns([1, 1, 0.3, 3])
    with l1: st.caption("Prefixo (4)")
    with l2: st.caption("Subordinada (2)")
    with l3: st.caption("\u00A0")
    with l4: st.caption("\u00A0")

    # Linha 2: widgets (fora do form)
    c1, c2, c3, c4 = st.columns([1, 1, 0.3, 3])
    with c1:
        sel_prefixo = st.text_input(
            "",
            key="bbts_inc_prefixo",
            max_chars=4,
            label_visibility="collapsed",
            placeholder="0000",
            on_change=_fechar_modal,
        )
    with c2:
        sel_sub = st.text_input(
            "",
            key="bbts_inc_sub",
            max_chars=2,
            label_visibility="collapsed",
            placeholder="00",
            on_change=_fechar_modal,
        )
    with c3:
        if st.button("🔍", key="bbts_inc_btn_lupa", help="Buscar dependência"):
            st.session_state['bbts_open_modal'] = True
    with c4:
        # badge do nome
        if (sel_prefixo and len(sel_prefixo.strip()) == 4) and (sel_sub and len(sel_sub.strip()) == 2):
            _nome = nome_da_dependencia(sel_prefixo, sel_sub)
            if _nome:
                st.markdown(f"\n🏷️ {sel_prefixo}-{sel_sub} — {_nome}\n", unsafe_allow_html=True)
            else:
                st.markdown(f"\n❓ {sel_prefixo}-{sel_sub} — não encontrada\n", unsafe_allow_html=True)

    if st.session_state.get('bbts_open_modal'):
        abrir_busca_dependencia()

    # ===== Demais campos + botão – DENTRO do form =====
    with st.form("bbts_form_incluir", clear_on_submit=True):
        c1b, c2b = st.columns(2)
        with c1b:
            sgt_chamado = st.text_input("SGT Chamado", key="bbts_inc_chamado")
            dt_chamado = st.date_input("Data do chamado", value=None, format="DD/MM/YYYY", key="bbts_inc_data_chamado")
            data_chamado = date_to_iso(dt_chamado)
        with c2b:
            sgt_quant_ramais = st.text_input("Quantidade de ramais (num)", key="bbts_inc_qtde")
            email_cat_bbts = st.text_input("E-mail CAT BBTS", key="bbts_inc_email")
        descricao_os = st.text_area("Descrição da OS", key="bbts_inc_desc")

        salvar = st.form_submit_button("💾 Salvar")
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
                            INSERT INTO bbts (prefixo, subordinada, sgt_chamado, data_chamado, descricao_os, sgt_quant_ramais, email_cat_bbts)
                            VALUES (%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                sel_prefixo.strip(),
                                sel_sub.strip(),
                                sgt_chamado or None,
                                data_chamado,
                                descricao_os or None,
                                int(sgt_quant_ramais) if sgt_quant_ramais.strip() else None,
                                email_cat_bbts or None,
                            ),
                        )
                        st.toast("Incluído com sucesso!", icon="✅")
                        st.cache_data.clear()
                    except Exception as e:
                        st.toast(f"Erro ao incluir: {e}", icon="❌")

# -------------------------------- LISTAR -----------------------------------
with aba_listar:
    with st.expander("Filtros", expanded=True):
        f_prefixo = st.text_input("Prefixo (4)", max_chars=4, key="bbts_f_prefixo")
        f_sub = st.text_input("Subordinada (2)", max_chars=2, key="bbts_f_sub")
        f_chamado = st.text_input("SGT Chamado contém", key="bbts_f_chamado")

        sql = (
            "SELECT id, prefixo, subordinada, sgt_chamado, data_chamado, sgt_quant_ramais, email_cat_bbts "
            "FROM bbts WHERE 1=1"
        )
        params = []
        if f_prefixo.strip():
            sql += " AND prefixo=%s"; params.append(f_prefixo.strip())
        if f_sub.strip():
            sql += " AND subordinada=%s"; params.append(f_sub.strip())
        if f_chamado.strip():
            sql += " AND sgt_chamado LIKE %s"; params.append(f"%{f_chamado.strip()}%")
        sql += " ORDER BY COALESCE(data_chamado, '0001-01-01') DESC, id DESC"

    rows = fetch_all(sql, tuple(params))
    df = pd.DataFrame(rows)
    if not df.empty:
        if "data_chamado" in df.columns:
            df["data_chamado"] = df["data_chamado"].apply(fmt_br)
    st.dataframe(df, use_container_width=True)

# -------------------------------- EDITAR -----------------------------------
with aba_editar:
    st.subheader("Manutenção")

    id_edit = st.text_input("ID", key="bbts_ed_id")

    # Linha compacta coerente com a de Incluir
    e1, e2, e3, e4 = st.columns([1, 1, 0.3, 3])
    with e1:
        st.caption("Prefixo (4)")
        prefixo = st.text_input("", max_chars=4, key="bbts_ed_prefixo", label_visibility="collapsed", placeholder="0000")
    with e2:
        st.caption("Subordinada (2)")
        subordinada = st.text_input("", max_chars=2, key="bbts_ed_sub", label_visibility="collapsed", placeholder="00")
    with e3:
        st.caption("\u00A0")
        st.button("🔍", key="bbts_ed_btn_dummy", type="secondary", disabled=True)
    with e4:
        st.caption("\u00A0")
        if (prefixo and len(prefixo.strip()) == 4) and (subordinada and len(subordinada.strip()) == 2):
            _nome = nome_da_dependencia(prefixo, subordinada)
            if _nome:
                st.markdown(f"\n🏷️ {prefixo}-{subordinada} — {_nome}\n", unsafe_allow_html=True)
            else:
                st.markdown(f"\n❓ {prefixo}-{subordinada} — não encontrada\n", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        sgt_chamado_ed = st.text_input("SGT Chamado", key="bbts_ed_chamado")
        dt_chamado_ed = st.date_input("Data do chamado", value=None, format="DD/MM/YYYY", key="bbts_ed_data_chamado")
        data_chamado_ed = date_to_iso(dt_chamado_ed)
        descricao_os_ed = st.text_area("Descrição da OS", key="bbts_ed_desc")
    with c2:
        sgt_quant_ramais_ed = st.text_input("Quantidade de ramais (num)", key="bbts_ed_qtde")
        email_cat_bbts_ed = st.text_input("E-mail CAT BBTS", key="bbts_ed_email")

    colA, colB, _ = st.columns([1, 1, 9], gap="small")
    with colA:
        if st.button("💾 Atualizar", key="bbts_bt_atualizar"):
            if not id_edit.strip():
                st.error("Informe o ID para atualizar.")
            else:
                if not dependencia_existe(prefixo, subordinada):
                    st.error("Dependência não encontrada. Ajuste prefixo/subordinada ou cadastre em 📌 Dependências.")
                else:
                    try:
                        execute(
                            """
                            UPDATE bbts
                            SET prefixo=%s, subordinada=%s, sgt_chamado=%s, data_chamado=%s,
                                descricao_os=%s, sgt_quant_ramais=%s, email_cat_bbts=%s
                            WHERE id=%s
                            """,
                            (
                                prefixo.strip(),
                                subordinada.strip(),
                                sgt_chamado_ed or None,
                                data_chamado_ed,
                                descricao_os_ed or None,
                                int(sgt_quant_ramais_ed) if sgt_quant_ramais_ed.strip() else None,
                                email_cat_bbts_ed or None,
                                int(id_edit),
                            ),
                        )
                        st.success("Atualizado.")
                    except Exception as e:
                        st.error(f"Erro: {e}")
    with colB:
        if st.button("🗑️ Excluir", key="bbts_bt_excluir"):
            if not id_edit.strip():
                st.error("Informe o ID para excluir.")
            else:
                try:
                    execute("DELETE FROM bbts WHERE id=%s", (int(id_edit),))
                    st.success("Excluído")
                except Exception as e:
                    st.error(f"Erro: {e}")
