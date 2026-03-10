import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple

from db import fetch_all, fetch_one, execute
from utils import text_input_nullable, number_input_nullable

st.set_page_config(page_title="Dependências", page_icon="🏦", layout="wide")
st.title("🏦 Dependências")

# =========================================================
# Helpers visuais / conversões
# =========================================================
def _fmt(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return ""
    return str(v)

def _to_bool_from_sim_nao(opt: str) -> Optional[bool]:
    if opt == "(vazio)":
        return None
    return True if opt == "Sim" else False

def _bool_to_sim_nao(v: Optional[bool]) -> str:
    if v is None:
        return "(vazio)"
    return "Sim" if v else "Não"

def _to_int_or_none(v) -> Optional[int]:
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        return None

def _norm_prefixo(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s != "" else None

def _norm_subordinada(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s != "" else None

def _status_label(codigo: Optional[int], mapa: Dict[int, Dict[str, Any]]) -> str:
    if codigo is None:
        return "(vazio)"
    meta = mapa.get(int(codigo))
    if not meta:
        return f"{codigo} - (não encontrado)"
    return f"{codigo} - {meta['descricao']}"

# =========================================================
# Cache de apoio
# =========================================================
@st.cache_data(ttl=300, show_spinner=False)
def cache_status():
    rows = fetch_all("""
        SELECT codigo, descricao, finaliza_ciclo
        FROM status
        ORDER BY codigo
    """)
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["codigo", "descricao", "finaliza_ciclo"])
    mapa = {
        int(r["codigo"]): {
            "descricao": r["descricao"],
            "finaliza_ciclo": bool(r["finaliza_ciclo"]),
        }
        for r in rows
    }
    return df, mapa

@st.cache_data(ttl=300, show_spinner=False)
def cache_lookup_dependencias():
    rows = fetch_all("""
        SELECT prefixo, subordinada, nome
        FROM dependencia
        ORDER BY prefixo, subordinada
    """)
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["prefixo", "subordinada", "nome"])
    df["prefixo"] = df["prefixo"].astype(str).str.strip()
    df["subordinada"] = df["subordinada"].astype(str).str.strip()
    df["nome"] = df["nome"].fillna("").astype(str).str.strip()
    lookup = {
        (r["prefixo"], r["subordinada"]): r["nome"]
        for _, r in df.iterrows()
    }
    return lookup

def clear_caches():
    st.cache_data.clear()

# =========================================================
# Acesso a dados
# =========================================================
def dependencia_existe(prefixo: str, subordinada: str) -> bool:
    row = fetch_one(
        "SELECT 1 AS ok FROM dependencia WHERE prefixo=%s AND subordinada=%s",
        (prefixo, subordinada),
    )
    return row is not None

def load_dependencia(prefixo: str, subordinada: str):
    sql = """
    SELECT
        prefixo, subordinada, nome, uor, cidade, uf,
        condominio, cod_condominio, linha_necessaria, tipo_ramal,
        contato_matricula, contato_nome, contato_obs,
        tem_central_pvv, ramais_controle, ramais_manter,
        pendencias, observacoes, cod_status, lote, concluido
    FROM dependencia
    WHERE prefixo=%s AND subordinada=%s
    """
    return fetch_one(sql, (prefixo, subordinada))

def insert_dependencia(payload: Dict[str, Any]):
    sql = """
    INSERT INTO dependencia (
        prefixo, subordinada, nome, uor, cidade, uf,
        condominio, cod_condominio, linha_necessaria, tipo_ramal,
        contato_matricula, contato_nome, contato_obs,
        tem_central_pvv, ramais_controle, ramais_manter,
        pendencias, observacoes, cod_status, lote, concluido
    ) VALUES (
        %s,%s,%s,%s,%s,%s,
        %s,%s,%s,%s,
        %s,%s,%s,
        %s,%s,%s,
        %s,%s,%s,%s,%s
    )
    """
    params = (
        payload.get("prefixo"),
        payload.get("subordinada"),
        payload.get("nome"),
        payload.get("uor"),
        payload.get("cidade"),
        payload.get("uf"),
        payload.get("condominio"),
        payload.get("cod_condominio"),
        payload.get("linha_necessaria"),
        payload.get("tipo_ramal"),
        payload.get("contato_matricula"),
        payload.get("contato_nome"),
        payload.get("contato_obs"),
        payload.get("tem_central_pvv"),
        payload.get("ramais_controle"),
        payload.get("ramais_manter"),
        payload.get("pendencias"),
        payload.get("observacoes"),
        payload.get("cod_status"),
        payload.get("lote"),
        payload.get("concluido"),
    )
    execute(sql, params)

def update_dependencia(payload: Dict[str, Any]):
    sql = """
    UPDATE dependencia SET
        nome=%s,
        uor=%s,
        cidade=%s,
        uf=%s,
        condominio=%s,
        cod_condominio=%s,
        linha_necessaria=%s,
        tipo_ramal=%s,
        contato_matricula=%s,
        contato_nome=%s,
        contato_obs=%s,
        tem_central_pvv=%s,
        ramais_controle=%s,
        ramais_manter=%s,
        pendencias=%s,
        observacoes=%s,
        cod_status=%s,
        lote=%s,
        concluido=%s
    WHERE prefixo=%s AND subordinada=%s
    """
    params = (
        payload.get("nome"),
        payload.get("uor"),
        payload.get("cidade"),
        payload.get("uf"),
        payload.get("condominio"),
        payload.get("cod_condominio"),
        payload.get("linha_necessaria"),
        payload.get("tipo_ramal"),
        payload.get("contato_matricula"),
        payload.get("contato_nome"),
        payload.get("contato_obs"),
        payload.get("tem_central_pvv"),
        payload.get("ramais_controle"),
        payload.get("ramais_manter"),
        payload.get("pendencias"),
        payload.get("observacoes"),
        payload.get("cod_status"),
        payload.get("lote"),
        payload.get("concluido"),
        payload.get("prefixo"),
        payload.get("subordinada"),
    )
    execute(sql, params)

def delete_dependencias(chaves: List[Tuple[str, str]]):
    for prefixo, subordinada in chaves:
        execute(
            "DELETE FROM dependencia WHERE prefixo=%s AND subordinada=%s",
            (prefixo, subordinada),
        )

def update_concluido_bulk(changes: List[Tuple[str, str, bool]]):
    for prefixo, subordinada, concluido in changes:
        execute(
            "UPDATE dependencia SET concluido=%s WHERE prefixo=%s AND subordinada=%s",
            (1 if concluido else 0, prefixo, subordinada),
        )

def query_dependencias_listagem(
    f_prefixo: str,
    f_subordinada: str,
    f_lote: str,
    f_status: Optional[int],
    f_situacao: str,
):
    sql = """
    SELECT
        d.prefixo,
        d.subordinada,
        d.nome,
        d.cidade,
        d.uf,
        d.uor,
        d.lote,
        d.cod_status,
        d.concluido
    FROM dependencia d
    WHERE 1=1
    """
    params: List[Any] = []

    if f_prefixo.strip():
        sql += " AND d.prefixo=%s"
        params.append(f_prefixo.strip())

    if f_subordinada.strip():
        sql += " AND d.subordinada=%s"
        params.append(f_subordinada.strip())

    if f_lote.strip():
        try:
            sql += " AND d.lote=%s"
            params.append(int(f_lote.strip()))
        except ValueError:
            st.warning("Lote precisa ser numérico.")

    if f_status is not None:
        sql += " AND d.cod_status=%s"
        params.append(int(f_status))

    if f_situacao == "Somente em aberto":
        sql += " AND COALESCE(d.concluido, 0)=0"
    elif f_situacao == "Somente concluídas":
        sql += " AND d.concluido=1"

    sql += " ORDER BY d.prefixo, d.subordinada"
    rows = fetch_all(sql, tuple(params))
    return pd.DataFrame(rows)

# =========================================================
# Regras / validações
# =========================================================
def validar_payload(payload: Dict[str, Any]) -> List[str]:
    errs = []

    prefixo = payload.get("prefixo")
    subordinada = payload.get("subordinada")
    cod_condominio = payload.get("cod_condominio")
    uf = payload.get("uf")

    if not prefixo or len(prefixo) != 4:
        errs.append("Prefixo deve ter 4 caracteres.")
    if not subordinada or len(subordinada) != 2:
        errs.append("Subordinada deve ter 2 caracteres.")
    if payload.get("condominio") is True and not cod_condominio:
        errs.append("Quando 'Condomínio?' = Sim, o 'Código do condomínio' é obrigatório.")
    if uf and len(uf) != 2:
        errs.append("UF deve ter 2 caracteres.")
    return errs

def render_status_coerencia(cod_status: Optional[int], concluido: bool, mapa_status: Dict[int, Dict[str, Any]]):
    if cod_status is None:
        if concluido:
            st.info("A dependência está marcada como concluída, porém sem status informado.")
        return

    meta = mapa_status.get(int(cod_status))
    if not meta:
        return

    finaliza = bool(meta["finaliza_ciclo"])
    desc = meta["descricao"]

    if finaliza and not concluido:
        st.warning(
            f"O status selecionado ('{desc}') está marcado como finalizador de ciclo, "
            f"mas a dependência ainda está com 'Concluído' = Não."
        )
    elif concluido and not finaliza:
        st.info(
            f"A dependência está concluída, mas o status selecionado ('{desc}') "
            f"não está marcado como finalizador. Isso é permitido, mas vale revisar a coerência."
        )
    elif finaliza and concluido:
        st.success("Status e conclusão estão coerentes entre si.")

# =========================================================
# Abas
# =========================================================
aba_incluir, aba_listar, aba_editar = st.tabs(["➕ Incluir", "📋 Listar", "✏️ Editar"])

df_status, mapa_status = cache_status()

status_options = ["(vazio)"] + [
    f"{int(r['codigo'])} - {r['descricao']}" + (" • finaliza ciclo" if bool(r["finaliza_ciclo"]) else "")
    for _, r in df_status.iterrows()
]

# =========================================================
# ABA INCLUIR
# =========================================================
with aba_incluir:
    st.subheader("Inclusão de dependência")

    with st.form("form_dep_incluir", clear_on_submit=False):
        c0a, c0b, c0c = st.columns([1, 1, 1.2])
        with c0a:
            prefixo = st.text_input("Prefixo (4)", max_chars=4, placeholder="0000")
        with c0b:
            subordinada = st.text_input("Subordinada (2)", max_chars=2, placeholder="00")
        with c0c:
            concluido = st.checkbox("Dependência concluída", value=False)

        c1, c2, c3 = st.columns(3)

        with c1:
            nome = text_input_nullable("Nome da dependência", key="dep_inc_nome")
            uor = number_input_nullable("UOR", key="dep_inc_uor")
            cidade = text_input_nullable("Cidade", key="dep_inc_cidade")
            uf = text_input_nullable("UF", key="dep_inc_uf", max_chars=2)
            lote = number_input_nullable("Lote", key="dep_inc_lote")

        with c2:
            condominio_opt = st.selectbox("Condomínio?", ["(vazio)", "Sim", "Não"], index=0)
            linha_necessaria_opt = st.selectbox("Linha necessária?", ["(vazio)", "Sim", "Não"], index=0)
            tem_central_pvv_opt = st.selectbox("Tem central PVV?", ["(vazio)", "Sim", "Não"], index=0)
            tipo_ramal = text_input_nullable("Tipo de ramal", key="dep_inc_tipo_ramal")
            cod_condominio = text_input_nullable("Código do condomínio", key="dep_inc_cod_condominio")

        with c3:
            contato_matricula = text_input_nullable("Contato - Matrícula", key="dep_inc_contato_matricula", max_chars=8)
            contato_nome = text_input_nullable("Contato - Nome", key="dep_inc_contato_nome")
            ramais_controle = number_input_nullable("Ramais - Controle", key="dep_inc_ramais_controle")
            ramais_manter = number_input_nullable("Ramais - Manter", key="dep_inc_ramais_manter")
            status_sel = st.selectbox("Status da dependência", status_options, index=0)

        pendencias = st.text_area("Pendências", height=110)
        observacoes = st.text_area("Observações", height=110)
        contato_obs = st.text_area("Contato - Observações", height=86)

        salvar = st.form_submit_button("💾 Salvar inclusão", use_container_width=True)

        cod_status = None
        if status_sel != "(vazio)":
            cod_status = int(status_sel.split(" - ")[0])

        render_status_coerencia(cod_status, concluido, mapa_status)

        if salvar:
            payload = {
                "prefixo": _norm_prefixo(prefixo),
                "subordinada": _norm_subordinada(subordinada),
                "nome": nome,
                "uor": uor,
                "cidade": cidade,
                "uf": (uf or "").strip().upper() or None,
                "condominio": _to_bool_from_sim_nao(condominio_opt),
                "cod_condominio": cod_condominio,
                "linha_necessaria": _to_bool_from_sim_nao(linha_necessaria_opt),
                "tipo_ramal": tipo_ramal,
                "contato_matricula": contato_matricula,
                "contato_nome": contato_nome,
                "contato_obs": (contato_obs or "").strip() or None,
                "tem_central_pvv": _to_bool_from_sim_nao(tem_central_pvv_opt),
                "ramais_controle": ramais_controle,
                "ramais_manter": ramais_manter,
                "pendencias": (pendencias or "").strip() or None,
                "observacoes": (observacoes or "").strip() or None,
                "cod_status": cod_status,
                "lote": lote,
                "concluido": bool(concluido),
            }

            errs = validar_payload(payload)
            if dependencia_existe(payload["prefixo"], payload["subordinada"]):
                errs.append("Já existe dependência com este prefixo/subordinada.")

            if errs:
                for e in errs:
                    st.error(e)
            else:
                try:
                    insert_dependencia(payload)
                    clear_caches()
                    st.success("Dependência incluída com sucesso.")
                except Exception as e:
                    st.error(f"Erro ao incluir: {e}")

# =========================================================
# ABA LISTAR
# =========================================================
with aba_listar:
    st.subheader("Listagem e ações em lote")

    with st.expander("Filtros", expanded=True):
        f1, f2, f3, f4, f5 = st.columns([1, 1, 1, 2, 1.4])
        with f1:
            f_prefixo = st.text_input("Prefixo", max_chars=4, key="dep_lst_prefixo")
        with f2:
            f_sub = st.text_input("Subordinada", max_chars=2, key="dep_lst_sub")
        with f3:
            f_lote = st.text_input("Lote", key="dep_lst_lote")
        with f4:
            st_status_options = ["(todos)"] + status_options[1:]
            f_status_sel = st.selectbox("Status", st_status_options, index=0, key="dep_lst_status")
        with f5:
            f_situacao = st.selectbox(
                "Situação",
                ["Todas", "Somente em aberto", "Somente concluídas"],
                index=0,
                key="dep_lst_situacao"
            )

    f_status = None
    if f_status_sel != "(todos)":
        f_status = int(f_status_sel.split(" - ")[0])

    df = query_dependencias_listagem(
        f_prefixo=f_prefixo,
        f_subordinada=f_sub,
        f_lote=f_lote,
        f_status=f_status,
        f_situacao=f_situacao,
    )

    if df.empty:
        st.info("Nenhuma dependência encontrada para os filtros informados.")
    else:
        df["status_desc"] = df["cod_status"].apply(lambda x: _status_label(x, mapa_status))
        df["concluido_atual"] = df["concluido"].fillna(False).astype(bool)
        df["novo_concluido"] = df["concluido_atual"]
        df["excluir"] = False

        editor_df = df[[
            "prefixo",
            "subordinada",
            "nome",
            "cidade",
            "uf",
            "uor",
            "lote",
            "status_desc",
            "concluido_atual",
            "novo_concluido",
            "excluir",
        ]].rename(columns={
            "prefixo": "Prefixo",
            "subordinada": "Subordinada",
            "nome": "Nome",
            "cidade": "Cidade",
            "uf": "UF",
            "uor": "UOR",
            "lote": "Lote",
            "status_desc": "Status",
            "concluido_atual": "Concluído atual",
            "novo_concluido": "Novo concluído",
            "excluir": "Excluir",
        })

        edited = st.data_editor(
            editor_df,
            use_container_width=True,
            hide_index=True,
            disabled=[
                "Prefixo", "Subordinada", "Nome", "Cidade", "UF", "UOR", "Lote", "Status", "Concluído atual"
            ],
            column_config={
                "Concluído atual": st.column_config.CheckboxColumn(disabled=True),
                "Novo concluído": st.column_config.CheckboxColumn(
                    help="Marque/desmarque o valor desejado e depois clique em 'Aplicar conclusão'."
                ),
                "Excluir": st.column_config.CheckboxColumn(
                    help="Selecione as linhas e depois clique em 'Excluir selecionadas'."
                ),
            },
            key="dep_list_editor",
        )

        a1, a2 = st.columns([1, 1])

        with a1:
            if st.button("✅ Aplicar conclusão", use_container_width=True, key="dep_bt_aplicar_conclusao"):
                changes: List[Tuple[str, str, bool]] = []

                for i, row in edited.iterrows():
                    concl_atual = bool(row["Concluído atual"])
                    novo_concl = bool(row["Novo concluído"])
                    if concl_atual != novo_concl:
                        changes.append((
                            str(row["Prefixo"]).strip(),
                            str(row["Subordinada"]).strip(),
                            novo_concl
                        ))

                if not changes:
                    st.info("Nenhuma alteração de conclusão foi identificada.")
                else:
                    try:
                        update_concluido_bulk(changes)
                        clear_caches()
                        st.success(f"{len(changes)} dependência(s) atualizada(s) com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao aplicar conclusão: {e}")

        with a2:
            if st.button("🗑️ Excluir selecionadas", use_container_width=True, key="dep_bt_excluir_lote"):
                keys_to_delete: List[Tuple[str, str]] = []

                for _, row in edited.iterrows():
                    if bool(row["Excluir"]):
                        keys_to_delete.append((
                            str(row["Prefixo"]).strip(),
                            str(row["Subordinada"]).strip(),
                        ))

                if not keys_to_delete:
                    st.info("Nenhuma dependência foi marcada para exclusão.")
                else:
                    try:
                        delete_dependencias(keys_to_delete)
                        clear_caches()
                        st.success(f"{len(keys_to_delete)} dependência(s) excluída(s) com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir dependências: {e}")

        st.caption(
            "A conclusão é aplicada apenas quando você clica em 'Aplicar conclusão'. "
            "Isso evita gravações acidentais ao apenas navegar ou editar visualmente a grade."
        )

# =========================================================
# ABA EDITAR
# =========================================================
with aba_editar:
    st.subheader("Edição individual")

    lookup = cache_lookup_dependencias()

    h1, h2, h3, h4 = st.columns([1, 1, 0.35, 3])
    with h1:
        prefixo_ed = st.text_input("Prefixo (4)", max_chars=4, key="dep_ed_prefixo", placeholder="0000")
    with h2:
        subordinada_ed = st.text_input("Subordinada (2)", max_chars=2, key="dep_ed_subordinada", placeholder="00")
    with h3:
        st.write("")
        st.write("")
        st.button("🔍", key="dep_ed_lupa", disabled=True)
    with h4:
        nome_badge = None
        if (prefixo_ed and len(prefixo_ed.strip()) == 4) and (subordinada_ed and len(subordinada_ed.strip()) == 2):
            nome_badge = lookup.get((prefixo_ed.strip(), subordinada_ed.strip()))
        if nome_badge:
            st.markdown(
                f"""
                <div style='padding:8px 10px;background:#F0F2F6;border-radius:8px;display:inline-block'>
                    🏷️ <b>{prefixo_ed.strip()}-{subordinada_ed.strip()}</b> — {nome_badge}
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif prefixo_ed.strip() and subordinada_ed.strip():
            st.markdown(
                f"""
                <div style='padding:8px 10px;background:#FFF3CD;border-radius:8px;display:inline-block'>
                    ❓ <b>{prefixo_ed.strip()}-{subordinada_ed.strip()}</b> — não encontrada
                </div>
                """,
                unsafe_allow_html=True,
            )

    data = None
    if (prefixo_ed and len(prefixo_ed.strip()) == 4) and (subordinada_ed and len(subordinada_ed.strip()) == 2):
        data = load_dependencia(prefixo_ed.strip(), subordinada_ed.strip())

    st.markdown("---")

    if not data:
        st.info("Informe prefixo e subordinada válidos para carregar uma dependência.")
    else:
        status_inicial = _status_label(data.get("cod_status"), mapa_status)
        if status_inicial not in status_options:
            status_inicial = "(vazio)"

        with st.form("form_dep_editar", clear_on_submit=False):
            l0a, l0b, l0c = st.columns([1, 1, 1.2])
            with l0a:
                st.text_input("Prefixo", value=_fmt(data.get("prefixo")), disabled=True)
            with l0b:
                st.text_input("Subordinada", value=_fmt(data.get("subordinada")), disabled=True)
            with l0c:
                concluido_ed = st.checkbox("Dependência concluída", value=bool(data.get("concluido")))

            c1, c2, c3 = st.columns(3)

            with c1:
                nome_ed = st.text_input("Nome da dependência", value=_fmt(data.get("nome")))
                uor_ed = st.text_input("UOR", value=_fmt(data.get("uor")))
                cidade_ed = st.text_input("Cidade", value=_fmt(data.get("cidade")))
                uf_ed = st.text_input("UF", value=_fmt(data.get("uf")), max_chars=2)
                lote_ed = st.text_input("Lote", value=_fmt(data.get("lote")))

            with c2:
                condominio_ed = st.selectbox(
                    "Condomínio?",
                    ["(vazio)", "Sim", "Não"],
                    index=["(vazio)", "Sim", "Não"].index(_bool_to_sim_nao(data.get("condominio")))
                )
                linha_necessaria_ed = st.selectbox(
                    "Linha necessária?",
                    ["(vazio)", "Sim", "Não"],
                    index=["(vazio)", "Sim", "Não"].index(_bool_to_sim_nao(data.get("linha_necessaria")))
                )
                tem_central_pvv_ed = st.selectbox(
                    "Tem central PVV?",
                    ["(vazio)", "Sim", "Não"],
                    index=["(vazio)", "Sim", "Não"].index(_bool_to_sim_nao(data.get("tem_central_pvv")))
                )
                tipo_ramal_ed = st.text_input("Tipo de ramal", value=_fmt(data.get("tipo_ramal")))
                cod_condominio_ed = st.text_input("Código do condomínio", value=_fmt(data.get("cod_condominio")))

            with c3:
                contato_matricula_ed = st.text_input("Contato - Matrícula", value=_fmt(data.get("contato_matricula")), max_chars=8)
                contato_nome_ed = st.text_input("Contato - Nome", value=_fmt(data.get("contato_nome")))
                ramais_controle_ed = st.text_input("Ramais - Controle", value=_fmt(data.get("ramais_controle")))
                ramais_manter_ed = st.text_input("Ramais - Manter", value=_fmt(data.get("ramais_manter")))
                status_sel_ed = st.selectbox(
                    "Status da dependência",
                    status_options,
                    index=status_options.index(status_inicial) if status_inicial in status_options else 0
                )

            pendencias_ed = st.text_area("Pendências", value=_fmt(data.get("pendencias")), height=110)
            observacoes_ed = st.text_area("Observações", value=_fmt(data.get("observacoes")), height=110)
            contato_obs_ed = st.text_area("Contato - Observações", value=_fmt(data.get("contato_obs")), height=86)

            salvar_ed = st.form_submit_button("💾 Salvar alterações", use_container_width=True)

            cod_status_ed = None
            if status_sel_ed != "(vazio)":
                cod_status_ed = int(status_sel_ed.split(" - ")[0])

            render_status_coerencia(cod_status_ed, concluido_ed, mapa_status)

            if salvar_ed:
                payload = {
                    "prefixo": data.get("prefixo"),
                    "subordinada": data.get("subordinada"),
                    "nome": (nome_ed or "").strip() or None,
                    "uor": _to_int_or_none(uor_ed),
                    "cidade": (cidade_ed or "").strip() or None,
                    "uf": (uf_ed or "").strip().upper() or None,
                    "condominio": _to_bool_from_sim_nao(condominio_ed),
                    "cod_condominio": (cod_condominio_ed or "").strip() or None,
                    "linha_necessaria": _to_bool_from_sim_nao(linha_necessaria_ed),
                    "tipo_ramal": (tipo_ramal_ed or "").strip() or None,
                    "contato_matricula": (contato_matricula_ed or "").strip() or None,
                    "contato_nome": (contato_nome_ed or "").strip() or None,
                    "contato_obs": (contato_obs_ed or "").strip() or None,
                    "tem_central_pvv": _to_bool_from_sim_nao(tem_central_pvv_ed),
                    "ramais_controle": _to_int_or_none(ramais_controle_ed),
                    "ramais_manter": _to_int_or_none(ramais_manter_ed),
                    "pendencias": (pendencias_ed or "").strip() or None,
                    "observacoes": (observacoes_ed or "").strip() or None,
                    "cod_status": cod_status_ed,
                    "lote": _to_int_or_none(lote_ed),
                    "concluido": bool(concluido_ed),
                }

                errs = validar_payload(payload)

                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    try:
                        update_dependencia(payload)
                        clear_caches()
                        st.success("Alterações salvas com sucesso.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar alterações: {e}")
