#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
importa_dependencias.py (versão para usar db.py / utils.py locais)

- Lê `predios_uor.csv` (separador ;) no diretório atual.
- Importa (UPSERT) na tabela `dependencia` usando a conexão do módulo local `db.py` (PyMySQL).
- Exibe andamento textual (linhas processadas, % e ETA) a cada N registros.

Requisitos do ambiente:
  - db.py e utils.py no mesmo diretório (já fornecidos) -> conexão via PyMySQL (autocommit=True)
  - Pacotes: PyMySQL (já usado em db.py)

Execução:
  python3 importa_dependencias.py

Parâmetros fixos (ajuste abaixo, se necessário):
  CSV_IN = 'predios_uor.csv'
  SEP = ';'
  BATCH = 500   # tamanho do commit/executemany e intervalo de progresso
"""

import os
import csv
import time
from datetime import timedelta

# Módulos locais (conexão/utilitários)
import db  # usa get_conn() e execute()/fetch helpers do seu projeto

CSV_IN = 'predios_uor.csv'
SEP = ';'
BATCH = 500

UPSERT_SQL = (
    """
    INSERT INTO dependencia (
        prefixo, subordinada, nome, uor, cidade, uf,
        condominio, cod_condominio, linha_necessaria, tipo_ramal, contato_matricula,
        contato_nome, contato_obs, tem_central_pvv, ramais_controle, ramais_manter,
        pendencias, observacoes, cod_status, lote
    ) VALUES (
        %(prefixo)s, %(subordinada)s, %(nome)s, %(uor)s, %(cidade)s, %(uf)s,
        NULL, %(cod_condominio)s, NULL, NULL, NULL,
        NULL, NULL, NULL, NULL, NULL,
        NULL, NULL, NULL, %(lote)s
    )
    ON DUPLICATE KEY UPDATE
        nome = VALUES(nome),
        uor = VALUES(uor),
        cidade = VALUES(cidade),
        uf = VALUES(uf),
        cod_condominio = VALUES(cod_condominio),
        lote = VALUES(lote)
    """
)


def human(n):
    return f"{n:,}".replace(',', '.')


def to_int_or_none(v):
    s = ('' if v is None else str(v)).strip()
    if s == '':
        return None
    try:
        return int(s)
    except Exception:
        return None


def normalize_row(row: dict) -> dict:
    """Mapeia e normaliza uma linha do CSV para o dicionário esperado pelo UPSERT."""
    prefixo = (row.get('prefixo') or '').strip().zfill(4)
    subordinada = (row.get('subordinada') or '').strip().zfill(2)
    nome = (row.get('nome_dependencia') or '').strip()[:120]
    uor = to_int_or_none(row.get('uor'))
    cidade = (row.get('nome_municipio') or '').strip()[:30]
    uf = (row.get('uf') or '').strip().upper()[:2]
    cod_condominio = (row.get('predio_nash') or '').strip()[:32]
    lote = to_int_or_none(row.get('lote'))
    return {
        'prefixo': prefixo,
        'subordinada': subordinada,
        'nome': nome,
        'uor': uor,
        'cidade': cidade,
        'uf': uf,
        'cod_condominio': cod_condominio,
        'lote': lote,
    }


def count_total_lines(path: str) -> int:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return max(sum(1 for _ in f) - 1, 0)
    except Exception:
        return 0


def main():
    if not os.path.exists(CSV_IN):
        print(f"Arquivo não encontrado: {CSV_IN}")
        return 2

    total = count_total_lines(CSV_IN)
    print(f"Importando de {CSV_IN} (sep='{SEP}')... Total estimado: {human(total)} linhas")

    conn = db.get_conn()  # conexão PyMySQL com autocommit=True (db.py)
    cur = conn.cursor()

    processed = 0
    t0 = time.time()
    batch = []

    try:
        with open(CSV_IN, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=SEP)
            for row in reader:
                batch.append(normalize_row(row))
                processed += 1

                if len(batch) >= BATCH:
                    cur.executemany(UPSERT_SQL, batch)
                    batch.clear()

                    # Progresso
                    if total:
                        pct = (processed / total) * 100.0
                        elapsed = time.time() - t0
                        rate = processed / max(elapsed, 1e-9)
                        eta_s = int((total - processed) / max(rate, 1e-9))
                        print(f"Progresso: {human(processed)}/{human(total)} ({pct:5.1f}%)  vel={rate:,.1f} l/s  ETA~{timedelta(seconds=eta_s)}")
                    else:
                        print(f"Progresso: {human(processed)} linhas...")

        if batch:
            cur.executemany(UPSERT_SQL, batch)
            batch.clear()

        elapsed = time.time() - t0
        rate = processed / max(elapsed, 1e-9)
        print(f"Concluído: {human(processed)} linhas em {elapsed:.1f}s (vel média {rate:,.1f} l/s)")
        return 0

    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário. Nenhum commit pendente (autocommit ativo em db.py).")
        return 130
    except Exception as e:
        print(f"\nERRO durante importação: {e}")
        return 1
    finally:
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    raise SystemExit(main())
