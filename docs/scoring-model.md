# Modelo de Score

Atualizado em 2026-06-11.

Complemento de calibracao: [Score: Skills Transferiveis](scoring-transferable-skills.md).

## Objetivo

O score do JobFit AI deve estimar se vale a pena gastar tempo abrindo e avaliando uma vaga.

A pergunta principal do score é:

```text
Os requisitos visíveis da vaga têm cobertura real no currículo e nas preferências configuradas?
```

O score não tenta prever contratação. Ele tenta priorizar vagas com maior chance de aderência inicial em triagens humanas, filtros de recrutadores e leituras automatizadas de currículo.

## Referências

Este modelo usa como base conceitual abordagens comuns de matching entre vagas, currículos, ocupações e habilidades:

- ESCO, taxonomia europeia de habilidades, competências, qualificações e ocupações: https://esco.ec.europa.eu/en
- O*NET, base ocupacional do Departamento de Trabalho dos EUA com habilidades, conhecimento, atividades e contexto de trabalho: https://www.onetcenter.org/content.html
- ISCO, classificação internacional de ocupações da OIT, com conceitos de nível e especialização de habilidade: https://ilostat.ilo.org/methods/concepts-and-definitions/classification-occupation/
- Pesquisa sobre extração e matching de skills usando ESCO e modelos de linguagem: https://arxiv.org/abs/2307.03539

Essas referências não definem os pesos exatos do JobFit AI. Elas orientam a decisão de comparar vaga e currículo por cargo, skills, evidência, senioridade e contexto, em vez de usar somente contagem bruta de palavras.

## Entradas

O score usa dados extraídos da vaga:

- Cargo.
- Empresa.
- Localização.
- Modalidade.
- Senioridade.
- Descrição ou texto bruto extraído.
- Provedor da vaga.

O score usa dados configurados pelo usuário:

- Cargos desejados.
- Tecnologias.
- Senioridade aceita.
- Modalidades aceitas.
- Localizações aceitas.
- Termos obrigatórios ou prioritários.
- Termos indesejados.
- Dados reais do currículo em `profile_items`.

## Leitura do Currículo

Os dados reais do currículo são a parte mais importante para aproximar o score de uma triagem tipo ATS.

Cada item de currículo pode representar:

- Tecnologia.
- Habilidade.
- Experiência.
- Projeto.
- Formação.
- Certificação.
- Idioma.

O campo `Nome` indica a skill, experiência ou ativo curricular.

O campo `Evidência` dá contexto e vale mais do que uma palavra solta. Exemplo:

```text
Nome: React
Evidência: Desenvolvi dashboards em React e TypeScript consumindo APIs REST.
```

Esse exemplo é mais forte do que apenas:

```text
Nome: React
```

## Importação do Currículo

O currículo pode ser importado em PDF pela tela de configurações.

O sistema extrai o texto localmente com `pypdf` e atualiza:

```text
references/profile-extracted.md
```

Esse arquivo deve preservar o texto extraído do PDF sem resumo ou reescrita manual. Ele fica fora do Git porque contém dados sensíveis.

Depois da extração, o app sugere preenchimento para:

- Perfil básico.
- Cargos alvo.
- Tecnologias e skills usadas para detectar requisitos de vaga.
- Termos prioritários.
- Dados reais do currículo em `profile_items`.

As evidências usadas pelo score devem vir de trechos do próprio currículo extraído, não de texto inventado.

## Normalização

Antes de comparar textos, o sistema normaliza variações comuns:

- Remove diferenças de maiúsculas/minúsculas.
- Remove acentos.
- Trata separadores como espaço.
- Aproxima `Desenvolvedora` e `Desenvolvedor`.
- Aproxima `ReactJS`, `React.js` e `React`.
- Aproxima `Frontend`, `Front-end` e `Front end`.
- Aproxima `Fullstack` e `Full Stack`.
- Aproxima `Remoto`, `remote` e `trabalho remoto`.
- Aproxima `Brasil` e `Brazil`.

## Camadas do Score

O score máximo é 100.

```text
Cargo/função compatível:                até 20 pontos
Requisitos técnicos cobertos:           até 35 pontos
Evidência contextual no currículo:      até 15 pontos
Termos obrigatórios/prioritários:       até 10 pontos
Senioridade compatível:                 até 10 pontos
Modalidade compatível:                  até 5 pontos
Localização compatível:                 até 5 pontos
Termos indesejados:                     -15 pontos
```

## Regra Por Camada

### 1. Cargo ou Função

Vale até 20 pontos.

Compara o título e a descrição da vaga com os cargos desejados.

Exemplos de match:

- `Desenvolvedor React` com `Desenvolvedora React`.
- `Frontend Engineer` com `Frontend Developer`.
- `Full Stack Developer` com `Desenvolvedor Full Stack`.

### 2. Requisitos Técnicos Cobertos

Vale até 35 pontos.

Primeiro o sistema identifica quais skills relevantes aparecem na vaga, usando:

- Tecnologias configuradas.
- Termos obrigatórios.
- Skills e experiências cadastradas no currículo.

Depois verifica se esses requisitos aparecem no currículo.

Se há dados reais de currículo, a cobertura vem desses dados.

Se ainda não há dados reais de currículo, o sistema usa tecnologias configuradas como fallback, mas adiciona um gap pedindo evidências.

### 3. Evidência Contextual

Vale até 15 pontos.

Essa camada diferencia uma palavra solta de uma evidência real.

Ganha pontos quando uma skill exigida pela vaga aparece em:

- Evidência de uma tecnologia.
- Evidência de uma habilidade.
- Experiência.
- Projeto.
- Certificação.

Exemplo forte:

```text
React aparece na vaga.
React aparece no currículo.
A evidência diz que houve uso real de React em dashboard ou produto.
```

### 4. Termos Obrigatórios ou Prioritários

Vale até 10 pontos.

Esses termos representam preferências fortes do usuário.

Exemplo:

```text
React
```

Se a vaga menciona React ou variações reconhecidas, ganha essa camada.

### 5. Senioridade

Vale até 10 pontos.

Compara senioridade da vaga com senioridades aceitas.

Se a vaga não informa senioridade claramente, não ganha essa camada, mas também não é descartada automaticamente.

### 6. Modalidade

Vale até 5 pontos.

Compara `Remoto`, `Híbrido` ou `Presencial` com as modalidades aceitas.

### 7. Localização

Vale até 5 pontos.

Compara localização com as localizações aceitas.

`Brasil` aceita cidades brasileiras e vagas remotas no Brasil quando não há conflito claro.

### 8. Termos Indesejados

Penaliza 15 pontos.

Exemplos:

```text
PHP
WordPress
Suporte
Help Desk
Estágio
```

Essa penalização é forte porque representa descarte explícito.

## Classificação

```text
70 a 100 = Aplicar
50 a 69  = Avaliar
0 a 49   = Ignorar
```

## Interpretação

`Aplicar` significa que a vaga parece ter forte aderência ao currículo e às preferências.

`Avaliar` significa que a vaga tem sinais relevantes, mas precisa de leitura manual.

`Ignorar` significa que a vaga não mostrou aderência suficiente ou contém penalizações fortes.

## Limitações

O score depende da qualidade do texto extraído do e-mail.

Alertas de vaga muitas vezes trazem descrições incompletas. Nesses casos, o score pode subestimar uma vaga boa.

O sistema não acessa sites de vaga para enriquecer descrição, evitando scraping agressivo.

O modelo ainda é determinístico. Uma camada de IA pode ser adicionada no futuro para interpretar textos ambíguos, mas deve continuar usando apenas dados reais cadastrados.
