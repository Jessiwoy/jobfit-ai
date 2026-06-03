# Agente JobFit AI

## Propósito

Este agente orienta o desenvolvimento do projeto JobFit AI.

Antes de responder com detalhes de implementação ou fazer alterações de código, leia os documentos de orientação do projeto e alinhe a resposta ou implementação a eles.

## Leitura Obrigatória Antes de Desenvolver

Sempre revisar estes arquivos primeiro:

- `README.md`
- `docs/requirements.md`
- `docs/architecture.md`
- `docs/data-requirements.md`
- `docs/sprints-and-epics.md`
- `docs/technical-decisions.md`
- `docs/design-system.md`

## Limites do Projeto

JobFit AI é uma ferramenta local de triagem de vagas.

Não implementar:

- Candidaturas automáticas.
- Robôs para sites de vagas.
- Scraping agressivo.
- Dependência obrigatória de APIs pagas.
- PostgreSQL.
- Redis.
- Docker.
- Kubernetes.
- Microserviços.
- Infraestrutura complexa.

## Stack Obrigatória

Usar:

- Python.
- SQLite.
- Streamlit.
- Gmail API.
- Bibliotecas gratuitas e open source.

## Regra de Fontes

O sistema deve processar somente labels do Gmail configuradas pelo usuário.

Ele não deve varrer a caixa de entrada inteira.

Labels esperadas inicialmente:

- `Linkedin Jobs`
- `Indeed Jobs`

Novas labels devem ser suportadas por configuração.

## Abordagem de Desenvolvimento

Construir incrementalmente por sprint ou épico.

Preferir:

- Módulos pequenos e coesos.
- Schema SQLite claro.
- Score determinístico primeiro.
- Materiais por templates primeiro.
- Testes para parser, score e deduplicação.

Evitar:

- Abstrações prematuras.
- Infraestrutura em background desnecessária.
- Automações ocultas.
- Regra de negócio dentro das páginas Streamlit.

## Fluxo de Git

Manter um fluxo profissional de versionamento.

Usar:

- `main` para versão estável.
- `develop` para desenvolvimento integrado.
- `feature/*` para funcionalidades criadas a partir de `develop`.
- Conventional Commits para mensagens.

Criar commits pequenos conforme o projeto evoluir.

Antes de commitar:

- Revisar `git status`.
- Conferir se as mudanças pertencem ao mesmo escopo.
- Não incluir credenciais, tokens, banco SQLite local ou dados pessoais sensíveis.

Exemplos de mensagens:

- `docs: add initial project documentation`
- `feat: add streamlit settings page`
- `fix: handle duplicate gmail messages`
- `test: add email parser tests`

## Padrões Python

Ao implementar código Python:

- Usar ambiente virtual `.venv`.
- Manter dependências em `requirements.txt`.
- Separar UI, services, repositories e core.
- Usar type hints quando ajudarem na clareza.
- Manter regra de negócio fora do Streamlit.
- Usar `pytest` para testes.
- Usar `ruff` para lint e formatação.

## Regra de Não Inventar Informações

Materiais gerados devem usar somente fatos presentes no perfil e currículo cadastrados pelo usuário.

Nunca inventar:

- Experiências.
- Habilidades.
- Empresas.
- Datas.
- Formação.
- Certificações.
- Conquistas.

## Orientação de Resposta

Quando houver pedido de implementação, primeiro identificar o épico ou sprint relacionado.

Quando houver mudança de escopo, atualizar a documentação antes do código se a mudança afetar requisitos, arquitetura, dados ou limites do projeto.
