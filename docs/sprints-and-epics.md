# Sprints e Épicos

## Estado Atual do Projeto

Atualizado em 2026-06-11.

Regra de sequenciamento:

- Seguir os épicos em ordem.
- Não iniciar o Épico 5 antes de fechar os critérios principais dos Épicos 3 e 4.
- Não iniciar score, dashboard avançado ou materiais antes de concluir coleta, extração e limpeza.

Status por épico:

- Épico 1: entregue.
- Épico 2: entregue.
- Épico 3: entregue.
- Épico 4: entregue.
- Épico 5: entregue.
- Épico 6: em andamento.
- Épico 7: pendente, exceto visualização básica e recorte de dashboard master-detail antecipado para apoiar validação do Épico 6.
- Épico 8: pendente.
- Épico 9: pendente.

Entregas já existentes:

- Banco SQLite inicial com migrations.
- Configurações básicas no Streamlit.
- Cadastro de perfil, preferências, itens reais de perfil e fontes Gmail.
- Validação de labels do Gmail.
- Coleta de e-mails somente de labels ativas configuradas.
- Persistência de texto e HTML brutos dos e-mails.
- Detecção inicial de provedor por remetente, links e conteúdo.
- Processamento manual de e-mails salvos.
- Parser genérico inicial para criar vagas.
- Parsers iniciais por provedor para LinkedIn e Indeed.
- Reprocessamento manual de e-mails com erro de extração.
- Deduplicação inicial por `gmail_message_id` e `content_hash`.
- Limpeza manual inicial de vagas por status interno: `duplicate`, `old` e `incompatible`, exibidos na interface como duplicada, antiga e incompatível.
- Dashboard com filtro de status para ocultar vagas que deixaram de ser novas oportunidades.
- Validação da limpeza com banco local: 42 vagas revisadas, 13 duplicadas marcadas e 29 mantidas como novas.
- Score determinístico inicial salvo em `job_analyses`, com classificação `Aplicar`, `Avaliar` ou `Ignorar`.
- Proteção para não calcular scores quando perfil, preferências e dados reais ainda não estiverem configurados.
- Limpeza de scores antigos quando o recálculo é solicitado sem critérios configurados.
- Limpeza de scores antigos quando preferências ou dados reais são alterados.
- Resumo de critérios configurados antes do recálculo de scores.
- Resumo de scores calculados por classificação e faixa de score.
- Dashboard com filtros de score mínimo e classificação.
- Dashboard em padrão master-detail com tabela compacta e painel de detalhes da vaga selecionada.
- Extração multi-vaga para alertas digest de LinkedIn, Indeed e Glassdoor.
- Reprocessamento manual de e-mails já processados para reaproveitar e-mails brutos após melhoria de parser.
- Normalização de score para variações comuns como `ReactJS`, `Front-end`, `Frontend`, `Fullstack`, `Full Stack`, `Remoto` e `remote`.
- Ajuste do score determinístico para não exigir correspondência de todos os cargos e tecnologias configurados.
- Reformulação do score em camadas, comparando requisitos visíveis da vaga com evidências reais do currículo.
- Documentação da regra de negócio do score em `docs/scoring-model.md`.
- Limpeza menos agressiva para localização, evitando descartar cidades brasileiras quando `Brasil` está aceito.
- Marcação de e-mails digest genéricos como duplicados quando as vagas internas já foram extraídas.
- Validação local após reprocessamento: 324 vagas salvas, 155 vagas novas, 156 duplicadas e 13 incompatíveis.
- Distribuição local atual dos scores: 1 `Aplicar`, 76 `Avaliar` e 78 `Ignorar`.

Próximas entregas, em ordem:

1. Revisar manualmente as vagas classificadas como `Avaliar` e ajustar pesos/limiares conforme o resultado real.
2. Cadastrar dados reais do currículo em `profile_items` para melhorar explicação de pontos fortes e gaps.
3. Fechar o Épico 6 quando os scores estiverem coerentes para uso diário.
4. Avaliar uma camada opcional de IA somente depois do score determinístico estar calibrado e testável.

## Épico 1: Fundação do Projeto

Objetivo: criar a base local do projeto sem integração com Gmail.

Escopo esperado:

- Estrutura de pastas.
- Setup de migrations SQLite.
- Conexão com banco.
- Tabelas iniciais.
- Padrão simples de repositories.
- Base do app Streamlit.
- Tela inicial de configurações.

Critério de aceite:

- O app inicia localmente.
- O banco pode ser criado a partir da migration.
- O usuário consegue salvar preferências básicas.

## Épico 2: Fontes de Vagas e Labels do Gmail

Objetivo: suportar a label configurável de coleta de vagas.

Escopo esperado:

- Tabela `job_sources`.
- Adicionar, editar, ativar e desativar a label de coleta.
- Resolver IDs das labels no Gmail.
- Validar se a label existe.

Critério de aceite:

- O usuário consegue configurar `Job Alerts`.
- O sistema lê somente a label ativa.

## Épico 3: Coleta no Gmail

Objetivo: coletar e-mails brutos dos alertas de vagas.

Escopo esperado:

- Fluxo OAuth local do Gmail.
- Buscar mensagens por label configurada.
- Salvar texto e HTML brutos.
- Ignorar mensagens já processadas.
- Detectar o provedor provável da vaga pelo e-mail.
- Registrar status e erros.

Critério de aceite:

- Novos e-mails das labels configuradas são salvos no SQLite.
- Nenhum e-mail fora das labels configuradas é lido.

## Épico 4: Extração de Vagas

Objetivo: transformar e-mails em registros de vagas.

Escopo esperado:

- Parser genérico.
- Parser para LinkedIn.
- Parser para Indeed.
- Parser para Glassdoor.
- Extração de múltiplas vagas quando um e-mail de alerta contém uma lista/digest.
- Extração de cargo, empresa, localização, URL, data e descrição.
- Registro de falhas sem perder o e-mail bruto.

Critério de aceite:

- E-mails processados geram vagas no banco.
- E-mails digest podem gerar mais de uma vaga quando o texto bruto contém blocos separados de vaga.
- Extrações incompletas ficam visíveis e podem ser reprocessadas.

## Épico 5: Limpeza e Deduplicação

Objetivo: manter a lista de vagas útil e limpa.

Escopo esperado:

- Detecção de duplicatas.
- Filtro de vagas antigas.
- Filtros básicos de incompatibilidade.
- Controle de status.

Critério de aceite:

- Vagas repetidas não aparecem como novas oportunidades.
- Vagas antigas ou incompatíveis podem ser ocultadas ou marcadas.

## Épico 6: Score de Compatibilidade

Objetivo: ranquear vagas por aderência ao perfil.

Escopo esperado:

- Score determinístico de 0 a 100.
- Pontos fortes.
- Gaps.
- Motivo da recomendação.
- Classificação `Aplicar`, `Avaliar` ou `Ignorar`.
- Recalcular scores quando preferências mudarem.
- Normalizar variações comuns de termos em português e inglês.
- Comparar requisitos técnicos visíveis na vaga com dados reais do currículo.
- Valorizar evidências contextuais em experiências, projetos, certificações e habilidades reais.
- Calibrar pesos com vagas reais antes de iniciar geração de materiais.
- Evitar que listas longas de tecnologias reduzam artificialmente vagas boas.

Critério de aceite:

- Cada vaga extraída pode receber um score explicável.
- O dashboard consegue filtrar por score e classificação.

## Épico 7: Dashboard

Objetivo: criar uma interface Streamlit útil para triagem diária.

Escopo esperado:

- Lista de vagas.
- Filtros.
- Página ou seção de detalhes.
- Link para vaga original.
- Filtro por fonte.
- Exibição da análise.

Critério de aceite:

- O usuário consegue revisar vagas rapidamente e abrir apenas as mais relevantes.

## Épico 8: Geração de Materiais

Objetivo: gerar materiais de apoio apenas para vagas fortes.

Escopo esperado:

- Gerar somente para score maior ou igual a 80.
- Currículo adaptado por templates locais.
- Carta de apresentação por templates locais.
- Resumo estratégico.
- Pontos a destacar.
- Regra rígida de não inventar informações.

Critério de aceite:

- Materiais usam apenas dados reais cadastrados.
- Materiais ficam salvos e visíveis nos detalhes da vaga.

## Épico 9: Polimento e Confiabilidade

Objetivo: deixar o projeto confortável para uso local diário.

Escopo esperado:

- Logs.
- Tratamento de erros.
- Controles de reprocessamento.
- Instruções de uso no README.
- Testes de parser, score e deduplicação.

Critério de aceite:

- Falhas comuns são visíveis e recuperáveis.
- A lógica principal possui testes focados.
