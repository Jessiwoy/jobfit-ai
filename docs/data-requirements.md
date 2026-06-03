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

## Dados Opcionais

Podemos configurar também:

- Empresas a evitar.
- Expectativa salarial.
- Tipo de contrato desejado.
- Áreas de interesse.
- Áreas a evitar.
- Score mínimo padrão no dashboard.
- Idade máxima da vaga em dias.
