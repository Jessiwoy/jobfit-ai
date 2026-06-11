# Requisitos do Projeto

## Objetivo

JobFit AI é uma ferramenta local para reduzir o tempo gasto na triagem manual de vagas.

O sistema deve:

- Ler e-mails de alertas de vagas em labels configuradas do Gmail.
- Extrair informações das vagas.
- Salvar vagas e análises em SQLite.
- Comparar cada vaga com o perfil profissional do usuário.
- Gerar score de compatibilidade de 0 a 100.
- Gerar pontos fortes, pontos ausentes e motivo da recomendação.
- Classificar cada vaga como `Aplicar`, `Avaliar` ou `Ignorar`.
- Exibir as vagas em uma interface Streamlit.
- Gerar materiais de apoio somente para vagas com score maior ou igual a 70.

O sistema não deve:

- Aplicar automaticamente em vagas.
- Automatizar ações em sites de vagas.
- Fazer scraping agressivo do LinkedIn.
- Ler a caixa de entrada inteira.
- Inventar experiências, habilidades, empresas, datas ou conquistas.

## Fontes de Vagas

As vagas serão coletadas inicialmente de uma única label configurada no Gmail.

Label inicial:

- `Job Alerts`

O sistema deve permitir alterar essa label no futuro, mas a coleta padrão deve permanecer simples.

Cada configuração de coleta deve armazenar:

- Nome da fonte de coleta.
- Nome da label no Gmail.
- Status ativo/inativo.
- Tipo de parser padrão, quando existir.
- Data da última sincronização.

A origem real da vaga, como LinkedIn, Indeed ou outro site, deve ser detectada pelo remetente, links e conteúdo do e-mail.

## Fluxo Principal

### 1. Coleta

Ler somente e-mails das labels configuradas e ativas.

Extrair e salvar:

- Fonte da vaga.
- Provedor detectado da vaga, quando possível.
- Metadados do e-mail.
- Texto bruto do e-mail.
- HTML bruto do e-mail, quando disponível.
- Cargo.
- Empresa.
- Localização.
- Link da vaga.
- Data da vaga.
- Descrição, quando disponível.

Regras de extração:

- Um e-mail pode gerar uma ou mais vagas.
- Alertas digest de LinkedIn, Indeed e Glassdoor devem ser separados em vagas individuais quando o texto bruto permitir.
- Quando um e-mail digest gerar vagas individuais, o título genérico do alerta não deve aparecer como oportunidade nova.
- E-mails já processados devem poder ser reprocessados após melhoria de parser, usando o texto e HTML brutos salvos.

### 2. Limpeza

Remover, ocultar ou marcar:

- Vagas duplicadas.
- Vagas antigas.
- Vagas incompatíveis com filtros básicos.
- Falhas de extração.

### 3. Score

Comparar vaga x perfil profissional.

Gerar:

- Score de 0 a 100.
- Pontos fortes.
- Pontos ausentes.
- Motivo da recomendação.
- Classificação.

Classificações:

- `Aplicar`
- `Avaliar`
- `Ignorar`

Regras de score determinístico:

- O score deve ser explicável e testável.
- A regra detalhada do score deve ficar documentada em [Modelo de Score](scoring-model.md).
- O score deve normalizar variações comuns de grafia e idioma, como `ReactJS`, `React.js`, `Frontend`, `Front-end`, `Fullstack`, `Full Stack`, `Remoto`, `remote`, `Brasil` e `Brazil`.
- Cargos e tecnologias configurados representam alternativas desejadas, não uma lista em que todos os itens precisam aparecer.
- O score deve comparar requisitos visíveis da vaga com dados reais do currículo quando esses dados estiverem cadastrados.
- Evidências em experiências, projetos e exemplos reais devem valer mais do que palavras soltas.
- Vagas boas não devem receber score baixo apenas porque o e-mail contém uma descrição incompleta.
- Termos obrigatórios devem aumentar a relevância quando aparecem.
- Termos indesejados devem penalizar fortemente a vaga.
- Localização `Brasil` deve aceitar cidades brasileiras ou vagas remotas no Brasil quando não houver evidência clara de incompatibilidade.
- O score deve ser calibrado com revisão manual das vagas reais antes de avançar para geração de materiais.

### 4. Materiais

Gerar materiais apenas para vagas com score maior ou igual a 70.

Materiais esperados:

- Currículo adaptado.
- Carta de apresentação.
- Resumo estratégico da vaga.
- Pontos que o usuário deve destacar na candidatura.

Regra obrigatória:

Os materiais devem usar apenas informações reais cadastradas no perfil profissional do usuário.

## Dashboard

Tabela principal:

- Empresa.
- Cargo.
- Data.
- Score.
- Classificação.
- Link da vaga.

Filtros:

- Score mínimo.
- Tecnologia.
- Modalidade.
- Empresa.
- Fonte.
- Classificação.

Detalhes da vaga:

- Resumo.
- Score.
- Pontos fortes.
- Gaps.
- Motivo da recomendação.
- Materiais gerados.
- Link ou botão para abrir a vaga original.

## Configurações

A tela de configurações deve permitir editar:

- Perfil profissional.
- Cargos desejados.
- Senioridade.
- Tecnologias.
- Modalidade de trabalho.
- Localização.
- Termos obrigatórios.
- Termos indesejados.
- Fontes de vagas por label do Gmail.
- Experiências e habilidades reais que podem ser usadas nos materiais.
