# Design System

Este documento define a direção visual e de experiência para a interface Streamlit do JobFit AI.

## Princípios de Interface

A interface deve ser simples, objetiva e adequada para triagem diária de vagas.

Prioridades:

- Leitura rápida.
- Filtros fáceis de usar.
- Informação densa, mas organizada.
- Pouca decoração visual.
- Destaque claro para score, classificação e motivo da recomendação.

Evitar:

- Visual de landing page.
- Elementos decorativos sem função.
- Layouts grandes demais para tarefas operacionais.
- Cards aninhados.
- Textos explicativos longos dentro da interface.

## Estrutura de Navegação

Menu principal esperado:

- Dashboard.
- Detalhes da vaga.
- Sincronização.
- Configurações.

## Dashboard

O dashboard deve priorizar triagem rápida em padrão master-detail:

- Tabela compacta para comparar vagas.
- Painel de detalhes abaixo da tabela para a vaga selecionada.
- Evitar colocar descrição, pontos fortes, gaps e motivo da recomendação como colunas da tabela principal.
- Evitar modal neste momento; manter a revisão na mesma tela para reduzir atrito.

Filtros devem ficar próximos da tabela:

- Score mínimo.
- Fonte.
- Tecnologia.
- Modalidade.
- Empresa.
- Classificação.

Colunas principais da tabela compacta:

- Score.
- Classificação.
- Cargo.
- Empresa.
- Localização.
- Status.

O painel de detalhes deve exibir:

- Link original.
- Fonte ou provedor.
- Descrição.
- Motivo da recomendação.
- Pontos fortes.
- Gaps.
- Termos encontrados e ausentes, quando existirem.

## Classificações

Usar cores de estado de forma consistente:

- `Aplicar`: verde.
- `Avaliar`: amarelo ou âmbar.
- `Ignorar`: cinza ou vermelho discreto.

O score deve ser visível, mas sem exagero visual.

## Detalhes da Vaga

A tela de detalhes deve mostrar:

- Título da vaga.
- Empresa.
- Localização.
- Fonte.
- Link original.
- Score.
- Classificação.
- Pontos fortes.
- Gaps.
- Motivo da recomendação.
- Materiais gerados, quando existirem.

## Configurações

A tela de configurações deve ser dividida em seções claras:

- Perfil profissional.
- Preferências de vagas.
- Tecnologias.
- Termos obrigatórios.
- Termos indesejados.
- Fontes de vagas.
- Dados reais para materiais.

## Componentes Streamlit Recomendados

Usar componentes nativos sempre que forem suficientes:

- `st.dataframe` ou `st.data_editor` para listas e configurações.
- `st.selectbox` e `st.multiselect` para filtros.
- `st.slider` para score mínimo.
- `st.tabs` para separar blocos de configuração.
- `st.button` para ações explícitas.
- `st.link_button` para abrir vagas externas.
- `st.status`, `st.warning`, `st.error` e `st.success` para feedback.

## Tom de Texto

Usar português claro e direto.

Exemplos:

- `Buscar novos e-mails`.
- `Recalcular scores`.
- `Gerar materiais`.
- `Abrir vaga`.
- `Nenhuma vaga encontrada para os filtros atuais`.

## Regra de Conteúdo

A interface não deve sugerir candidatura automática.

Textos devem reforçar que:

- O sistema faz triagem.
- A decisão de aplicar é manual.
- Materiais são rascunhos de apoio.
