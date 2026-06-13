# Score: Skills Transferiveis

Atualizado em 2026-06-11.

## Decisao

O score passa a reconhecer skills transferiveis como sinal parcial.

Isso corrige casos em que a vaga pede uma tecnologia proxima, mas nao identica ao curriculo. Exemplo: a vaga pede Angular, mas o curriculo tem React, TypeScript, JavaScript e frontend.

## Regra

Skills transferiveis nao contam como experiencia real.

Elas adicionam ate 10 pontos quando:

- a vaga tem cargo, senioridade ou contexto coerente com o perfil;
- o requisito tecnico da vaga nao aparece literalmente no curriculo;
- o curriculo mostra base tecnica na mesma familia de habilidade.

## Familias Iniciais

- Frameworks frontend: React, Angular, Vue, Next.js e frontend.
- Linguagens e APIs web: JavaScript, TypeScript, Node, Python, REST e APIs REST.
- UI web: HTML, CSS, TailwindCSS e frontend.
- Bancos relacionais: SQL, MySQL e PostgreSQL.
- Testes frontend: Jest e Cypress.

## Exemplo

Uma vaga fullstack junior que pede Angular ou outro framework frontend e Python nao deve receber score muito baixo quando o curriculo mostra React, TypeScript, JavaScript, Node e APIs REST.

Nesse caso:

- Angular pode receber credito parcial por base em React/frontend.
- Python pode receber credito parcial por base em JavaScript/TypeScript/Node/APIs.
- O score final ainda depende de cargo, senioridade, localizacao, modalidade e requisitos literais cobertos.

## Limite

A camada transferivel nao substitui o match literal. Se uma vaga exige experiencia forte em Python e o curriculo nao tem Python, isso continua aparecendo como gap. A regra apenas evita descarte automatico quando o resto da vaga parece aderente.

## Correcao De Falso Positivo

Termos curtos agora precisam aparecer como palavra ou token independente. Isso evita pontuar termos como `seo` quando eles aparecem apenas dentro de parametros de URL ou codigos de rastreamento do LinkedIn.
