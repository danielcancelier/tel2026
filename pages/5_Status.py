import streamlit as st
import pandas as pd
from db import fetch_all, execute

st.set_page_config(page_title="Status", page_icon="🔢", layout="wide")
st.title("🔢 Status")

COLS = ["codigo", "descricao", "finaliza_ciclo"]

@st.cache_data(show_spinner=False)
def carregar_df():
    rows = fetch_all("SELECT codigo, descricao, finaliza_ciclo FROM status ORDER BY codigo")
    df = pd.DataFrame(rows, columns=COLS)
    if not df.empty:
        df["codigo"] = pd.to_numeric(df["codigo"], errors="coerce").astype('Int64')
        # normaliza descricao (None quando vazio)
        df["descricao"] = df["descricao"].where(df["descricao"].notna(), None)
        # converte finaliza_ciclo para boolean (False por padrão)
        df["finaliza_ciclo"] = df["finaliza_ciclo"].fillna(0).astype(bool)
    else:
        df = pd.DataFrame(columns=COLS)
        df["codigo"] = df["codigo"].astype('Int64')
        df["finaliza_ciclo"] = df.get("finaliza_ciclo", pd.Series([], dtype=bool))
    return df

def normalizar_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().reindex(columns=COLS)
    out["codigo"] = pd.to_numeric(out["codigo"], errors="coerce").astype('Int64')
    out["descricao"] = out["descricao"].replace({"": None})
    out["finaliza_ciclo"] = out["finaliza_ciclo"].fillna(False).astype(bool)
    return out


def diff_status(df_atual: pd.DataFrame, df_novo: pd.DataFrame):
    a = df_atual.set_index("codigo", drop=True)
    n = df_novo.set_index("codigo", drop=True)

    cods_atual = set(a.index.dropna())
    cods_novo = set(n.index.dropna())

    inserir = sorted(list(cods_novo - cods_atual))
    excluir = sorted(list(cods_atual - cods_novo))

    atualizar = []
    for k in sorted(cods_novo & cods_atual):
        # comparar descricao
        desc_a = None if (k not in a.index or pd.isna(a.loc[k, "descricao"])) else a.loc[k, "descricao"]
        desc_n = None if (k not in n.index or pd.isna(n.loc[k, "descricao"])) else n.loc[k, "descricao"]
        # comparar finaliza_ciclo (como bool)
        fin_a = bool(a.loc[k, "finaliza_ciclo"]) if k in a.index else False
        fin_n = bool(n.loc[k, "finaliza_ciclo"]) if k in n.index else False
        if desc_a != desc_n or fin_a != fin_n:
            atualizar.append(k)

    df_ins = n.loc[inserir, ["descricao", "finaliza_ciclo"]].reset_index() if inserir else pd.DataFrame(columns=COLS)
    df_upd = n.loc[atualizar, ["descricao", "finaliza_ciclo"]].reset_index() if atualizar else pd.DataFrame(columns=COLS)
    df_del = pd.DataFrame({"codigo": excluir}) if excluir else pd.DataFrame(columns=["codigo"]) 
    return df_ins, df_upd, df_del

base_df = carregar_df()

col_config = {
    "codigo": st.column_config.NumberColumn(
        "Código (PK)",
        format="%d",
        step=1,
        required=True,
    ),
    "descricao": st.column_config.TextColumn(
        "Descrição",
        max_chars=200,
    ),
    "finaliza_ciclo": st.column_config.CheckboxColumn(
        "Finaliza ciclo?",
        help="Quando marcado, este status indica conclusão do ciclo.",
        default=False,
    ),
}

edited_df = st.data_editor(
    base_df,
    column_config=col_config,
    hide_index=True,
    width="stretch",
    num_rows="dynamic",
    key="status_editor",
)


def validar_df(df: pd.DataFrame) -> list[str]:
    msgs = []
    if df.empty:
        return msgs
    if df["codigo"].isna().any():
        msgs.append("Existem linhas com Código vazio.")
    if (~df["codigo"].isna() & (df["codigo"] < 0)).any():
        msgs.append("Há códigos negativos — informe inteiros positivos.")
    cods = df["codigo"].dropna().astype(int)
    dups = cods[cods.duplicated()].unique().tolist()
    if dups:
        msgs.append(f"Códigos duplicados: {', '.join(map(str, dups))}.")
    return msgs

btn_salvar = st.button("Salvar alterações")
if btn_salvar:
    df_novo = normalizar_df(edited_df)
    erros = validar_df(df_novo)
    if erros:
        for m in erros:
            st.error(m)
    else:
        df_ins, df_upd, df_del = diff_status(base_df, df_novo)
        total_ops = len(df_ins) + len(df_upd) + len(df_del)
        if total_ops == 0:
            st.info("Nenhuma alteração a salvar.")
        else:
            try:
                for _, row in df_ins.iterrows():
                    execute(
                        "INSERT INTO status (codigo, descricao, finaliza_ciclo) VALUES (%s, %s, %s)",
                        (int(row["codigo"]), row["descricao"], bool(row["finaliza_ciclo"]))
                    )
                for _, row in df_upd.iterrows():
                    execute(
                        "UPDATE status SET descricao=%s, finaliza_ciclo=%s WHERE codigo=%s",
                        (row["descricao"], bool(row["finaliza_ciclo"]), int(row["codigo"]))
                    )
                for _, row in df_del.iterrows():
                    execute("DELETE FROM status WHERE codigo=%s", (int(row["codigo"]),))
            except Exception as e:
                st.error(f"Erro ao salvar alterações: {e}")
            else:
                st.success(
                    f"Alterações salvas. Inseridos: {len(df_ins)} · Atualizados: {len(df_upd)} · Excluídos: {len(df_del)}"
                )
                st.cache_data.clear()
