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

Labels iniciais:

- `Linkedin Jobs`
- `Indeed Jobs`

O sistema deve permitir adicionar novas labels futuramente.

Regra importante:

O JobFit AI deve ler somente as labels configuradas. Ele não deve varrer a caixa de entrada inteira.

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
