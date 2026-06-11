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

Atualização em 2026-06-11:

- O score determinístico deve ser calibrado durante o Épico 6 usando vagas reais já coletadas.
- A regra de negócio detalhada fica em [Modelo de Score](scoring-model.md).
- O score passa a ser em camadas e compara requisitos visíveis da vaga com evidências reais do currículo.
- Listas longas de cargos e tecnologias são preferências alternativas, não uma lista de requisitos que todos precisam aparecer na vaga.
- Tecnologias configuradas ajudam a identificar requisitos relevantes, mas evidências em `profile_items` têm maior valor.
- Evidências em experiências, projetos e certificações devem valer mais que palavras soltas.
- O score deve usar cobertura suficiente por categoria: bom match de cargo, requisitos técnicos cobertos pelo currículo, evidência contextual e termos prioritários podem gerar pontuação alta.
- O currículo PDF pode ser usado para preencher `profile_items`, mas a extração deve preservar o texto original em `references/profile-extracted.md` sem resumo ou reescrita manual.
- Campos ausentes ou pobres no e-mail devem reduzir confiança, mas não descartar automaticamente uma vaga.
- Termos indesejados continuam penalizando a vaga, mas não devem anular sozinhos uma aderência técnica forte.
- Variações comuns devem ser normalizadas antes do score, por exemplo `Frontend`, `Front-end`, `Fullstack`, `Full Stack`, `Remoto`, `remote`, `Brasil` e `Brazil`.

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

## Decisão 10: Extração Multi-vaga em Alertas Digest

E-mails de alerta podem conter uma lista de vagas, não apenas uma vaga.

Regras:

- Parsers específicos por provedor devem tentar extrair múltiplas vagas quando o texto bruto contém blocos repetidos de cargo, empresa, localização e link.
- LinkedIn, Indeed e Glassdoor devem ter tratamento específico antes de cair no parser genérico.
- O parser genérico continua existindo como fallback para e-mails desconhecidos.
- Quando um e-mail digest já gerou vagas internas, o registro genérico do alerta deve ser tratado como duplicado/ruído para não aparecer como oportunidade nova.
- O texto e HTML brutos continuam sendo preservados para permitir reprocessamento após melhorias de parser.

Motivos:

- Alertas como LinkedIn, Indeed e Glassdoor frequentemente enviam várias vagas por e-mail.
- Considerar apenas o assunto do e-mail subestima a quantidade de oportunidades e prejudica o score.
- Reprocessar e-mails brutos evita depender de nova coleta no Gmail para corrigir extrações antigas.

## Decisão 11: IA Como Camada Opcional Futura

IA generativa pode ser útil para interpretar descrições vagas e comparar com o currículo, mas não deve ser requisito obrigatório neste momento.

Regras:

- Primeiro calibrar extração, normalização, limpeza e score determinístico no Épico 6.
- IA pode ser avaliada depois como segunda camada, preferencialmente para vagas `Avaliar`, vagas com score intermediário ou vagas com baixa confiança.
- A IA deve retornar dados estruturados e auditáveis: score, classificação, pontos fortes, gaps, motivo e confiança.
- A IA deve usar somente dados reais cadastrados no perfil e currículo; não pode inventar experiências, habilidades, empresas, datas ou conquistas.
- O sistema deve continuar útil sem IA, mantendo o princípio local-first e sem dependência paga obrigatória.

Motivos:

- Score determinístico é mais barato, testável e previsível.
- IA pode melhorar interpretação sem substituir regras básicas de privacidade, custo e explicabilidade.
- Usar IA cedo demais pode mascarar problemas de parser e dados incompletos.

## Decisões em Aberto

Precisam de confirmação do usuário:

- Grafia exata das labels no Gmail.
- Idioma principal do dashboard.
- Idioma dos materiais gerados.
- Se os materiais devem seguir o idioma da vaga.
- Idade máxima padrão das vagas.
- Dados iniciais do perfil profissional.
- Dados reais do currículo.
- Limiar final de score para `Aplicar`, `Avaliar` e `Ignorar` após revisão manual das vagas reais.
- Se a camada opcional de IA será local, via API gratuita/baixo custo ou adiada.
