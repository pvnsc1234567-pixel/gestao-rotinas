# Sistema de Gestão de Rotinas

API backend (Python + Flask + banco relacional) para gerenciar rotinas pessoais, como estudo ou exercício.
Usuários se cadastram, criam rotinas, ativam/desativam cada uma e registram a execução diária.
Toda ação relevante fica gravada em um histórico (log).

**Tecnologias:** Python 3, Flask, Flask-SQLAlchemy (ORM), Flask-Migrate (migrations), python-dotenv. Banco padrão: SQLite (pode trocar por PostgreSQL/MySQL pelo `.env`).

---

## Estrutura do projeto

```
gestao-rotinas/
├── app/
│   ├── __init__.py        # create_app(): cria o app, registra rotas e tratamento de erros
│   ├── extensions.py      # db (SQLAlchemy) e migrate (Flask-Migrate)
│   ├── models.py          # tabelas do banco
│   ├── services.py        # regras de negócio e validações
│   └── routes/            # rotas (uma por assunto)
│       ├── usuarios.py
│       ├── categorias.py
│       ├── rotinas.py
│       ├── execucoes.py
│       └── logs.py
├── migrations/            # gerada por "flask db init" (versionar no Git)
├── config.py              # configurações (lê o .env)
├── run.py                 # ponto de entrada
├── schema.sql             # script CREATE TABLE de referência
├── requirements.txt
├── .env.example           # modelo do .env
└── .gitignore
```

## Banco de dados

| Tabela | Função | Campos principais |
|---|---|---|
| `usuarios` | Quem usa o sistema | `id` (PK), `nome`, `email` (único), `criado_em` |
| `categorias` | Tabela auxiliar (ex.: Estudo, Exercício) | `id` (PK), `nome` (único), `descricao` |
| `rotinas` | Tabela principal | `id` (PK), `usuario_id` (FK), `categoria_id` (FK, opcional), `nome`, `descricao`, `ativa`, `criado_em` |
| `execucoes` | Registro diário de cada rotina | `id` (PK), `rotina_id` (FK), `data`, `observacao`, `criado_em` — **único por (`rotina_id`, `data`)** |
| `logs` | Histórico de ações | `id` (PK), `usuario_id` (FK), `rotina_id` (FK, opcional), `acao`, `descricao`, `criado_em` |

**Relacionamentos (1:N):** um usuário tem várias rotinas e vários logs; uma categoria tem várias rotinas; uma rotina tem várias execuções e vários logs.

## Regras de negócio

1. **Uma execução por rotina por dia** — registrar a mesma rotina duas vezes na mesma data retorna `409`. A regra é checada no código e também garantida no banco pela constraint única `uq_execucao_rotina_data`.
2. **Só rotinas ativas podem ser executadas** — rotina inativa retorna `409` ao tentar registrar execução.
3. **Sem execução em data futura** — a data é opcional (padrão: hoje) e não pode ser posterior a hoje.
4. **Histórico automático** — criar, atualizar, ativar, desativar e remover rotina, além de registrar e remover execução, geram um registro em `logs` (na mesma transação da ação).
5. **Mudança de status coerente** — ativar uma rotina já ativa (ou desativar uma já inativa) retorna `409`.
6. **E-mail e nome de categoria únicos** — duplicidade retorna `409`.
7. **Categoria em uso não pode ser removida** — retorna `409`.
8. **Remoções em cascata** — remover um usuário remove suas rotinas, execuções e logs; remover uma rotina remove suas execuções, mas seus logs são mantidos (com `rotina_id` nulo).

## Rotas

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Verifica se a API está no ar |
| POST | `/usuarios` | Cadastra usuário (`nome`, `email`) |
| GET | `/usuarios` | Lista usuários |
| GET | `/usuarios/<id>` | Detalha um usuário |
| PUT | `/usuarios/<id>` | Atualiza `nome` e/ou `email` |
| DELETE | `/usuarios/<id>` | Remove o usuário |
| POST | `/categorias` | Cria categoria (`nome`, `descricao` opcional) |
| GET | `/categorias` | Lista categorias |
| GET | `/categorias/<id>` | Detalha uma categoria |
| PUT | `/categorias/<id>` | Atualiza categoria |
| DELETE | `/categorias/<id>` | Remove categoria (se não estiver em uso) |
| POST | `/rotinas` | Cria rotina (`usuario_id`, `nome`, `descricao` e `categoria_id` opcionais) |
| GET | `/rotinas` | Lista rotinas; filtros: `?usuario_id=`, `?categoria_id=`, `?ativa=true\|false` |
| GET | `/rotinas/<id>` | Detalha uma rotina |
| PUT | `/rotinas/<id>` | Atualiza `nome`, `descricao`, `categoria_id` |
| PATCH | `/rotinas/<id>/status` | Ativa/desativa: `{"ativa": true}` ou `{"ativa": false}` |
| DELETE | `/rotinas/<id>` | Remove a rotina |
| POST | `/rotinas/<id>/execucoes` | Registra execução (`data` AAAA-MM-DD e `observacao` opcionais) |
| GET | `/rotinas/<id>/execucoes` | Lista execuções da rotina (mais recentes primeiro) |
| DELETE | `/execucoes/<id>` | Remove uma execução |
| GET | `/logs` | Lista o histórico; filtros: `?usuario_id=`, `?rotina_id=`, `?acao=` |

Ações possíveis em `logs.acao`: `CRIAR_ROTINA`, `ATUALIZAR_ROTINA`, `ATIVAR_ROTINA`, `DESATIVAR_ROTINA`, `EXECUTAR_ROTINA`, `REMOVER_EXECUCAO`, `REMOVER_ROTINA`.

Erros voltam em JSON: `{"erro": "mensagem"}` com o status adequado (400 validação, 404 não encontrado, 409 conflito/regra de negócio).

## Como executar

Pré-requisitos: Python 3.10+ e Git.

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Configurar as variáveis de ambiente
copy .env.example .env         # Windows
# cp .env.example .env         # Linux / macOS

# 4. Criar o banco a partir das migrations
#    (primeira vez, sem a pasta migrations/: rode "flask db init" e "flask db migrate" antes — veja abaixo)
flask db upgrade

# 5. Rodar a aplicação
flask run
```

A API sobe em `http://127.0.0.1:5000`.

### Migrations

A pasta `migrations/` é gerada pelo Flask-Migrate e **deve ser versionada no Git** (só o `venv/` e o `.env` ficam de fora).
Na primeira vez, rode:

```bash
flask db init                          # cria a pasta migrations/
flask db migrate -m "criacao inicial"  # gera a migration a partir dos models
flask db upgrade                       # cria as tabelas no banco
```

Quem clonar o repositório depois (com `migrations/` já presente) só precisa rodar `flask db upgrade`.
Depois de alterar `models.py`: `flask db migrate -m "descricao"` e `flask db upgrade`.

## Exemplo de uso (curl)

```bash
# cadastrar usuário
curl -X POST http://127.0.0.1:5000/usuarios -H "Content-Type: application/json" \
  -d '{"nome": "Ana", "email": "ana@email.com"}'

# criar rotina
curl -X POST http://127.0.0.1:5000/rotinas -H "Content-Type: application/json" \
  -d '{"usuario_id": 1, "nome": "Estudar Python"}'

# registrar execução de hoje (1ª vez: 201)
curl -X POST http://127.0.0.1:5000/rotinas/1/execucoes -H "Content-Type: application/json" -d '{}'

# repetir no mesmo dia -> 409 (regra de negócio)
curl -X POST http://127.0.0.1:5000/rotinas/1/execucoes -H "Content-Type: application/json" -d '{}'

# desativar a rotina e tentar executar -> 409
curl -X PATCH http://127.0.0.1:5000/rotinas/1/status -H "Content-Type: application/json" -d '{"ativa": false}'

# ver o histórico
curl http://127.0.0.1:5000/logs
```

No Windows (cmd/PowerShell) o `curl` costuma reclamar das aspas do JSON; nesse caso, use Postman, Insomnia ou a extensão Thunder Client do VS Code.
