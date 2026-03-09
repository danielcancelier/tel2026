
import streamlit as st
import pandas as pd
from db import fetch_all, execute

st.set_page_config(page_title="Produtos", page_icon="🛒", layout="wide")
st.title("🛒 Produtos")

COLS = ["codigo", "descricao", "fornecedor"]

@st.cache_data(show_spinner=False)
def carregar_df():
    rows = fetch_all("SELECT codigo, descricao, fornecedor FROM produtos ORDER BY codigo")
    df = pd.DataFrame(rows, columns=COLS)
    if not df.empty:
        df["codigo"] = pd.to_numeric(df["codigo"], errors="coerce").astype('Int64')
        # normaliza strings vazias para None
        for c in ["descricao", "fornecedor"]:
            df[c] = df[c].where(df[c].notna(), None)
    else:
        df = pd.DataFrame(columns=COLS)
        df["codigo"] = df["codigo"].astype('Int64')
    return df

def normalizar_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().reindex(columns=COLS)
    out["codigo"] = pd.to_numeric(out["codigo"], errors="coerce").astype('Int64')
    for c in ["descricao", "fornecedor"]:
        out[c] = out[c].replace({"": None})
    return out

def diff_produtos(df_atual: pd.DataFrame, df_novo: pd.DataFrame):
    a = df_atual.set_index("codigo", drop=True)
    n = df_novo.set_index("codigo", drop=True)
    cods_atual = set(a.index.dropna())
    cods_novo = set(n.index.dropna())
    inserir = sorted(list(cods_novo - cods_atual))
    excluir = sorted(list(cods_atual - cods_novo))
    atualizar = []
    for k in sorted(cods_novo & cods_atual):
        # compara campo a campo; considera None ~ NaN equivalentes
        def norm(v):
            return None if (pd.isna(v) or v == "") else v
        a_desc, a_forn = norm(a.loc[k, "descricao"]), norm(a.loc[k, "fornecedor"])
        n_desc, n_forn = norm(n.loc[k, "descricao"]), norm(n.loc[k, "fornecedor"])
        if a_desc != n_desc or a_forn != n_forn:
            atualizar.append(k)
    df_ins = n.loc[inserir, ["descricao", "fornecedor"]].reset_index() if inserir else pd.DataFrame(columns=COLS)
    df_upd = n.loc[atualizar, ["descricao", "fornecedor"]].reset_index() if atualizar else pd.DataFrame(columns=COLS)
    df_del = pd.DataFrame({"codigo": excluir}) if excluir else pd.DataFrame(columns=["codigo"])
    return df_ins, df_upd, df_del

# Carrega dados do banco
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
    "fornecedor": st.column_config.TextColumn(
        "Fornecedor",
        max_chars=200,
    ),
}

edited_df = st.data_editor(
    base_df,
    column_config=col_config,
    hide_index=True,
    width="stretch",
    num_rows="dynamic",
    key="produtos_editor",
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

# Botão simples abaixo da grade
btn_salvar = st.button("Salvar alterações")
if btn_salvar:
    df_novo = normalizar_df(edited_df)
    erros = validar_df(df_novo)
    if erros:
        for m in erros:
            st.error(m)
    else:
        df_ins, df_upd, df_del = diff_produtos(base_df, df_novo)
        total_ops = len(df_ins) + len(df_upd) + len(df_del)
        if total_ops == 0:
            st.info("Nenhuma alteração a salvar.")
        else:
            try:
                for _, row in df_ins.iterrows():
                    execute(
                        "INSERT INTO produtos (codigo, descricao, fornecedor) VALUES (%s, %s, %s)",
                        (int(row["codigo"]), row["descricao"], row["fornecedor"])  # campos podem ser None
                    )
                for _, row in df_upd.iterrows():
                    execute(
                        "UPDATE produtos SET descricao=%s, fornecedor=%s WHERE codigo=%s",
                        (row["descricao"], row["fornecedor"], int(row["codigo"]))
                    )
                for _, row in df_del.iterrows():
                    execute(
                        "DELETE FROM produtos WHERE codigo=%s",
                        (int(row["codigo"]),)
                    )
            except Exception as e:
                st.error(f"Erro ao salvar alterações: {e}")
            else:
                st.success(
                    f"Alterações salvas. Inseridos: {len(df_ins)} · Atualizados: {len(df_upd)} · Excluídos: {len(df_del)}"
                )
                st.cache_data.clear()
