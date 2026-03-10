import streamlit as st
import pandas as pd
import altair as alt
from db import fetch_all, fetch_one
from datetime import date, timedelta

# ------------------------------------------------------------------------------
# Configuração da página
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="SQUAD 1290 • Dashboard",
    page_icon="📊",
    layout="wide",
)
st.title("📊 Dashboard de Progresso – SQUAD 1290")

# ------------------------------------------------------------------------------
# Helpers de carga e cache
# ------------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def load_status_lookup():
    # inclui finaliza_ciclo para usar na visão de 'ciclos de produto'
    rows = fetch_all("SELECT codigo, descricao, finaliza_ciclo FROM status ORDER BY codigo")
    # dicionários auxiliares
    lut_desc = {r["codigo"]: (r["descricao"] or "Sem descrição") for r in rows}
    lut_finaliza = {r["codigo"]: bool(r["finaliza_ciclo"]) for r in rows}
    return lut_desc, lut_finaliza

@st.cache_data(ttl=60, show_spinner=False)
def load_dependencias():
    sql = """
    SELECT d.prefixo,
           d.subordinada,
           d.cod_status,
           d.lote,
           d.concluido,
           s.descricao AS status_desc
    FROM dependencia d
    LEFT JOIN status s ON s.codigo = d.cod_status
    """
    return pd.DataFrame(fetch_all(sql))

@st.cache_data(ttl=60, show_spinner=False)
def load_atualizacoes_all():
    sql = """
    SELECT a.prefixo,
           a.subordinada,
           a.cod_produto,
           p.descricao AS produto,
           a.cod_status,
           s.descricao AS status_desc,
           s.finaliza_ciclo,
           a.quantidade,
           a.data_status
    FROM atualizacoes a
    LEFT JOIN status s   ON s.codigo = a.cod_status
    LEFT JOIN produtos p ON p.codigo = a.cod_produto
    """
    return pd.DataFrame(fetch_all(sql))

@st.cache_data(ttl=60, show_spinner=False)
def load_atualizacoes_last_per_dep_prod():
    # Último registro por (dependência, produto) usando MAX(data_status)
    sql = """
    SELECT a.prefixo,
           a.subordinada,
           a.cod_produto,
           p.descricao AS produto,
           a.cod_status,
           s.descricao AS status_desc,
           s.finaliza_ciclo,
           a.quantidade,
           a.data_status
    FROM atualizacoes a
    JOIN (
        SELECT prefixo, subordinada, cod_produto, MAX(data_status) AS maxdt
        FROM atualizacoes
        GROUP BY prefixo, subordinada, cod_produto
    ) last
      ON a.prefixo=last.prefixo
     AND a.subordinada=last.subordinada
     AND a.cod_produto=last.cod_produto
     AND a.data_status=last.maxdt
    LEFT JOIN status s   ON s.codigo = a.cod_status
    LEFT JOIN produtos p ON p.codigo = a.cod_produto
    """
    return pd.DataFrame(fetch_all(sql))

# ------------------------------------------------------------------------------
# Carrega dados
# ------------------------------------------------------------------------------
status_lut_desc, status_lut_finaliza = load_status_lookup()
df_dep     = load_dependencias()
df_at_all  = load_atualizacoes_all()
df_at_last = load_atualizacoes_last_per_dep_prod()

# Segurança contra DataFrames vazios
for df in (df_dep, df_at_all, df_at_last):
    if df.empty:
        pass

# ------------------------------------------------------------------------------
# Sidebar – filtros e parâmetros
# ------------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configurações")
    st.subheader("🎯 Alvo")
    alvo_total = st.number_input(
        "Total de dependências (alvo)",
        min_value=1, max_value=100_000, value=4000, step=100,
        help="Usado para calcular % de progresso geral."
    )

    st.subheader("📦 Visão de atualizações")
    modo_at = st.radio(
        "Como agregar `atualizacoes`?",
        options=["Todos os registros", "Último por dependência/produto"],
        help="A segunda opção considera apenas o registro mais recente por (dependência, produto)."
    )

# ------------------------------------------------------------------------------
# KPIs principais
# ------------------------------------------------------------------------------
# 👉 Regra: conclusão de DEPENDÊNCIA é dada por dependencia.concluido (bool)
#           (não depende mais de 'descrições de status')

total_dep = int(len(df_dep))
if "concluido" in df_dep.columns and not df_dep.empty:
    dep_concluidas = int(df_dep["concluido"].fillna(0).astype(bool).sum())
else:
    dep_concluidas = 0

pct_dep = (dep_concluidas / alvo_total * 100.0) if alvo_total else 0.0

# Atualizações recentes (últimos 7 dias) – independente de finalização
hoje = date.today()
janela = hoje - timedelta(days=7)
recentes = 0
if not df_at_all.empty:
    recentes = int(
        df_at_all.loc[
            df_at_all["data_status"].notna() &
            (pd.to_datetime(df_at_all["data_status"], errors="coerce") >= pd.to_datetime(janela))
        ].shape[0]
    )

col1, col2, col3, col4 = st.columns(4)
col1.metric("Dependências (no BD)", f"{total_dep:,}")
col2.metric("Concluídas (dep.)", f"{dep_concluidas:,}")
col3.metric("Progresso (dep. / alvo)", f"{pct_dep:,.1f}%")
col4.metric("Atualizações (últimos 7 dias)", f"{recentes:,}")

st.caption(
    "KPIs calculados a partir das tabelas `dependencia` (usando o campo **concluido**) e `atualizacoes`/`status` (para ciclos de produto)."
)

# ------------------------------------------------------------------------------
# Abas de visualização
# ------------------------------------------------------------------------------
tab_dep, tab_at, tab_time = st.tabs(["📍 Dependências", "🧾 Atualizações", "⏱️ Evolução temporal"])

# === Aba Dependências =========================================================
with tab_dep:
    st.subheader("Distribuição de status (Dependências)")
    if not df_dep.empty:
        df_dep_plot = (
            df_dep.assign(status_desc=lambda d: d["status_desc"].fillna("Sem status"))
                  .groupby("status_desc", as_index=False)
                  .size()
                  .rename(columns={"size": "total"})
        )
        df_dep_plot["pct"] = df_dep_plot["total"] / max(alvo_total, 1) * 100

        chart_dep = alt.Chart(df_dep_plot).mark_arc(innerRadius=60).encode(
            theta=alt.Theta(field="total", type="quantitative"),
            color=alt.Color("status_desc:N", legend=alt.Legend(title="Status")),
            tooltip=[
                alt.Tooltip("status_desc:N", title="Status"),
                alt.Tooltip("total:Q", title="Qtde", format=",.0f"),
                alt.Tooltip("pct:Q", title="% do alvo", format=",.1f"),
            ],
        ).properties(height=320)
        st.altair_chart(chart_dep, use_container_width=True)

        st.subheader("Status por lote (100% stacked)")
        if "lote" in df_dep.columns and df_dep["lote"].notna().any():
            df_lote = (
                df_dep.assign(
                    status_desc=lambda d: d["status_desc"].fillna("Sem status"),
                    lote=lambda d: d["lote"].fillna(0).astype(int),
                )
                .groupby(["lote", "status_desc"], as_index=False)
                .size()
            )
            # normalização por lote
            df_tot_lote = (
                df_lote.groupby("lote", as_index=False)["size"].sum().rename(columns={"size": "tot_lote"})
            )
            df_lote = df_lote.merge(df_tot_lote, on="lote")
            df_lote["pct"] = df_lote["size"] / df_lote["tot_lote"]

            chart_lote = alt.Chart(df_lote).mark_bar().encode(
                x=alt.X("lote:N", title="Lote"),
                y=alt.Y("pct:Q", title="% no lote", stack="normalize", axis=alt.Axis(format="%")),
                color=alt.Color("status_desc:N", legend=alt.Legend(title="Status")),
                tooltip=[
                    alt.Tooltip("lote:N", title="Lote"),
                    alt.Tooltip("status_desc:N", title="Status"),
                    alt.Tooltip("size:Q", title="Qtde", format=",.0f"),
                    alt.Tooltip("pct:Q", title="% (lote)", format=".1%"),
                ],
            ).properties(height=360)
            st.altair_chart(chart_lote, use_container_width=True)
        else:
            st.info("Não há dados de lote para exibir.")
    else:
        st.warning("Não encontrei registros em `dependencia`.")

# === Aba Atualizações =========================================================
with tab_at:
    st.subheader(f"Distribuição de status — {modo_at}")

    df_src = df_at_last if modo_at == "Último por dependência/produto" else df_at_all
    if not df_src.empty:
        df_src = df_src.assign(
            status_desc=lambda d: d["status_desc"].fillna("Sem status"),
            produto=lambda d: d["produto"].fillna("Sem produto"),
            finaliza_ciclo=lambda d: d["finaliza_ciclo"].fillna(0).astype(bool),
        )

        colA, colB = st.columns([1, 1])
        with colA:
            st.caption("Por status")
            df_by_status = df_src.groupby("status_desc", as_index=False).size().rename(columns={"size": "total"})
            chart_stat = alt.Chart(df_by_status).mark_arc(innerRadius=60).encode(
                theta="total:Q",
                color=alt.Color("status_desc:N", legend=alt.Legend(title="Status")),
                tooltip=[
                    alt.Tooltip("status_desc:N", title="Status"),
                    alt.Tooltip("total:Q", title="Qtde", format=",.0f"),
                ],
            ).properties(height=320)
            st.altair_chart(chart_stat, use_container_width=True)

        with colB:
            st.caption("Top produtos por ciclos concluídos")
            # 👉 conclusão de CICLO DE PRODUTO é dada por status.finaliza_ciclo = 1
            df_conc = df_src[df_src["finaliza_ciclo"]]
            if not df_conc.empty:
                df_top = (
                    df_conc.groupby("produto", as_index=False)
                           .size().rename(columns={"size": "concluidos"})
                           .sort_values("concluidos", ascending=False)
                           .head(15)
                )
                chart_prod = alt.Chart(df_top).mark_bar().encode(
                    x=alt.X("concluidos:Q", title="Ciclos concluídos"),
                    y=alt.Y("produto:N", sort="-x", title="Produto"),
                    tooltip=[
                        alt.Tooltip("produto:N", title="Produto"),
                        alt.Tooltip("concluidos:Q", title="Qtde", format=",.0f"),
                    ],
                ).properties(height=360)
                st.altair_chart(chart_prod, use_container_width=True)
            else:
                st.info("Nenhum registro está em status que finaliza ciclo.")

        with st.expander("Tabela (amostra)"):
            st.dataframe(df_src.head(200), use_container_width=True)
    else:
        st.warning("Não encontrei registros em `atualizacoes`.")

# === Aba Evolução Temporal ====================================================
with tab_time:
    st.subheader("Evolução de ciclos concluídos no tempo")
    if not df_at_all.empty:
        tmp = df_at_all.copy()
        tmp["data_status"] = pd.to_datetime(tmp["data_status"], errors="coerce")
        tmp = tmp[tmp["data_status"].notna()]
        tmp["finaliza_ciclo"] = tmp["finaliza_ciclo"].fillna(0).astype(bool)

        di = (
            tmp[tmp["finaliza_ciclo"]]
               .groupby("data_status", as_index=False)
               .size()
               .sort_values("data_status")
        )
        if not di.empty:
            di["acum"] = di["size"].cumsum()
            chart_time = alt.Chart(di).mark_area(opacity=0.6).encode(
                x=alt.X("data_status:T", title="Data"),
                y=alt.Y("acum:Q", title="Acumulado (ciclos concluídos)"),
                tooltip=[
                    alt.Tooltip("data_status:T", title="Data"),
                    alt.Tooltip("size:Q", title="No dia", format=",.0f"),
                    alt.Tooltip("acum:Q", title="Acumulado", format=",.0f"),
                ],
            ).properties(height=380)
            st.altair_chart(chart_time, use_container_width=True)
        else:
            st.info("Não há atualizações com status que finaliza ciclo e data preenchida.")
    else:
        st.warning("Não encontrei registros em `atualizacoes`.")
