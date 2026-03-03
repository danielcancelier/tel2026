import streamlit as st
import pandas as pd
from db import fetch_all, fetch_one, execute
from utils import text_input_nullable, number_input_nullable
from typing import Optional, Dict, Any

st.set_page_config(page_title="Dependências", page_icon="📌", layout="wide")
st.title("📌 Dependências")

# ---------------------- Utilidades de exibição ----------------------
def _fmt(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return "—"
    return str(v)

# ---------------------- Cache de listas auxiliares ----------------------
@st.cache_data(ttl=300, show_spinner=False)
def cache_status():
    rows = fetch_all("SELECT codigo, descricao FROM status ORDER BY codigo")
    df = pd.DataFrame(rows)
    d = {int(r['codigo']): r['descricao'] for r in rows}
    return df, d

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
           ramais_controle, ramais_manter, pendencias, observacoes, cod_status, lote
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
                cod_status=%s, lote=%s
            WHERE prefixo=%s AND subordinada=%s
        """
        params = (
            payload.get("nome"), payload.get("uor"), payload.get("condominio"),
            payload.get("cod_condominio"), payload.get("linha_necessaria"),
            payload.get("contato_matricula"), payload.get("contato_nome"),
            payload.get("contato_obs"), payload.get("tem_central_pvv"),
            payload.get("ramais_controle"), payload.get("ramais_manter"),
            payload.get("pendencias"), payload.get("observacoes"),
            payload.get("cod_status"), payload.get("lote"),
            payload.get("prefixo"), payload.get("subordinada"),
        )
        execute(sql, params)
    else:
        sql = """
            INSERT INTO dependencia (
                prefixo, subordinada, nome, uor, condominio, cod_condominio,
                linha_necessaria, contato_matricula, contato_nome, contato_obs,
                tem_central_pvv, ramais_controle, ramais_manter, pendencias,
                observacoes, cod_status, lote
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
            payload.get("observacoes"), payload.get("cod_status"), payload.get("lote"),
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

    sql = (
        "SELECT prefixo, subordinada, nome, uor, cod_condominio, "
        "ramais_controle, ramais_manter, cod_status, lote FROM dependencia WHERE 1=1"
    )
    params = []
    if f_prefixo.strip():
        sql += " AND prefixo=%s"; params.append(f_prefixo.strip())
    if f_sub.strip():
        sql += " AND subordinada=%s"; params.append(f_sub.strip())
    if f_lote.strip():
        try:
            params.append(int(f_lote.strip()))
            sql += " AND lote=%s"
        except ValueError:
            st.warning("Lote precisa ser numérico.")
    sql += " ORDER BY prefixo, subordinada"

    rows = fetch_all(sql, tuple(params))
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# -------------------------------- INCLUIR -----------------------------------
with aba_incluir:
    st.subheader("Inclusão de Dependência")

    c_key1, c_key2 = st.columns([1, 1])
    with c_key1:
        prefixo_inc = st.text_input("Prefixo (4)", max_chars=4, key="dep_inc_prefixo", placeholder="0000")
    with c_key2:
        subordinada_inc = st.text_input("Subordinada (2)", max_chars=2, key="dep_inc_subordinada", placeholder="00")

    st.caption("Preencha os demais campos abaixo e clique em 💾 Salvar para incluir.")

    c1, c2, c3 = st.columns(3)
    with c1:
        # Sub-linha: Condomínio?  | Código do condomínio
        sc1, sc2 = st.columns([1,1])
        with sc1:
            condominio_opt_inc = st.selectbox("Condomínio?", ["(vazio)", "Sim", "Não"], index=0, key="dep_inc_condominio")
            condominio_inc = None if condominio_opt_inc == "(vazio)" else (True if condominio_opt_inc == "Sim" else False)
        with sc2:
            if condominio_opt_inc == "Sim":
                cod_condominio_inc = text_input_nullable("Código do condomínio", key="dep_inc_cod_condominio")
            else:
                cod_condominio_inc = None

        uor_inc = number_input_nullable("UOR", key="dep_inc_uor")
        contato_matricula_inc = text_input_nullable("Contato - Matrícula (8)", key="dep_inc_contato_matricula", max_chars=8)
        ramais_controle_inc = number_input_nullable("Ramais - Controle", key="dep_inc_ramais_controle")

        df_status, d_status = cache_status()
        sel_status_inc = st.selectbox("Status", ["(vazio)"] + [f"{c} - {d_status[c]}" for c in d_status], index=0, key="dep_inc_status")
        cod_status_inc = None if sel_status_inc == "(vazio)" else int(sel_status_inc.split(" - ")[0])

        lote_inc = number_input_nullable("Lote", key="dep_inc_lote")

    with c2:
        linha_necessaria_opt_inc = st.selectbox("Linha necessária?", ["(vazio)", "Sim", "Não"], index=0, key="dep_inc_linha_necessaria")
        linha_necessaria_inc = None if linha_necessaria_opt_inc == "(vazio)" else (True if linha_necessaria_opt_inc == "Sim" else False)

        tem_central_pvv_opt_inc = st.selectbox("Tem central PVV?", ["(vazio)", "Sim", "Não"], index=0, key="dep_inc_tem_central_pvv")
        tem_central_pvv_inc = None if tem_central_pvv_opt_inc == "(vazio)" else (True if tem_central_pvv_opt_inc == "Sim" else False)

        ramais_manter_inc = number_input_nullable("Ramais - Manter", key="dep_inc_ramais_manter")

    with c3:
        nome_inc = text_input_nullable("Nome da Dependência", key="dep_inc_nome")
        contato_nome_inc = text_input_nullable("Contato - Nome", key="dep_inc_contato_nome")
        contato_obs_inc = text_input_nullable("Contato - Observações", key="dep_inc_contato_obs")

        pendencias_txt_inc = st.text_area("Pendências", key="dep_inc_pendencias", height=120)
        observacoes_txt_inc = st.text_area("Observações", key="dep_inc_observacoes", height=120)

        pendencias_inc = None if (pendencias_txt_inc or "").strip() == "" else pendencias_txt_inc
        observacoes_inc = None if (observacoes_txt_inc or "").strip() == "" else observacoes_txt_inc

    colA, colB = st.columns([1,1])
    with colA:
        if st.button("💾 Salvar", key="dep_inc_bt_salvar"):
            if not prefixo_inc or not subordinada_inc:
                st.error("Informe prefixo e subordinada.")
            else:
                exists = load_dependencia(prefixo_inc, subordinada_inc) is not None
                if exists:
                    st.error("Já existe dependência com este Prefixo/Subordinada. Use ✏️ Editar.")
                else:
                    payload = {
                        'prefixo': prefixo_inc, 'subordinada': subordinada_inc,
                        'nome': nome_inc,
                        'uor': uor_inc, 'condominio': condominio_inc, 'cod_condominio': cod_condominio_inc,
                        'linha_necessaria': linha_necessaria_inc,
                        'contato_matricula': st.session_state.get('dep_inc_contato_matricula'),
                        'contato_nome': st.session_state.get('dep_inc_contato_nome'),
                        'contato_obs': st.session_state.get('dep_inc_contato_obs'),
                        'tem_central_pvv': tem_central_pvv_inc,
                        'ramais_controle': ramais_controle_inc, 'ramais_manter': ramais_manter_inc,
                        'pendencias': pendencias_inc, 'observacoes': observacoes_inc,
                        'cod_status': cod_status_inc, 'lote': lote_inc,
                    }
                    try:
                        save_dependencia(payload, is_update=False)
                        st.success("Registro incluído.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro ao incluir: {e}")
    with colB:
        if st.button("🧹 Limpar", key="dep_inc_bt_limpar"):
            for k in list(st.session_state.keys()):
                if k.startswith('dep_inc_'):
                    del st.session_state[k]
            st.rerun()

# -------------------------------- EDITAR  -----------------------------------
with aba_editar:
    st.subheader("Manutenção de Dependência")
    # --- Cabeçalho de seleção (alinhado como no 1-Comunicação) ---

    # --- Cabeçalho de seleção (2 linhas como no 1-Comunicação) ---

    # Linha 1: apenas rótulos
    l1, l2, l3, l4 = st.columns([1, 1, 0.3, 3])
    with l1:
        st.caption("Prefixo (4)")
    with l2:
        st.caption("Subordinada (2)")
    with l3:
        st.caption("\u00A0")
    with l4:
        st.caption("\u00A0")

    # Linha 2: widgets (inputs, botão, badge)
    c1, c2, c3, c4 = st.columns([1, 1, 0.3, 3])
    with c1:
        prefixo_ed = st.text_input(
            "", max_chars=4, key="dep_ed_prefixo",
            label_visibility="collapsed", placeholder="0000"
        )
    with c2:
        subordinada_ed = st.text_input(
            "", max_chars=2, key="dep_ed_subordinada",
            label_visibility="collapsed", placeholder="00"
        )
    with c3:
        # Lupa na segunda linha (como em 1-Comunicação)
        if st.button("🔍", key="dep_ed_btn_lupa", help="Buscar dependência"):
            # Aqui você pode acionar um modal/diálogo de busca no futuro, se desejar
            pass
    with c4:
        # Badge do nome (mostra na 2ª linha, na área larga)
        lookup = cache_lookup_nomes()
        if (prefixo_ed and len(prefixo_ed.strip()) == 4) and (subordinada_ed and len(subordinada_ed.strip()) == 2):
            nome_badge = lookup.get((prefixo_ed.strip(), subordinada_ed.strip()))
            if nome_badge:
                st.markdown(f"\n🏷️ **{prefixo_ed}-{subordinada_ed} — {nome_badge}**\n")
            else:
                st.markdown(f"\n❓ **{prefixo_ed}-{subordinada_ed} — não encontrada**\n")

    st.markdown("---")

    data = None
    if prefixo_ed and subordinada_ed and len(prefixo_ed.strip())==4 and len(subordinada_ed.strip())==2:
        data = load_dependencia(prefixo_ed.strip(), subordinada_ed.strip())

    if not data:
        st.info("Informe Prefixo (4) e Subordinada (2) válidos para consultar/editar os dados na tela.")
    else:
        df_status, d_status = cache_status()
        status_options = ["(vazio)"] + [f"{c} - {d_status[c]}" for c in d_status]
        status_initial = "(vazio)" if data.get('cod_status') is None else f"{int(data.get('cod_status'))} - {d_status.get(int(data.get('cod_status')), '—')}"

        # Linha 1
        r1c1, r1c2, r1c3 = st.columns([1,1,2])
        with r1c1:
            st.text_input("Prefixo", value=_fmt(data.get('prefixo')), key="dep_vw_prefixo", disabled=True)
        with r1c2:
            st.text_input("Subordinada", value=_fmt(data.get('subordinada')), key="dep_vw_subordinada", disabled=True)
        with r1c3:
            st.text_input("Nome da Dependência", value=_fmt(data.get('nome')), key="dep_vw_nome")

        # Linha 2
        r2c1, r2c2, r2c3 = st.columns([1,1,1])
        with r2c1:
            st.text_input("UOR", value=_fmt(data.get('uor')), key="dep_vw_uor")
        with r2c2:
            st.text_input("Lote", value=_fmt(data.get('lote')), key="dep_vw_lote")
        with r2c3:
            st.selectbox(
                "Status",
                status_options,
                index=status_options.index(status_initial) if status_initial in status_options else 0,
                key="dep_vw_status"
            )

        # Linha 3
        r3c1, r3c2, r3c3 = st.columns([1,1,1])
        with r3c1:
            cond_str = "(vazio)" if data.get('condominio') is None else ("Sim" if data.get('condominio') else "Não")
            st.selectbox("Condomínio?", ["(vazio)", "Sim", "Não"], index=["(vazio)","Sim","Não"].index(cond_str), key="dep_vw_condominio")
        with r3c2:
            st.text_input("Código do condomínio", value=_fmt(data.get('cod_condominio')), key="dep_vw_cod_cond")
        with r3c3:
            linha_str = "(vazio)" if data.get('linha_necessaria') is None else ("Sim" if data.get('linha_necessaria') else "Não")
            st.selectbox("Linha necessária?", ["(vazio)", "Sim", "Não"], index=["(vazio)","Sim","Não"].index(linha_str), key="dep_vw_linha")

        # Linha 4
        r4c1, r4c2, r4c3 = st.columns([1,1,1])
        with r4c1:
            pvv_str = "(vazio)" if data.get('tem_central_pvv') is None else ("Sim" if data.get('tem_central_pvv') else "Não")
            st.selectbox("Tem central PVV?", ["(vazio)", "Sim", "Não"], index=["(vazio)","Sim","Não"].index(pvv_str), key="dep_vw_pvv")
        with r4c2:
            st.text_input("Ramais - Controle", value=_fmt(data.get('ramais_controle')), key="dep_vw_ram_ctrl")
        with r4c3:
            st.text_input("Ramais - Manter", value=_fmt(data.get('ramais_manter')), key="dep_vw_ram_manter")

        # Linha 5
        r5c1, r5c2 = st.columns([1,2])
        with r5c1:
            st.text_input("Contato - Matrícula", value=_fmt(data.get('contato_matricula')), key="dep_vw_cont_matr")
            st.text_input("Contato - Nome", value=_fmt(data.get('contato_nome')), key="dep_vw_cont_nome")
        with r5c2:
            st.text_area("Contato - Observações", value=_fmt(data.get('contato_obs')), height=86, key="dep_vw_cont_obs")

        # Linha 6
        st.text_area("Pendências", value=_fmt(data.get('pendencias')), height=110, key="dep_vw_pend")
        st.text_area("Observações", value=_fmt(data.get('observacoes')), height=110, key="dep_vw_obs")

        # --- Rodapé de ações (Salvar / Recarregar) ---
        colA, colB, colC = st.columns([1,1,2])
        with colA:
            salvar_clicked = st.button("💾 Salvar alterações", key="dep_ed_btn_salvar")
        with colB:
            descartar_clicked = st.button("↩️ Recarregar", key="dep_ed_btn_descartar", help="Descarta edições e recarrega do banco")

        def _to_bool(opt: str):
            if opt == "(vazio)":
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

        if descartar_clicked:
            st.rerun()

        if salvar_clicked:
            # Converte seleção de status "código - descrição" em inteiro
            dep_status_sel = st.session_state.get("dep_vw_status", "(vazio)")
            cod_status = None
            if dep_status_sel != "(vazio)":
                try:
                    cod_status = int(dep_status_sel.split(" - ")[0].strip())
                except:
                    cod_status = None

            # Monta payload a partir dos campos da UI (convertendo "—" -> None)
            payload = {
                "prefixo": (st.session_state.get("dep_vw_prefixo") or "").replace("—","").strip() or None,
                "subordinada": (st.session_state.get("dep_vw_subordinada") or "").replace("—","").strip() or None,
                "nome": (st.session_state.get("dep_vw_nome") or "").strip() or None,
                "uor": _to_int_or_none(st.session_state.get("dep_vw_uor")),
                "condominio": _to_bool(st.session_state.get("dep_vw_condominio")),
                "cod_condominio": (st.session_state.get("dep_vw_cod_cond") or "").strip() or None,
                "linha_necessaria": _to_bool(st.session_state.get("dep_vw_linha")),
                "contato_matricula": (st.session_state.get("dep_vw_cont_matr") or "").strip() or None,
                "contato_nome": (st.session_state.get("dep_vw_cont_nome") or "").strip() or None,
                "contato_obs": (st.session_state.get("dep_vw_cont_obs") or "").strip() or None,
                "tem_central_pvv": _to_bool(st.session_state.get("dep_vw_pvv")),
                "ramais_controle": _to_int_or_none(st.session_state.get("dep_vw_ram_ctrl")),
                "ramais_manter": _to_int_or_none(st.session_state.get("dep_vw_ram_manter")),
                "pendencias": (st.session_state.get("dep_vw_pend") or "").strip() or None,
                "observacoes": (st.session_state.get("dep_vw_obs") or "").strip() or None,
                "cod_status": cod_status,
                "lote": _to_int_or_none(st.session_state.get("dep_vw_lote")),
            }

            # Validações essenciais
            errs = []
            if not payload["prefixo"] or len(payload["prefixo"]) != 4:
                errs.append("Prefixo deve ter 4 caracteres.")
            if not payload["subordinada"] or len(payload["subordinada"]) != 2:
                errs.append("Subordinada deve ter 2 caracteres.")
            mat = payload["contato_matricula"]
            #if mat and len(mat) != 8:
            #    errs.append("Contato - Matrícula deve ter 8 dígitos.")
            if payload["condominio"] is True and not payload["cod_condominio"]:
                errs.append("Quando 'Condomínio?' = Sim, o 'Código do condomínio' é obrigatório.")

            if errs:
                for e in errs:
                    st.error(e)
            else:
                try:
                    # Atualiza o registro existente
                    save_dependencia(payload, is_update=True)
                    st.success("Alterações salvas com sucesso.")
                    st.cache_data.clear()  # limpa caches (status/lookup)
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")