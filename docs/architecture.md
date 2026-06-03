# Arquitetura

## Princípios

A arquitetura deve ser simples, local e fácil de manter.

O projeto deve seguir uma estrutura de monólito modular pequeno:

- Streamlit para interface.
- Python para regras de negócio.
- SQLite para persistência.
- Gmail API para coleta de e-mails.

Evitar infraestrutura complexa, filas, containers, serviços distribuídos e dependências pagas obrigatórias.

## Estrutura Proposta

```text
jobfit-ai/
  app/
    streamlit_app.py
    pages/
      dashboard.py
      detalhes_vaga.py
      configuracoes.py
      sincronizacao.py

  core/
    config.py
    database.py
    models.py

  services/
    gmail_service.py
    email_parser.py
    deduplication_service.py
    scoring_service.py
    materials_service.py
    parsers/
      generic_parser.py
      linkedin_parser.py
      indeed_parser.py

  repositories/
    job_sources_repository.py
    user_repository.py
    preferences_repository.py
    profile_items_repository.py
    email_messages_repository.py
    jobs_repository.py
    analyses_repository.py
    materials_repository.py

  data/
    jobfit.db

  migrations/
    001_initial_schema.sql

  scripts/
    sync_gmail.py
    score_jobs.py
    generate_materials.py

  tests/
    test_email_parser.py
    test_scoring_service.py
    test_deduplication_service.py

  credentials/
    credentials.json
    token.json

  docs/
    requirements.md
    architecture.md
    data-requirements.md
    sprints-and-epics.md
    technical-decisions.md
    design-system.md

  .agents/
    jobfit-ai-agent.md

  README.md
  pyproject.toml
  requirements.txt
  .gitignore
```

## Responsabilidades por Camada

### app

Contém a interface Streamlit.

Deve exibir dados, coletar entradas do usuário e acionar operações.

Não deve conter lógica pesada de Gmail, parsing, score ou persistência.

### core

Contém infraestrutura compartilhada:

- Configurações.
- Conexão SQLite.
- Modelos ou estruturas compartilhadas.

### services

Contém regras de negócio:

- Coleta no Gmail.
- Parsing de e-mails.
- Extração de vagas.
- Deduplicação.
- Score de compatibilidade.
- Geração de materiais.

### repositories

Contém acesso ao banco de dados.

SQL deve ficar nos repositories ou nas migrations, evitando consultas espalhadas pelas páginas Streamlit.

### migrations

Contém a evolução versionada do schema SQLite.

### scripts

Contém comandos manuais para executar etapas específicas fora da interface.

## Regra de Coleta no Gmail

O serviço do Gmail deve ler somente a label configurada em `job_sources`.

O sistema não deve buscar mensagens na caixa toda.

Fluxo esperado para a fonte ativa:

1. Resolver a label pelo nome no Gmail.
2. Buscar mensagens dessa label.
3. Ignorar mensagens já salvas pelo `gmail_message_id`.
4. Salvar conteúdo bruto do e-mail.
5. Detectar o provedor provável, como LinkedIn ou Indeed, a partir do remetente, links ou conteúdo.
6. Marcar status de processamento.

## Estratégia de Parsers

Começar com um parser genérico e adicionar parsers específicos conforme necessário.

Seleção de parser:

- E-mails detectados como LinkedIn usam parser do LinkedIn quando disponível.
- E-mails detectados como Indeed usam parser do Indeed quando disponível.
- Provedores desconhecidos usam parser genérico.

O parser deve tolerar dados incompletos e preservar o conteúdo bruto para reprocessamento futuro.

## Estratégia de Score

A primeira versão do score deve ser determinística e explicável.

Dimensões sugeridas:

- Compatibilidade com cargo desejado.
- Compatibilidade com tecnologias.
- Compatibilidade com senioridade.
- Compatibilidade com modalidade.
- Compatibilidade com localização.
- Presença de termos obrigatórios.
- Penalização por termos indesejados.

IA generativa não é obrigatória para a primeira versão.

## Estratégia de Materiais

A primeira versão deve usar templates locais.

Os materiais devem ser gerados apenas a partir de:

- Dados reais do perfil.
- Experiências reais cadastradas.
- Informações extraídas da vaga.

O sistema nunca deve inventar informações profissionais.
