
# Portal Telefonia (Streamlit + MySQL)

Aplicação Streamlit (v1.50) para CRUD das tabelas `telefonia` (MySQL 8):
- `status`
- `dependencia`
- `comunicacao`
- `bbts`
- `atualizacoes`

## ⚙️ Pré-requisitos
- Python 3.10+
- MySQL 8 (com o database `telefonia` já criado)
- Bibliotecas Python (instale com `pip install -r requirements.txt`)

## 🔐 Conexão com o MySQL
- Host: `localhost`
- Porta: `3306`
- Usuário: `root`
- Senha: `DitecPR_9905`
- Database: `telefonia`

> Recomenda-se mover credenciais para variáveis de ambiente/secrets em produção.

## ▶️ Executando
```bash
pip install -r requirements.txt
streamlit run app.py
```

As páginas ficam no diretório `pages/` e aparecerão no menu lateral automaticamente.
