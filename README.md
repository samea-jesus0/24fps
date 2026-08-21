# 24FPS

Aplicacao web em Flask para descoberta, organizacao e compartilhamento de experiencias com filmes. O projeto integra com a OMDb API para buscar titulos, montar um catalogo tematico e enriquecer resenhas e listas de filmes.

## Visao Geral

Hoje o sistema oferece:

- cadastro e login de usuarios com `Flask-Login`
- busca de filmes por nome, detalhes por IMDb ID e sugestoes em tempo real
- catalogo por categorias com filtros de ano, pais, classificacao, idioma, duracao e ordenacao
- perfil do usuario com avatar, enquadramento da foto e bio
- CRUD de resenhas
- CRUD de wishlists publicas e privadas
- diretorio publico de usuarios e pagina publica de perfil
- upload local de imagens em `static/uploads`

## Stack

- Python 3.11
- Flask 3
- Flask-SQLAlchemy
- Flask-Login
- MySQL 8
- Requests
- Docker e Docker Compose

## Estrutura do Projeto

```text
24fps/
|-- app.py
|-- config.py
|-- extensions.py
|-- requirements.txt
|-- Dockerfile
|-- compose.yaml
|-- controller/
|   |-- auth_controller.py
|   |-- dashboard_controller.py
|   |-- filme_controller.py
|   |-- catalogo_controller.py
|   |-- perfil_controller.py
|   |-- user_profile_controller.py
|-- models/
|   |-- user.py
|   |-- review.py
|   |-- pesquisa.py
|   |-- wishlist.py
|   |-- wishlist_movie.py
|-- service/
|   |-- filme_service.py
|   |-- user_profile_service.py
|   |-- wishlist_service.py
|-- templates/
|-- static/
|   |-- css/
|   |-- js/
|   |-- uploads/
```

## Arquitetura Rapida

- `app.py` cria a aplicacao Flask, registra blueprints, inicializa banco/login e garante a pasta de uploads.
- `controller/` concentra rotas HTTP e renderizacao de templates.
- `service/` concentra regras de negocio e integracoes, principalmente com a OMDb API.
- `models/` define as tabelas do banco e relacionamentos.
- `templates/` e `static/` guardam a interface web.

## Banco de Dados e Inicializacao

Ao iniciar, a aplicacao executa:

- `db.create_all()` para criar tabelas ausentes
- `ensure_user_profile_columns()` para complementar colunas do perfil do usuario
- `ensure_review_columns()` para complementar colunas de resenhas

Tabelas principais:

- `user`
- `review`
- `pesquisas`
- `wishlist`
- `wishlist_movie`

Importante: o projeto nao usa uma ferramenta formal de migracao como Alembic. Parte da evolucao do schema acontece com `ALTER TABLE` na subida da aplicacao.

## Variaveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua-chave-secreta
API_KEY=sua-chave-da-omdb
DB_USER=root
DB_PASSWORD=sua-senha
DB_HOST=localhost
DB_PORT=3306
DB_NAME=filmes_24fps
FLASK_DEBUG=1
PORT=5000
```

Observacoes:

- `API_KEY` e a chave usada para a OMDb API.
- `DATABASE_URL` pode ser definida opcionalmente. Se ela nao existir, a aplicacao monta a conexao usando `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` e `DB_NAME`.
- O upload de imagem aceita `png`, `jpg`, `jpeg` e `gif`, com limite de 2 MB por arquivo.

Exemplo de `DATABASE_URL`:

```env
DATABASE_URL=mysql+pymysql://root:sua-senha@localhost:3306/filmes_24fps
```

## Como Rodar Localmente

### 1. Preparar ambiente Python

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Subir ou preparar o MySQL

Garanta que existe um banco MySQL acessivel com as credenciais do `.env`.

### 3. Iniciar a aplicacao

```powershell
python app.py
```

Aplicacao disponivel em `http://localhost:5000`.

## Como Rodar com Docker Compose

Com o arquivo `.env` preenchido, execute:

```powershell
docker compose up --build
```

Servicos expostos:

- aplicacao web em `http://localhost:5000`
- MySQL em `localhost:3307`

Volumes usados pelo Compose:

- `mysql_data` para persistencia do banco
- `uploads_data` para persistencia dos uploads

## Rotas Principais

- `/` redireciona para login ou pesquisa, dependendo da sessao
- `/cadastro` cadastro de usuario
- `/login` autenticacao
- `/logout` encerramento de sessao
- `/pesquisa` pagina principal de busca
- `/buscar` busca de filme por nome via JSON
- `/sugestoes` sugestoes de filmes
- `/api/movies/details` detalhes por `imdb_id` ou titulo
- `/catalogo` pagina do catalogo
- `/api/catalogo` dados do catalogo com filtros
- `/perfil` perfil do usuario autenticado
- `/perfil/reviews` CRUD de resenhas via JSON
- `/perfil/wishlists` CRUD de listas via JSON
- `/dashboard` atualizacao de avatar e enquadramento
- `/users` diretorio publico de usuarios
- `/users/<id>` perfil publico em HTML
- `/api/users` busca publica em JSON
- `/api/users/<id>` perfil publico em JSON

## Observacoes da Analise

- O fluxo principal ativo esta registrado em `app.py` por meio dos blueprints de autenticacao, filmes, catalogo, perfil, dashboard e perfis publicos.
- `service/auth_service.py` existe, mas o fluxo de autenticacao atual acontece diretamente em `controller/auth_controller.py`.
- `controller/resenha_controller.py` parece legado ou incompleto: o blueprint nao e registrado e ele referencia `resenha.html`, arquivo que nao existe na pasta `templates/`.
- `debug_perfil.py` e um script auxiliar local para depuracao, nao parte do fluxo de producao.
- O projeto depende da OMDb API para busca, sugestoes, detalhes e catalogo. Sem `API_KEY`, esses recursos falham ou retornam indisponibilidade.
- Nao ha suite de testes automatizados no repositorio neste momento.

## Sanidade Verificada

Foi executada uma checagem de compilacao Python nos modulos principais:

```powershell
python -m compileall app.py controller models service
```

Sem erros sintaticos nessa verificacao.
