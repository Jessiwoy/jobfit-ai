# Decisões Técnicas

## Decisão 1: Local-first

O projeto roda localmente e salva dados em SQLite.

Motivos:

- Setup simples.
- Sem infraestrutura paga.
- Volume de dados compatível com uso pessoal.

## Decisão 2: Labels do Gmail como Fontes

O projeto lê labels configuradas do Gmail, não a caixa de entrada inteira.

Motivos:

- Maior privacidade.
- Filtragem simples.
- Suporte a LinkedIn, Indeed e futuras fontes.

## Decisão 3: Armazenar E-mails Brutos

O texto e o HTML dos e-mails devem ser salvos antes do parsing.

Motivos:

- Parsers podem ser melhorados no futuro.
- Extrações com erro podem ser reprocessadas.
- O dado original fica preservado.

## Decisão 4: Separar E-mails de Vagas

As tabelas `email_messages` e `jobs` devem ser separadas.

Motivos:

- Um e-mail pode conter mais de uma vaga.
- Uma vaga pode ser atualizada sem perder o e-mail original.
- Facilita auditoria e reprocessamento.

## Decisão 5: Score Determinístico Primeiro

A primeira versão do score deve ser baseada em regras.

Motivos:

- Gratuito.
- Explicável.
- Fácil de testar.
- Não depende de APIs pagas.

## Decisão 6: Materiais por Templates Primeiro

A primeira versão dos materiais deve usar templates locais.

Motivos:

- Evita APIs pagas.
- Reduz risco de inventar informações.
- Mantém comportamento previsível.

## Decisão 7: Não Automatizar Candidaturas

O sistema nunca deve enviar candidaturas nem interagir com formulários de aplicação.

Motivos:

- O objetivo é triagem.
- A decisão de aplicar deve continuar manual.

## Decisão 8: Fluxo Profissional de Git

O projeto deve ser commitado incrementalmente conforme o desenvolvimento avançar.

Regras:

- Usar `main` como branch estável.
- Usar `develop` como branch principal de desenvolvimento.
- Criar branches `feature/*` a partir de `develop` para novas funcionalidades.
- Usar Conventional Commits.
- Fazer commits pequenos e coesos.
- Commits devem refletir uma entrega clara de documentação, estrutura, funcionalidade, correção ou teste.
- Não misturar mudanças sem relação no mesmo commit.

Exemplos:

- `docs: add initial project documentation`
- `feat: add sqlite schema migration`
- `feat: add gmail label source configuration`
- `fix: handle missing gmail label`
- `test: add scoring service tests`

## Decisão 9: Padrões Python

O projeto deve seguir padrões consistentes para Python.

Regras:

- Usar ambiente virtual local em `.venv`.
- Manter dependências em `requirements.txt`.
- Separar interface, regras de negócio e persistência em camadas.
- Usar type hints em código novo quando trouxer clareza.
- Preferir funções e classes pequenas, com responsabilidade clara.
- Manter regras de negócio fora das páginas Streamlit.
- Escrever testes focados para parsing, score e deduplicação.
- Usar formatação e linting com ferramentas gratuitas e open source.

Ferramentas recomendadas:

- `pytest` para testes.
- `ruff` para lint e formatação.

## Decisões em Aberto

Precisam de confirmação do usuário:

- Grafia exata das labels no Gmail.
- Idioma principal do dashboard.
- Idioma dos materiais gerados.
- Se os materiais devem seguir o idioma da vaga.
- Idade máxima padrão das vagas.
- Pesos iniciais do score.
- Dados iniciais do perfil profissional.
- Dados reais do currículo.
