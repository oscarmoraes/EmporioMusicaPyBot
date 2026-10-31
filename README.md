# 🎸 Empório da Música — Agente Autônomo de Atendimento Inteligente
> **Desafio Técnico — AI Engineer | Artefact Brasil**  
> **Candidato:** Oscar Lima  
> **Linguagem Principal:** Python 3.12 / 3.13  
> **Arquitetura:** Agente ReAct Híbrido com Function Calling Determinado + Ingestão Relacional SQLite + Retrieval Normativo Estruturado

---

## 📌 Sumário
1. [Visão Geral & Cenário de Negócio](#1-visão-geral--cenário-de-negócio)
2. [Arquitetura da Solução](#2-arquitetura-da-solução)
3. [Mapeamento de Edge Cases e Armadilhas dos Dados](#3-mapeamento-de-edge-cases-e-armadilhas-dos-dados)
4. [Justificativa das Decisões Técnicas](#4-justificativa-das-decisões-técnicas)
5. [Como Executar o Projeto](#5-como-executar-o-projeto)
6. [Exemplos de Interações Reais](#6-exemplos-de-interações-reais)
7. [Testes Automatizados](#7-testes-automatizados)
8. [Limitações Conhecidas & Próximos Passos](#8-limitações-conhecidas--próximos-passos)
9. [Uso de Assistentes de Código (Workflow com IA)](#9-uso-de-assistentes-de-código-workflow-com-ia)

---

## 1. Visão Geral & Cenário de Negócio

A **Empório da Música** é uma loja tradicional de instrumentos musicais fundada em 2008 em Campo Grande/MS. A equipe de atendimento recebia um alto volume de dúvidas recorrentes pelo canal do WhatsApp (67) 3321-4500, gerando sobrecarga operacional e demora no tempo de resposta ao cliente.

O objetivo deste projeto foi prototipar e implementar um **Agente de Atendimento em Python** que atue como o consultor musical virtual **Tom**, sendo capaz de:
- Assumir a persona acolhedora, especializada e amigável da marca;
- Roteador dinâmico: saber quando consultar dados operacionais (catálogo, estoque em tempo real, pedidos, promoções ativas) e quando consultar o manual de políticas (CDC, arrependimento de 7 dias, frete, horários);
- Respeitar estritamente o escopo exclusivo da loja (venda exclusiva de instrumentos musicais, recusando cordas, palhetas, amplificadores e outros acessórios avulsos);
- Garantir **zero alucinação** em preços, regras de parcelamento e disponibilidade de estoque.

---

## 2. Arquitetura da Solução

Para evitar os riscos de alucinação de SQL livre (*Text-to-SQL*) e a perda de contexto por chunking cego em bancos vetoriais pesados, adotamos uma **Arquitetura Híbrida ReAct com Roteamento por Ferramentas Especializadas (Function Calling)**:

```
                            ┌────────────────────────────────┐
                            │       Cliente / Usuário        │
                            │   (CLI Rich / Web Streamlit)   │
                            └───────────────┬────────────────┘
                                            │ Mensagem
                                            ▼
                            ┌────────────────────────────────┐
                            │    Agente Orquestrador Tom     │
                            │ (ReAct Multi-Step + Memória)   │
                            └───────────────┬────────────────┘
                                            │ Function Calling
               ┌────────────────────────────┼────────────────────────────┐
               ▼                            ▼                            ▼
     ┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
     │ search_products_ │         │   lookup_order   │         │  consult_store_  │
     │     catalog      │         │     details      │         │     policies     │
     │ get_product_info │         │                  │         │                  │
     └─────────┬────────┘         └────────┬─────────┘         └────────┬─────────┘
               │                           │                            │
               ▼                           ▼                            ▼
  ┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐
  │   SQLite em Memória     │ │   Motor de Prazos CDC   │ │  Section-Based Engine   │
  │ • Products + JSON Specs │ │ • Cruzamento de Pedidos │ │ • 10 Seções Normativas  │
  │ • Active/Expired Promos │ │ • Cálculo de 7d/30d/90d │ │ • Detector de Acessório │
  │ • Ponta de Estoque      │ │ • Status e Rastreio     │ │ • Regras de Frete e CDC │
  └─────────────────────────┘ └─────────────────────────┘ └─────────────────────────┘
```

### Componentes Chave:
- **`src/data_engine.py`**: Carrega os 6 arquivos CSV em tabelas relacionais indexadas no SQLite em memória. Deserializa o JSON da coluna `specs` dos produtos, calcula o `effective_price` via cruzamento com promoções ativas (`is_active = 1`), preserva o histórico de promoções expiradas e implementa a máquina de cálculo financeiro (desconto PIX e parcelamento no cartão).
- **`src/policy_engine.py`**: Extrai e indexa estruturadamente as 10 seções do manual `data/políticas_da_loja.pdf`. Mantém as tabelas e regras de exceção juntas (evitando segmentações que prejudiquem a coerência das regras) e implementa detecção léxica/semântica de itens fora de escopo (acessórios não vendidos).
- **`src/tools.py`**: Define os schemas JSON tipados das ferramentas para o modelo (`search_products_catalog`, `get_product_details_and_pricing`, `lookup_customer_orders`, `consult_store_policies`) e despacha as chamadas.
- **`src/agent.py`**: Loop ReAct multi-step do agente com tratamento de múltiplas chamadas consecutivas de ferramentas, formatação do System Prompt e injeção da persona musical.
- **`src/memory.py`**: Gerenciador de histórico de mensagens por sessão com rastreamento completo de telemetria das ferramentas executadas (*tool trace*).
- **`main.py` e `app.py`**: Interfaces interativas via terminal estilizado (Rich) e navegador web (Streamlit com layout estilo WhatsApp).

---

## 3. Mapeamento de Edge Cases e Armadilhas dos Dados

A exploração detalhada dos dados fornecidos no teste técnico revelou desafios específicos e sutilezas operacionais que o agente foi especialmente desenhado para tratar:

| # | Situação Especial Encontrada | Evidência no Dataset (`data/*`) | Tratamento Implementado no Agente |
| :- | :--- | :--- | :--- |
| **1** | **Produto Ativo sem Estoque** | `ID=96` (*Giannini GF-3D*, R$ 799,90) tem `status='active'`, mas `stock_quantity=0`. | A ferramenta separa o produto dos disponíveis regulares. O agente cumpre a **Seção 7.3 do Manual**: informa com empatia a indisponibilidade temporária e sugere automaticamente similares disponíveis (*Tagima Dallas* ou *Shelby SGD-195E*). |
| **2** | **Descontinuado COM Estoque (Ponta de Estoque)** | `ID=136` (*Ibanez Bass 2X*, R$ 441,00) tem `status='discontinued'`, mas **13 unidades em estoque**. | Em vez de bloquear a venda ou ocultar o produto, o agente trata o caso como **Oportunidade Comercial de Ponta de Estoque (Últimas Unidades)**: avisa com transparência que o modelo saiu de linha pelo fabricante (sem reposição futura), aplica gatilho de oportunidade pelo preço excelente e lista também modelos da linha atual para comparação. |
| **3** | **Descontinuado SEM Estoque** | `ID=113` (*Shelby SN-7C 7 Cordas*) tem `status='discontinued'` e `stock_quantity=0`. | O agente informa que o modelo não faz mais parte do catálogo regular e sugere modelos sucessores ativos (*Tagima TW-7 7 Cordas* ou *Rozini RV-174*). |
| **4** | **Promoção Ativa & Filtros de Preço** | `ID=90` (*Crafter HT-100*) tem preço de tabela R$ 2.399,00, mas promoção ativa de 18% (`is_active=1`), caindo para **R$ 1.967,18**. | A busca de catálogo filtra sobre o `effective_price`. Se o cliente busca "violões até R$ 2.000", o Crafter é corretamente incluído. O retorno exibe preço de tabela, desconto e valor final. |
| **5** | **Veto a Desconto Cumulativo no PIX** | Seção 6.2 do Manual: *"O desconto de PIX (5%) não se aplica sobre preços já promocionais."* | O calculador financeiro verifica `has_active_promo`. Para o *Crafter HT-100*, o PIX permanece R$ 1.967,18 (bloqueia acúmulo). Para produtos sem promoção (ex: *Takamine GD20* de R$ 2.199,00), o PIX aplica os 5% caindo para R$ 2.089,05. |
| **6** | **21 Promoções Expiradas no Histórico** | Promoções de Black Friday, Páscoa e Semana do Músico com `is_active=0` no CSV. | Caso o cliente pergunte sobre um desconto antigo, o agente consulta o histórico expirado e cumpre a Seção 7.3: esclarece com transparência que a campanha venceu e apresenta o valor regular. |
| **7** | **Categorias Sem Itens Cadastrados** | Categorias 6 (Sopro Madeiras), 7 (Sopro Metais) e 8 (Cordas Orquestrais) constam em `categories.csv`, mas possuem 0 produtos em `products.csv`. | Se o cliente buscar saxofone ou violino, o agente esclarece que a categoria pertence à loja, porém está temporariamente sem modelos cadastrados no estoque físico atual (diferenciando de acessórios, que a loja não vende). |
| **8** | **Itens Fora de Escopo (Acessórios)** | Clientes pedindo cordas avulsas, palhetas, cabos, cases, pedais ou amplificadores. | O `PolicyEngine` detecta os termos e instrui o agente a recusar educadamente, explicando o foco exclusivo em instrumentos e sugerindo lojas parceiras (Seções 1 e 7.1). |
| **9** | **Contradição de Parcelamento no Manual** | A Tabela da Seção 3 diz parcela mínima de R$ 100, mas a Seção 3.1 detalha: até 3x (mín. R$ 50), 4x a 6x (mín. R$ 80) e 7x a 12x (mín. R$ 100). | O motor aplica a regra detalhada da Seção 3.1 (escada progressiva de parcelas mínimas) e disponibiliza as parcelas matematicamente válidas. |
| **10** | **Análise de Prazos CDC para Devoluções** | Pedidos no histórico variam de out/2025 a mar/2026. | Fixamos a data de referência `REFERENCE_DATE = 2026-03-25` (logo após o último pedido). Ao consultar um pedido entregue (ex.: Pedido #1 de Pedro Henrique), o sistema calcula os dias decorridos (151 dias) e embasa juridicamente que o prazo de 7 dias de arrependimento (Art. 49 CDC) expirou. |

---

## 4. Justificativa das Decisões Técnicas

1. **Framework e Arquitetura do Agente:**
   - *Decisão:* Adotamos o padrão **ReAct nativo via Function Calling da API OpenAI** em vez de frameworks monolíticos (como LangChain ou CrewAI).
   - *Por quê:* Frameworks externos adicionam dezenas de dependências transitivas, dificultam o controle fino sobre o formato das mensagens e podem quebrar entre versões. A implementação nativa com Pydantic e chamadas tipadas é leve, determinística, auditável e compatível com múltiplos provedores (`OpenAI`, `Groq`, `Gemini via endpoint compatível`).

2. **Ingestão dos CSVs via SQLite Relacional em Memória:**
   - *Decisão:* Carregar os CSVs em tabelas relacionais SQLite com índices e views de preço promocional.
   - *Por quê:* Permitir que a LLM gere código SQL livre (*Text-to-SQL*) é perigoso em produção: há risco de injeção, sintaxes incorretas e falhas ao tentar interpretar campos semi-estruturados como a coluna `specs` (JSON). O `DataEngine` encapsula queries parametrizadas de alta performance, garantindo integridade dos dados e respostas em menos de 10 milissegundos.

3. **Retrieval Normativo por Seções Estruturadas (vs. VectorDB Pesado):**
   - *Decisão:* Indexação estruturada das 10 seções do manual PDF com busca léxica/semântica ponderada em vez de ChromaDB/FAISS com embeddings neurais pesados.
   - *Por quê:* O manual `políticas_da_loja.pdf` possui 8 páginas (~1.200 palavras). O chunking tradicional baseado em tamanho fixo fragmenta regras jurídicas dependentes (por exemplo, separa a tabela de frete das notas de cotação de baterias/pianos). Além disso, instalar bibliotecas como `torch` ou `sentence-transformers` exigiria downloads de mais de 1,5 GB no ambiente do avaliador. Nossa abordagem estruturada garante integridade de 100% do contexto por tópico sem sobrecarga.

4. **Cálculo Financeiro e Prazos CDC no Código (Não na LLM):**
   - *Decisão:* Descontos percentuais, escalonamento de parcelas sem juros e cálculo de dias corridos desde a entrega são executados em código determinístico Python e entregues prontos no retorno da ferramenta.
   - *Por quê:* Modelos de linguagem podem cometer erros de arredondamento em contas matemáticas complexas. Garantir que o valor das parcelas e os dias de elegibilidade sejam processados em Python assegura conformidade financeira e legal inegociável.

---

## 5. Como Executar o Projeto

### Pré-requisitos
- **Python 3.12 ou 3.13** instalado na máquina.
- Git instalado.

### Passo 1: Clonar e Acessar o Repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd "Desafio Técnico AI Engineer 2026"
```

### Passo 2: Criar e Ativar o Ambiente Virtual
No Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Passo 3: Instalar as Dependências
```bash
pip install -r requirements.txt
```

### Passo 4: Configurar as Chaves de API
Copie o arquivo de exemplo `.env.example` para `.env`:
```bash
cp .env.example .env
```
Abra o arquivo `.env` e insira sua chave da OpenAI:
```env
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
AGENT_TEMPERATURE=0.2
REFERENCE_DATE=2026-03-25
```
*(Opcionalmente, o sistema também suporta `GROQ_API_KEY` com o modelo `llama-3.3-70b-versatile`)*.

---

### Passo 5: Executar as Interfaces

#### Opção A: Interface de Linha de Comando (CLI com Rich)
Ideal para testes rápidos no terminal com formatação elegante:
```bash
python main.py
```
*Comandos disponíveis durante o chat:*
- `/tools`: exibe as ferramentas acionadas e parâmetros da última resposta;
- `/reset`: reinicia a conversa e limpa a memória de contexto;
- `/salvar`: exporta a transcrição da sessão atual para um arquivo Markdown;
- `/ajuda`: exibe sugestões de perguntas baseadas no desafio;
- `/sair`: encerra a CLI.

#### Opção B: Interface Web Interativa (Streamlit)
Interface moderna simulando a experiência do WhatsApp com visualização em tempo real das chamadas de ferramentas:
```bash
streamlit run app.py
```
*Destaques da Web UI:*
- Botões de **1 clique** na barra lateral para carregar e testar os cenários obrigatórios do desafio;
- Painel expansível `"🛠️ Bastidores: Ferramentas Acionadas pelo Agente"` em cada mensagem para auditar o raciocínio e o JSON retornado pelo sistema;
- Botão para exportar a conversa inteira para `.md`.

---

## 6. Exemplos de Interações Reais

O edital exige entre 3 e 5 conversas documentadas no repositório cobrindo cenários variados. Todas as conversas foram executadas diretamente pelo agente com o modelo `gpt-4o-mini` e salvas na pasta [`examples/`](./examples):

1. **[`examples/01_catalogo_violoes_ate_1000.md`](./examples/01_catalogo_violoes_ate_1000.md)**:  
   *Cenário:* Consulta de violões até R$ 1.000. Demonstra a listagem ordenada por preço efetivo, isolando o *Giannini GF-3D* (ativo sem estoque) e o *Shelby SN-7C* (descontinuado), seguida de consultoria musical especializada explicando as diferenças entre cordas de nylon e aço para iniciantes.
2. **[`examples/02_preco_promo_e_pagamento.md`](./examples/02_preco_promo_e_pagamento.md)**:  
   *Cenário:* Consulta de preço do *Takamine GD20* (R$ 2.199,00 com 5% de desconto no PIX e parcelamento em 12x) comparado ao *Crafter HT-100* (em promoção de 18% a R$ 1.967,18, aplicando a regra de **não cumulatividade do PIX** da Seção 6.2).
3. **[`examples/03_pedido_e_devolucao_arrependimento.md`](./examples/03_pedido_e_devolucao_arrependimento.md)**:  
   *Cenário Não-Trivial:* O cliente Pedro Henrique Oliveira consulta o status de seus pedidos. O agente localiza o Pedido #1 (entregue) e calcula em tempo real que o prazo de 7 dias do Direito de Arrependimento (Art. 49 CDC) expirou (151 dias decorridos). Em seguida, explica com base nos dados do sistema por que o Pedido #19 foi cancelado (falta de pagamento do boleto).
4. **[`examples/04_informacoes_gerais_e_frete.md`](./examples/04_informacoes_gerais_e_frete.md)**:  
   *Cenário:* Informações de endereço físico, horário de funcionamento e detalhamento de frete para Campo Grande (motoboy grátis acima de R$ 500) vs interior/outras cidades (Correios/Jadlog e necessidade de cotação individual para instrumentos de grande porte como baterias e pianos).
5. **[`examples/05_fora_de_escopo_e_ponta_de_estoque.md`](./examples/05_fora_de_escopo_e_ponta_de_estoque.md)**:  
   *Cenário:* Teste dos guardrails de escopo (recusa educada de cordas, palhetas e amplificador), tratamento de categorias com 0 itens no catálogo (saxofone e violino) e oportunidade comercial de **Ponta de Estoque / Últimas Unidades** para o contrabaixo *Ibanez Bass 2X* (descontinuado pelo fabricante com 13 unidades remanescentes a R$ 441,00).

---

## 7. Testes Automatizados (40 Casos) & Avaliação Adversarial do Agente

O projeto inclui uma suíte de **40 testes unitários e de integração** com `pytest` cobrindo toda a camada de dados, cálculos financeiros, logística e normas do CDC/LGPD, além de **37 cenários interativos** de 1 clique na barra lateral do Streamlit (`app.py`):

```bash
pytest -v tests/test_engine.py
```

### Baterias de Teste Cobertas (`tests/test_engine.py`):
- **Núcleo Base (10 testes):** normalização textual, busca de catálogo com teto de preço, promoções ativas, veto a PIX cumulativo, desconto PIX regular, ponta de estoque (`Ibanez Bass 2X`), escada de parcelamento sem juros, pedidos/devolução CDC, categorias sem estoque e detecção de acessórios fora de escopo;
- **Bateria A — Consultoria Musical & Catálogo Avançado (Casos 01 a 04):** violões de 7 cordas (descontinuado `Shelby SN-7C` vs sucessores ativos), esgotado `Giannini GF-3D` com similares, lançamento em pré-venda (`coming_soon` `Kala Barítono Cedar`) e equipamentos profissionais de estúdio acima de R$ 10.000,00;
- **Bateria B — Finanças, Parcelamento & Promoções Expiradas (Casos 05 a 08):** transparência em promoções encerradas (Black Friday e Páscoa), trava de parcela mínima em itens de menor valor (`Shelby Soprano`), regra de pagamento combinado PIX + Cartão (limite de R$ 2.000,00) e impacto de desconto promocional sobre a faixa de frete grátis em Campo Grande (`Ohana CK-20`);
- **Bateria C — Logística & Situações Críticas de Entrega (Casos 09 a 12):** pedido em trânsito com prazo estimado vencido e protocolo de reclamação de 24h úteis (`Order #8`), pedido pendente aguardando item em pré-venda (`Order #14`), pedido multi-itens de alto valor (`Order #15`) e múltiplos pedidos do mesmo cliente com cancelamento por endereço inválido (`Order #20`);
- **Bateria D — Trocas, Devoluções CDC & Garantias (Casos 13 a 16):** defeito após os 30 dias da loja mas dentro dos 90 dias da Garantia Legal CDC (`Order #7`), itens inelegíveis para troca (setup sob encomenda, venda final e boquilhas de sopro), perda de garantia por reparo em luthier não autorizado/desgaste natural e recusa no ato por avaria no transporte;
- **Bateria E — LGPD, Expediente & Guardrails Avançados (Casos 17 a 20):** exclusão de dados pessoais pela LGPD, atendimento fora de expediente aos domingos/horário de sábado, pedidos mistos (acessórios proibidos + guitarra `Fender Telecaster`) e escalonamento à gerência para propostas comerciais não previstas no manual (instrumento usado na troca e aluguel);
- **Bateria F — Casos Avançados de Borda (Casos 21 a 30):** promoção ativa que reduz o preço abaixo do teto de pagamento combinado (`Crafter HT-100` de R$ 2.399 por R$ 1.967,18), homônimos/e-mail duplicado no CRM com frete para o interior (`Três Lagoas`), histórico duplo de boleto vencido (`#19`) + garantia após 90 dias (`#1`), pedido cancelado por falta de estoque na época mas com produto disponível hoje (`Rozini RC-104`), troca por preferência com diferença de valor, comparativo de baterias acústicas com frete de grande porte (`Dourados`), sintetizadores (`Korg`, `Roland`, `Nord`), categorias de orquestra/sopro e compra institucional em lote (`5x Yamaha C40` para escola de música).

### Avaliação Empírica: Cenários Canônicos, Variações Coloquiais e Benchmark de Modelos
Além dos testes determinísticos, submetemos o agente completo a três experimentos empíricos ponta a ponta:
1. **35 Cenários Canônicos com `gpt-4o-mini` (5 do edital + 30 das Baterias A–F):** **100% de aderência** aos fatos do banco de dados, cálculos de parcelamento/PIX e políticas da loja, com latência média de **~3,1s por resposta**.
2. **35 Variações Adversariais/Coloquiais de WhatsApp (`gpt-4o-mini`):** Reescrevemos os mesmos 35 cenários usando gírias musicais (*"pegar no rolo"*, *"quinhentão no pix de sinal"*, *"batera"*, *"mizinha arrebentou"*, *"print salvo do ano passado"*), abreviações e ordens frasais invertidas para auditar a generalização semântica do agente sem depender de palavras-chave fixas, orientando melhorias nos contratos das Tools (`src/tools.py`) e no enriquecimento de alternativas similares (`src/data_engine.py`).
3. **Benchmark Comparativo e Engenharia de Otimização para Modelo Nano (`gpt-5-nano` vs. `gpt-4o-mini`):**
   - Modelos legados de entrada (`gpt-3.5-turbo` e `gpt-4.1-nano`) já encontram-se descontinuados na API da OpenAI (*HTTP 404 Deprecated*). Executamos os mesmos 35 cenários no modelo ativo da classe **Nano** (**`gpt-5-nano`**), primeiro em sua configuração padrão (*baseline*) e depois aplicando **4 intervenções arquiteturais específicas para modelos Nano**:
     1. **Controle de Orçamento de Raciocínio (`reasoning_effort="low"`):** Redução dos tokens internos de raciocínio para perguntas transacionais de WhatsApp (`src/agent.py`).
     2. **Payloads *Single-Hop* e *Context Pruning* (`src/data_engine.py`):** Inclusão de `pix_price` diretamente nos resultados de `search_catalog` (evitando chamadas redundantes em loop a `get_product_details_and_pricing`) e omissão de planos de pagamento/PIX quando `stock_quantity == 0` ou `status == "coming_soon"` (impedindo que modelos menores vazem o preço PIX de itens esgotados).
     3. **Guardrail Negativo Estrito contra *Literal Instruction Following* (`src/agent.py` e `src/policy_engine.py`):** Proibição explícita de redigir receitas culinárias ou listas fora do domínio (no *baseline*, o `gpt-5-nano` havia escrito uma receita completa de bolo de milho no `CASE_19`).
     4. **Restrição de Concisão e Sanitização Determinística de Saída:** Limite de extensão para leitura fluida no celular e correção pós-processamento de domínio oficial (`contato@emporiodamusica.com.br`).
   - **Resultado Comparativo nos 35 Cenários (`gpt-4o-mini` vs. `gpt-5-nano` Baseline vs. `gpt-5-nano` Otimizado):**

| Métrica (35 Cenários End-to-End) | `gpt-4o-mini` (Padrão) | `gpt-5-nano` (Baseline) | `gpt-5-nano` (Pós-Otimização Arquitetural) |
| :--- | :---: | :---: | :---: |
| **Latência Média por Turno** | **~3,1 s** | 25,14 s | **6,41 s (-74,5%)** |
| **Latência Máxima (Pior Caso)** | **~5,8 s** | 47,36 s | **10,03 s (-78,8%)** |
| **Total de *Tool Calls* (35 casos)** | **45** | 65 | **51 (-21,5%)** |
| **Extensão Média da Resposta** | **~165 palavras** | 311,3 palavras | **224,0 palavras (-28,0%)** |
| **Guardrail `CASE_19` (Bolo de Milho)** | ✅ Recusou com humor | ❌ Escreveu a receita inteira | ✅ **Recusou em 1 frase curta** |
| **Vazamento PIX Item Esgotado (`CASES 01/02`)** | ✅ Sem vazamento | ❌ Citou PIX do item sem estoque | ✅ **100% eliminado (*Context Pruning*)** |

---

## 8. Limitações Conhecidas & Próximos Passos

Em transparência com os critérios de avaliação do desafio, documentamos as limitações conhecidas da arquitetura atual e o que faríamos com mais tempo para evolução em produção:

1. **Trade-offs do Modelo Leve (`gpt-4o-mini`) em *Multi-Constraint Reasoning*:**
   - Embora o `gpt-4o-mini` ofereça excelente latência e baixo custo, testes adversariais com frases muito coloquiais mostraram que, quando o usuário afirma um preço na própria pergunta (ex.: *"vi o Crafter que custa R$ 2.399..."*), modelos leves podem ocasionalmente confiar na premissa do usuário se não forem instruídos de forma estrita no schema da Tool a sempre validar o preço efetivo no banco. Em produção crítica, combinaríamos um roteador de intenção prévio ou um modelo de raciocínio superior (`gpt-4o`) para turnos financeiros complexos.
2. **Recuperação Léxica vs. Semântica Híbrida nas Políticas (`PolicyEngine`):**
   - O `PolicyEngine` atual utiliza indexação estruturada por seções e pontuação léxica normalizada (zero dependências externas). Para gírias regionais muito distantes do vocabulário do manual (ex.: *"pegar instrumento no rolo"* em vez de *"usado como parte de pagamento"*), uma busca puramente léxica pode exigir expansão de sinônimos. Com mais tempo, implementaríamos **Hybrid Search (BM25 + Embeddings densos via `text-embedding-3-small`)** sobre os parágrafos do manual.
3. **Conector Oficial de WhatsApp (Meta Cloud API / Twilio) e Autenticação OTP (LGPD):**
   - Substituir a interface simulada por webhooks assíncronos (FastAPI + Redis) e exigir validação por código OTP antes de exibir detalhes de pedidos e endereços, prevenindo exposição de dados entre homônimos no CRM (observamos no dataset casos reais de homônimos/e-mails compartilhados, como `bruno.martins@jmail.com` nos IDs `11` e `43`).
4. **Observabilidade e LLM-as-a-Judge Contínuo:**
   - Integrar **Langfuse / OpenTelemetry** e transformar nosso script de auditoria adversarial de 35 variações em um pipeline de CI/CD (*LLM-as-a-Judge*) para detectar regressões de prompt antes de cada deploy.

---

## 9. Uso de Assistentes de Código (Workflow com IA)

Em consonância com as orientações do desafio (*"caso faça uso de algum recurso de IA, explique qual a escolhida e como utilizou"*), detalhamos nosso workflow de engenharia assistida por IA:

- **Assistente Utilizado:** Antigravity (Google DeepMind) integrado ao ambiente local de desenvolvimento.
- **Como a Ferramenta Foi Explorada:**
  1. **Análise Exploratória do Dataset:** A IA foi utilizada para inspecionar os arquivos CSV e detectar as armadilhas propositais nos dados (tais como produtos com estoque 0 e status ativo, categorias com 0 itens no catálogo e conflitos entre a tabela de parcelamento e o texto descritivo do PDF).
  2. **Refinamento Arquitetural:** Em vez de aceitar uma proposta genérica com bancos vetoriais pesados, realizamos uma sessão crítica aberta para substituir frameworks pesados por soluções enxutas, determinísticas e rápidas (SQLite em memória e Section-Based Retrieval).
  3. **Aceleração do Scaffolding:** Geração dos schemas JSON para Function Calling e estruturação da suite de testes do `pytest`.
  4. **Controle de Qualidade Humano:** Cada linha de lógica de negócio (cálculo de não cumulatividade do PIX, prazos de devolução do CDC e gatilho de ponta de estoque para descontinuados) foi validada, testada e ajustada manualmente para refletir com fidelidade as diretrizes da Empório da Música.
