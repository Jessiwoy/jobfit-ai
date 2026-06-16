# Dados Necessários

Este documento lista os dados que precisamos coletar do usuário antes ou durante a configuração do projeto.

## Labels do Gmail

Label atual:

- `Job Alerts`

Precisamos confirmar:

- Grafia exata de cada label no Gmail.
- Se alguma label é aninhada dentro de outra.
- Se os filtros do Gmail já aplicam essas labels automaticamente.
- Se os filtros usam a opção "Nunca enviar para Spam".

Todos os alertas de sites de vagas devem ser direcionados para a label `Job Alerts`.

## Gmail API

Precisamos de:

- Confirmação de que o usuário pode criar um projeto no Google Cloud.
- Arquivo de credenciais OAuth para aplicativo desktop.

Quando a implementação começar, o arquivo deverá ficar em:

```text
credentials/credentials.json
```

Esse arquivo não deve ser versionado no Git.

O token OAuth local sera salvo em:

```text
credentials/token.json
```

O escopo do Gmail deve ser somente leitura:

```text
https://www.googleapis.com/auth/gmail.readonly
```

## Perfil Profissional

Precisamos dos seguintes dados:

- Nome completo.
- E-mail profissional.
- Cargo atual ou cargo alvo.
- Localização.
- Idioma preferido para o dashboard.
- Idioma preferido para materiais gerados.
- Resumo profissional curto.

## Cargos Desejados

Precisamos da lista de cargos alvo.

Exemplos:

- Desenvolvedor Frontend.
- Desenvolvedor Full Stack.
- Desenvolvedor React.
- Software Engineer.

## Senioridade

Precisamos dos níveis desejados.

Exemplos:

- Júnior.
- Pleno.
- Sênior.
- Lead.

## Tecnologias

Precisamos da lista de tecnologias desejadas.

Exemplos:

- React.
- TypeScript.
- JavaScript.
- Node.js.
- Frontend.
- Full Stack.

## Modalidade

Precisamos das modalidades aceitas.

Exemplos:

- Remoto.
- Híbrido.
- Presencial.

## Localização

Precisamos das localizações aceitas.

Exemplos:

- Brasil.
- São Paulo.
- Remoto Brasil.
- Remoto global.

## Termos Obrigatórios

Precisamos dos termos que devem aumentar muito a relevância da vaga.

Exemplos:

- React.
- TypeScript.
- Remoto.

## Termos Indesejados

Precisamos dos termos que devem penalizar ou descartar vagas.

Exemplos:

- PHP.
- WordPress.
- Suporte.
- Estágio.

## Habilidades e Evidências Reais

Precisamos de fatos reais que podem ser usados nos materiais.

Para cada habilidade ou experiência:

- Nome.
- Nível.
- Tempo de experiência, se souber.
- Evidência ou exemplo real.

Exemplo:

```text
Habilidade: React
Nível: Intermediário
Evidência: Criação de dashboards com componentes reutilizáveis.
```

## Dados de Currículo

Antes de gerar currículo adaptado ou carta, precisamos de:

- Resumo profissional.
- Experiências profissionais.
- Projetos.
- Formação.
- Certificações.
- Idiomas.
- Habilidades.

Esses dados serão a única fonte permitida para geração de materiais.

## Importação de Currículo PDF

O app deve permitir carregar um currículo em PDF pela tela de configurações.

Ao importar o PDF, o sistema deve:

- Extrair o texto do PDF localmente.
- Atualizar `references/profile-extracted.md` com o texto extraído.
- Não resumir, reescrever ou trocar palavras do currículo extraído.
- Usar a extração apenas como base para sugerir preenchimento de perfil, preferências e dados reais.
- Manter o PDF e o markdown extraído fora do Git, pois contêm dados sensíveis.

O preenchimento automático deve sugerir:

- Nome.
- E-mail.
- Cargo atual ou alvo.
- Localização.
- Resumo profissional.
- Cargos alvo.
- Senioridades aceitas.
- Tecnologias e skills.
- Termos prioritários para score.
- Dados reais do currículo com evidências.

Quando houver conflito entre dados já configurados e dados importados, o app deve preservar os dados existentes ou pedir uma ação explícita do usuário antes de substituir dados reais.

## Dados Opcionais

Podemos configurar também:

- Empresas a evitar.
- Expectativa salarial.
- Tipo de contrato desejado.
- Áreas de interesse.
- Áreas a evitar.
- Score mínimo padrão no dashboard.
- Idade máxima da vaga em dias.

## Datas Operacionais das Vagas

Cada vaga deve manter duas datas com significados diferentes:

- `created_at`: data em que a vaga foi importada para o JobFit. Esta é a data confiável para filtros
  do dashboard e para a rotina diária de candidatura.
- `posted_at`: data de publicação na origem, quando for extraída com confiança da página da vaga.

Quando a data de publicação não estiver disponível ou não for confiável, a vaga continua podendo
ser filtrada pela data de importação.
