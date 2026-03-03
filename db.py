import os
import pymysql
from typing import Optional
import streamlit as st
from pymysql.err import OperationalError

# Ajustes de ambiente (padrão robusto em 127.0.0.1)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "DitecPR_9905"),
    "database": os.getenv("DB_NAME", "telefonia"),
    "charset": "utf8mb4",
    "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
    "read_timeout": int(os.getenv("DB_READ_TIMEOUT", "30")),
    "write_timeout": int(os.getenv("DB_WRITE_TIMEOUT", "30")),
}

RETRIABLE_ERRORS = (2006, 2013, 2014, 2055)  # server gone, lost conn, out-of-sync, lost at handshake

@st.cache_resource(show_spinner=False)
def _conn_factory():
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=DB_CONFIG["connect_timeout"],
        read_timeout=DB_CONFIG["read_timeout"],
        write_timeout=DB_CONFIG["write_timeout"],
    )

def _reset_conn():
    try:
        st.cache_resource.clear()
    except Exception:
        pass

def get_conn():
    """Retorna uma conexão válida; se a cacheada morreu, reconecta."""
    conn = _conn_factory()
    try:
        conn.ping(reconnect=True)   # verifica e reconecta se necessário
        return conn
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        _reset_conn()
        conn = _conn_factory()
        conn.ping(reconnect=True)
        return conn

def _run(sql: str, params: Optional[tuple], fetch: str):
    """Executa SQL com 1 retry em erros de conexão."""
    for attempt in (1, 2):
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                if fetch == "all":
                    return cur.fetchall()
                if fetch == "one":
                    return cur.fetchone()
                return cur.lastrowid or cur.rowcount
        except OperationalError as e:
            if getattr(e, "args", None) and e.args and e.args[0] in RETRIABLE_ERRORS and attempt == 1:
                _reset_conn()
                continue
            raise

def fetch_all(sql: str, params: Optional[tuple] = None):
    return _run(sql, params, "all")

def fetch_one(sql: str, params: Optional[tuple] = None):
    return _run(sql, params, "one")

def execute(sql: str, params: Optional[tuple] = None) -> int:
    return _run(sql, params, "exec")
