# JobFit AI

JobFit AI é um assistente local para triagem de vagas recebidas por alertas de e-mail.

O objetivo é economizar tempo na busca por vagas, sem automatizar candidaturas, sem criar robôs de aplicação e sem fazer scraping agressivo de sites como LinkedIn.

A decisão de abrir uma vaga, avaliar detalhes e se candidatar continuará sendo 100% manual.

## Objetivo do Projeto

O JobFit AI deve:

- Ler alertas de vagas recebidos em labels específicas do Gmail.
- Extrair informações das vagas.
- Salvar os dados localmente em SQLite.
- Comparar cada vaga com o perfil profissional configurado.
- Gerar score de compatibilidade, pontos fortes, gaps e motivo da recomendação.
- Exibir as vagas mais relevantes em um dashboard Streamlit.
- Gerar materiais de apoio somente para vagas com alta compatibilidade.

## Restrições

O projeto deve rodar localmente no computador do usuário.

Stack obrigatória:

- Python
- SQLite
- Streamlit
- Gmail API
- Bibliotecas gratuitas e open source

Não utilizar:

- APIs pagas como requisito obrigatório
- Serviços pagos
- Scraping agressivo do LinkedIn
- Robôs de candidatura automática
- PostgreSQL
- Redis
- Docker
- Kubernetes
- Microserviços
- Arquiteturas complexas
- Overengineering

## Fontes de Vagas

O sistema não deve buscar vagas diretamente no LinkedIn ou em sites de vagas.

A fonte inicial serão alertas de vagas recebidos por e-mail e organizados por labels do Gmail.

Label inicial:

- `Job Alerts`

O sistema deve permitir adicionar novas labels futuramente.

Regra importante:

O JobFit AI deve ler somente a label configurada. Ele não deve varrer a caixa de entrada inteira.

A origem real da vaga, como LinkedIn, Indeed ou outro site, deve ser detectada depois pelo remetente, links e conteúdo do e-mail.

## Documentação do Projeto

Antes de implementar ou alterar funcionalidades, leia:

- [Requisitos do Projeto](docs/requirements.md)
- [Arquitetura](docs/architecture.md)
- [Dados Necessários](docs/data-requirements.md)
- [Sprints e Épicos](docs/sprints-and-epics.md)
- [Decisões Técnicas](docs/technical-decisions.md)
- [Design System](docs/design-system.md)

Orientação para agentes:

- [Agente JobFit AI](.agents/jobfit-ai-agent.md)

## Fluxo de Desenvolvimento

O projeto usa um fluxo simples baseado em branches:

- `main`: versão estável.
- `develop`: branch principal de desenvolvimento.
- `feature/*`: branches criadas a partir de `develop` para novas entregas.

Commits devem seguir Conventional Commits, por exemplo:

- `docs: add initial project documentation`
- `feat: add sqlite schema migration`
- `fix: handle missing gmail label`
- `test: add scoring service tests`

## Ambiente Local

O projeto deve usar ambiente virtual Python local em `.venv`.

Arquivos sensíveis ou locais, como credenciais do Gmail, tokens OAuth, banco SQLite e `.venv`, não devem ser versionados.

### Setup

Criar ambiente virtual:

```powershell
python -m venv .venv
```

Instalar dependências:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Rodar lint:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

Rodar testes:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Inicializar banco local:

```powershell
.\.venv\Scripts\python.exe -m scripts.init_db
```

Abrir app Streamlit:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

### Gmail API

Para validar labels e coletar e-mails futuramente, coloque o OAuth Client de aplicativo desktop em:

```text
credentials/credentials.json
```

O token local sera gerado em:

```text
credentials/token.json
```

Esses arquivos sao locais e nao devem ser versionados.

O escopo usado pela aplicacao e somente leitura:

```text
https://www.googleapis.com/auth/gmail.readonly
```
