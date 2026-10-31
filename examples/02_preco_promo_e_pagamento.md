# Cenário 2: Consulta de Preços, Promoções Ativas e Regras de Pagamento (PIX e Cartão)

**Arquivo:** `02_preco_promo_e_pagamento.md`  
**Descrição do Cenário:** Demonstra o agente informando o preço do Takamine GD20 (sem promoção, com 5% de desconto no PIX e parcelamento sem juros) e comparando com o Crafter HT-100 (que possui promoção ativa de 18% e por isso NÃO acumula desconto de PIX conforme Seção 6.2).

---

## 👤 Turno 1 — Cliente:
> **"Quanto custa o Takamine GD20 e quais as formas de pagamento disponíveis?"**

### 🛠️ Chamadas de Ferramentas (Sistemas Consultados):
- **Ferramenta:** `get_product_details_and_pricing`
  - **Parâmetros:** `{'product_id_or_name': 'Takamine GD20'}`
  - **Resposta do Sistema:**
```json
{'found': True, 'product_id': 95, 'name': 'Takamine GD20 Dreadnought Natural', 'category_name': 'Violões', 'original_price': 2199.0, 'effective_price': 2199.0, 'has_active_promotion': False, 'active_promotion': None, 'expired_promotions': [{'promotion_id': 4, 'discount_percent': 12.0, 'description': 'Oferta Especial', 'is_active': False}], 'stock_quantity': 5, 'status': 'active', 'is_clearance_opportunity': False, 'status_guidance_for_agent': 'Produto disponível em estoque para pronta entrega.', 'specs': {'top': 'Cedro Sólido', 'back_sides': 'Sapele', 'neck': 'Mogno', 'strings': 'steel', 'scale': '650mm', 'electronics': 'no', 'color': 'Natural'}, 'description': 'Violão dreadnought Takamine com tampo sólido em cedro. Excelente para fingerstyle com timbre quente e definido.', 'payment_conditions': {'effective_price': 2199.0, 'original_price': 2199.0, 'has_active_promo': False, 'pix': {'price': 2089.05, 'discount_percent': 5, 'discount_applied': True, 'note': 'À vista no PIX com 5% de desconto: R$ 2089.05 (economia de R$ 109.95).'}, 'debit_card': {'price': 2199.0, 'note': 'À vista no débito (todas as bandeiras).'}, 'boleto': {'price': 2199.0, 'note': 'À vista no boleto bancário (compensação em até 3 dias úteis).'}, 'credit_card': {'max_installments_without_interest': 12, 'available_plans': [{'installments': 1, 'installment_value': 2199.0, 'total': 2199.0, 'interest_free': True}, {'installments': 2, 'installment_value': 1099.5, 'total': 2199.0, 'interest_free': True}, {'installments': 3, 'installment_value': 733.0, 'total': 2199.0, 'interest_free': True}, {'installments': 4, 'installment_value': 549.75, 'total': 2199.0, 'interest_free': True}, {'installments': 5, 'installment_value': 439.8, 'total': 2199.0, 'interest_free': True}, {'installments': 6, 'installment_value': 366.5, 'total': 2199.0, 'interest_free': True}, {'installments': 7, 'installment_value': 314.14, 'total': 2199.0, 'interest_free': True}, {'installments': 8, 'installment_value': 274.88, 'total': 2199.0, 'interest_free': True}, {'installments': 9, 'installment_value': 244.33, 'total': 2199.0, 'interest_free': True}, {'installments': 10, 'installment_value': 219.9, 'total': 2199.0, 'interest_free': True}, {'installments': 11, 'installment_value': 199.91, 'total': 2199.0, 'interest_free': True}, {'installments': 12, 'installment_value': 183.25, 'total': 2199.0, 'interest_free': True}], 'rules': 'Regra 3.1: até 3x (mín. R$ 50), 4x a 6x (mín. R$ 80), 7x a 12x (mín. R$ 100).'}}, 'similar_available_alternatives': []}
```
- **Ferramenta:** `consult_store_policies`
  - **Parâmetros:** `{'query': 'formas de pagamento'}`
  - **Resposta do Sistema:**
```json
{'query': 'formas de pagamento', 'total_sections_matched': 2, 'sections': [{'section_key': 'pagamento', 'title': '3 e 3.1. Formas de Pagamento e Regras de Parcelamento', 'content': 'Formas de pagamento aceitas:\n• PIX: Pagamento à vista com 5% de desconto sobre o preço de tabela (ATENÇÃO: não cumulativo com produtos já em promoção).\n• Cartão de Débito: À vista, todas as bandeiras aceitas.\n• Boleto Bancário: À vista, compensação em até 3 dias úteis.\n• Cartão de Crédito: Até 12x SEM JUROS.\n\nRegras Específicas de Parcelamento no Cartão (Seção 3.1):\n• Em até 3x sem juros: sem valor mínimo de parcela (exceto abaixo de R$ 50,00).\n• De 4x a 6x sem juros: parcela mínima de R$ 80,00.\n• De 7x a 12x sem juros: parcela mínima de R$ 100,00.\n• Combinação de pagamentos (ex.: PIX + Cartão): permitida para compras acima de R$ 2.000,00.'}, {'section_key': 'trocas_devolucoes', 'title': '4. Política de Trocas e Devoluções (CDC)', 'content': "A Empório da Música segue rigorosamente o Código de Defesa do Consumidor (Lei nº 8.078/90):\n\n4.1 Direito de Arrependimento (Compras Online / WhatsApp):\n• O cliente pode solicitar a devolução em até 7 (sete) dias corridos após o recebimento do produto, sem necessidade de justificativa.\n• O produto deve estar em sua embalagem original, sem sinais de uso, acompanhado de todos os manuais e acessórios originais.\n• O frete de devolução por arrependimento é 100% por conta da loja.\n• O reembolso/estorno é realizado na mesma forma de pagamento original em até 10 dias úteis.\n\n4.2 Trocas por Defeito de Fabricação:\n• Produtos com defeito podem ser trocados diretamente na loja em até 30 (trinta) dias corridos após a compra.\n• Após os 30 dias (e até o término da garantia), o cliente aciona a garantia do fabricante, com intermediação da Empório da Música mediante solicitação.\n• Não são cobertos danos causados por mau uso, quedas, umidade excessiva ou intervenções de terceiros não autorizados.\n\n4.3 Trocas por Preferência (cor, modelo, tamanho):\n• Permitidas em até 7 dias, condicionadas à disponibilidade em estoque. Produto em perfeito estado na embalagem original.\n\n4.4 Itens NÃO Elegíveis para Troca:\n• Instrumentos com personalização ou ajustes sob encomenda (setup/regulagem especial sob medida);\n• Produtos adquiridos em liquidação com aviso expresso de 'venda final';\n• Boquilhas de instrumentos de sopro (por rígidas questões de higiene sanitária)."}], 'out_of_scope_alert': None}
```

### 🎸 Resposta do Tom (Empório da Música):
O **Takamine GD20 Dreadnought Natural** está disponível por **R$ 2.199,00**. Como ele não está em promoção, você pode aproveitar as seguintes formas de pagamento:

### Formas de Pagamento:
- **PIX:** R$ 2.089,05 (5% de desconto à vista).
- **Cartão de Débito:** À vista, todas as bandeiras aceitas.
- **Boleto Bancário:** À vista, compensação em até 3 dias úteis.
- **Cartão de Crédito:** Até 12x SEM JUROS, com as seguintes opções de parcelamento:
  - 1x: R$ 2.199,00
  - 2x: R$ 1.099,50
  - 3x: R$ 733,00
  - 4x: R$ 549,75
  - 5x: R$ 439,80
  - 6x: R$ 366,50
  - 7x: R$ 314,14
  - 8x: R$ 274,88
  - 9x: R$ 244,33
  - 10x: R$ 219,90
  - 11x: R$ 199,91
  - 12x: R$ 183,25

Se precisar de mais alguma informação ou ajuda, é só avisar! 🎶

---

## 👤 Turno 2 — Cliente:
> **"E o violão Crafter HT-100? Ele está em promoção? Se eu pagar no PIX tenho mais 5% de desconto sobre o valor promocional?"**

### 🛠️ Chamadas de Ferramentas (Sistemas Consultados):
- **Ferramenta:** `get_product_details_and_pricing`
  - **Parâmetros:** `{'product_id_or_name': 'Crafter HT-100'}`
  - **Resposta do Sistema:**
```json
{'found': True, 'product_id': 90, 'name': 'Crafter HT-100 Folk Aço Natural', 'category_name': 'Violões', 'original_price': 2399.0, 'effective_price': 1967.18, 'has_active_promotion': True, 'active_promotion': {'promotion_id': 19, 'discount_percent': 18.0, 'description': 'Desconto Exclusivo', 'is_active': True}, 'expired_promotions': [], 'stock_quantity': 3, 'status': 'active', 'is_clearance_opportunity': False, 'status_guidance_for_agent': 'Produto disponível em estoque para pronta entrega.', 'specs': {'top': 'Spruce Engelmann Sólido', 'back_sides': 'Mogno', 'neck': 'Mogno', 'strings': 'steel', 'scale': '648mm', 'electronics': 'no', 'color': 'Natural'}, 'description': 'Violão folk de alta qualidade com tampo sólido em Spruce Engelmann. Projeção sonora superior e acabamento impecável.', 'payment_conditions': {'effective_price': 1967.18, 'original_price': 2399.0, 'has_active_promo': True, 'pix': {'price': 1967.18, 'discount_percent': 0, 'discount_applied': False, 'note': 'Preço promocional ativo: desconto de 5% do PIX não cumulativo (Seção 6.2).'}, 'debit_card': {'price': 1967.18, 'note': 'À vista no débito (todas as bandeiras).'}, 'boleto': {'price': 1967.18, 'note': 'À vista no boleto bancário (compensação em até 3 dias úteis).'}, 'credit_card': {'max_installments_without_interest': 12, 'available_plans': [{'installments': 1, 'installment_value': 1967.18, 'total': 1967.18, 'interest_free': True}, {'installments': 2, 'installment_value': 983.59, 'total': 1967.18, 'interest_free': True}, {'installments': 3, 'installment_value': 655.73, 'total': 1967.18, 'interest_free': True}, {'installments': 4, 'installment_value': 491.8, 'total': 1967.18, 'interest_free': True}, {'installments': 5, 'installment_value': 393.44, 'total': 1967.18, 'interest_free': True}, {'installments': 6, 'installment_value': 327.86, 'total': 1967.18, 'interest_free': True}, {'installments': 7, 'installment_value': 281.03, 'total': 1967.18, 'interest_free': True}, {'installments': 8, 'installment_value': 245.9, 'total': 1967.18, 'interest_free': True}, {'installments': 9, 'installment_value': 218.58, 'total': 1967.18, 'interest_free': True}, {'installments': 10, 'installment_value': 196.72, 'total': 1967.18, 'interest_free': True}, {'installments': 11, 'installment_value': 178.83, 'total': 1967.18, 'interest_free': True}, {'installments': 12, 'installment_value': 163.93, 'total': 1967.18, 'interest_free': True}], 'rules': 'Regra 3.1: até 3x (mín. R$ 50), 4x a 6x (mín. R$ 80), 7x a 12x (mín. R$ 100).'}}, 'similar_available_alternatives': []}
```
- **Ferramenta:** `consult_store_policies`
  - **Parâmetros:** `{'query': 'formas de pagamento'}`
  - **Resposta do Sistema:**
```json
{'query': 'formas de pagamento', 'total_sections_matched': 2, 'sections': [{'section_key': 'pagamento', 'title': '3 e 3.1. Formas de Pagamento e Regras de Parcelamento', 'content': 'Formas de pagamento aceitas:\n• PIX: Pagamento à vista com 5% de desconto sobre o preço de tabela (ATENÇÃO: não cumulativo com produtos já em promoção).\n• Cartão de Débito: À vista, todas as bandeiras aceitas.\n• Boleto Bancário: À vista, compensação em até 3 dias úteis.\n• Cartão de Crédito: Até 12x SEM JUROS.\n\nRegras Específicas de Parcelamento no Cartão (Seção 3.1):\n• Em até 3x sem juros: sem valor mínimo de parcela (exceto abaixo de R$ 50,00).\n• De 4x a 6x sem juros: parcela mínima de R$ 80,00.\n• De 7x a 12x sem juros: parcela mínima de R$ 100,00.\n• Combinação de pagamentos (ex.: PIX + Cartão): permitida para compras acima de R$ 2.000,00.'}, {'section_key': 'trocas_devolucoes', 'title': '4. Política de Trocas e Devoluções (CDC)', 'content': "A Empório da Música segue rigorosamente o Código de Defesa do Consumidor (Lei nº 8.078/90):\n\n4.1 Direito de Arrependimento (Compras Online / WhatsApp):\n• O cliente pode solicitar a devolução em até 7 (sete) dias corridos após o recebimento do produto, sem necessidade de justificativa.\n• O produto deve estar em sua embalagem original, sem sinais de uso, acompanhado de todos os manuais e acessórios originais.\n• O frete de devolução por arrependimento é 100% por conta da loja.\n• O reembolso/estorno é realizado na mesma forma de pagamento original em até 10 dias úteis.\n\n4.2 Trocas por Defeito de Fabricação:\n• Produtos com defeito podem ser trocados diretamente na loja em até 30 (trinta) dias corridos após a compra.\n• Após os 30 dias (e até o término da garantia), o cliente aciona a garantia do fabricante, com intermediação da Empório da Música mediante solicitação.\n• Não são cobertos danos causados por mau uso, quedas, umidade excessiva ou intervenções de terceiros não autorizados.\n\n4.3 Trocas por Preferência (cor, modelo, tamanho):\n• Permitidas em até 7 dias, condicionadas à disponibilidade em estoque. Produto em perfeito estado na embalagem original.\n\n4.4 Itens NÃO Elegíveis para Troca:\n• Instrumentos com personalização ou ajustes sob encomenda (setup/regulagem especial sob medida);\n• Produtos adquiridos em liquidação com aviso expresso de 'venda final';\n• Boquilhas de instrumentos de sopro (por rígidas questões de higiene sanitária)."}], 'out_of_scope_alert': None}
```

### 🎸 Resposta do Tom (Empório da Música):
O **Crafter HT-100 Folk Aço Natural** está em promoção com um desconto de **18%**, saindo por **R$ 1.967,18**. 

### Sobre o pagamento no PIX:
Infelizmente, o desconto de 5% do PIX não é cumulativo com o valor promocional já aplicado. Portanto, o preço para pagamento no PIX será o mesmo de R$ 1.967,18.

### Formas de Pagamento:
- **PIX:** R$ 1.967,18 (sem desconto adicional).
- **Cartão de Débito:** À vista, todas as bandeiras aceitas.
- **Boleto Bancário:** À vista, compensação em até 3 dias úteis.
- **Cartão de Crédito:** Até 12x SEM JUROS, com as seguintes opções de parcelamento:
  - 1x: R$ 1.967,18
  - 2x: R$ 983,59
  - 3x: R$ 655,73
  - 4x: R$ 491,80
  - 5x: R$ 393,44
  - 6x: R$ 327,86
  - 7x: R$ 281,03
  - 8x: R$ 245,90
  - 9x: R$ 218,58
  - 10x: R$ 196,72
  - 11x: R$ 178,83
  - 12x: R$ 163,93

Se precisar de mais alguma coisa, é só avisar! 🎸

---
