import streamlit as st

st.set_page_config(page_title="Teste Layout Horizontal", layout="wide")
st.title("Teste Layout Horizontal")

with st.form("form_linha"):
    # Linha 1: labels
    l1, l2, l3, l4 = st.columns([1, 1, 0.3, 3])
    with l1:
        st.caption("Campo 1 (4 chars)")
    with l2:
        st.caption("Campo 2 (2 chars)")
    with l3:
        st.caption("\u00A0")
    with l4:
        st.caption("\u00A0")

    # Linha 2: widgets
    c1, c2, c3, c4 = st.columns([1, 1, 0.3, 3])

    with c1:
        v1 = st.text_input(
            "",
            max_chars=4,
            label_visibility="collapsed",
            placeholder="0000"
        )

    with c2:
        v2 = st.text_input(
            "",
            value="00",          # 👈 valor padrão
            max_chars=2,
            label_visibility="collapsed"
        )

    with c3:
        enviar = st.form_submit_button("🔍")

    with c4:
        st.write("")
        if enviar:
            st.markdown(f"**Você digitou:** `{v1}` | `{v2}`")
        else:
            st.caption("Digite e clique na lupa.")
