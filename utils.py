import streamlit as st
from typing import Optional

def to_int_or_none(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        return None

def to_str_or_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s if s != "" else None

def bool_selectbox(label: str, key: str, value: Optional[bool] = None):
    # 3 estados: None / True / False
    options = {"(vazio)": None, "Sim": True, "Não": False}
    inv = {v: k for k, v in options.items()}
    default = inv.get(value, "(vazio)")
    choice = st.selectbox(label, list(options.keys()), index=list(options.keys()).index(default), key=key)
    return options[choice]

def bool_to_label(v: Optional[bool]) -> str:
    return {True: "Sim", False: "Não", None: "(vazio)"}.get(v, "(vazio)")

def text_input_nullable(label: str, key: str, value: Optional[str] = None, max_chars: Optional[int] = None):
    v = st.text_input(label, value=value or "", key=key, max_chars=max_chars)
    return to_str_or_none(v)

def number_input_nullable(label: str, key: str, value: Optional[int] = None):
    # Use text_input para permitir vazio => None
    v = st.text_input(label, value="" if value is None else str(value), key=key)
    return to_int_or_none(v)

def two_cols():
    return st.columns(2)
