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
{'found': True, 'product_id': 95, 'name': 'Takamine GD20 Dreadnought Natural', 'category_name': 'Violões', 'original_price': 2199.0, 'effective_price': 2199.0, 'has_active_promotion': False, 'active_promotion': None, 'expired_promotions': [{'promotion_id': 4, 'discount_percent': 12.0, 'description': 'Oferta Especial', 'is_active': False}], 'expired_promotions_guidance': 'ATENÇÃO (Seção 7.3 — Promoção Expirada): Este produto já teve promoção(ões) anterior(es) que estão ENCERRADAS/VENCIDAS no sistema: [Oferta Especial (12% off)]. Você DEVE informar explicitamente na sua resposta que a campanha (Oferta Especial (12% off)) já foi encerrada/expirou, apresentar o preço atual (R$ 2.199,00) e destacar o desconto de 5% no PIX (R$ 2.089,05).', 'stock_quantity': 5, 'status': 'active', 'is_clearance_opportunity': False, 'status_guidance_for_agent': 'Produto disponível em estoque para pronta entrega. | ATENÇÃO (Seção 7.3 — Promoção Expirada): Este produto já teve promoção(ões) anterior(es) que estão ENCERRADAS/VENCIDAS no sistema: [Oferta Especial (12% off)]. Você DEVE informar explicitamente na sua resposta que a campanha (Oferta Especial (12% off)) já foi encerrada/expirou, apresentar o preço atual (R$ 2.199,00) e destacar o desconto de 5% no PIX (R$ 2.089,05).', 'specs': {'top': 'Cedro Sólido', 'back_sides': 'Sapele', 'neck': 'Mogno', 'strings': 'steel', 'scale': '650mm', 'electronics': 'no', 'color': 'Natural'}, 'description': 'Violão dreadnought Takamine com tampo sólido em cedro. Excelente para fingerstyle com timbre quente e definido.', 'payment_conditions': {'effective_price': 2199.0, 'original_price': 2199.0, 'has_active_promo': False, 'pix': {'price': 2089.05, 'discount_percent': 5, 'discount_applied': True, 'note': 'À vista no PIX com 5% de desconto: R$ 2.089,05 (economia de R$ 109,95).'}, 'debit_card': {'price': 2199.0, 'note': 'À vista no débito (todas as bandeiras).'}, 'boleto': {'price': 2199.0, 'note': 'À vista no boleto bancário (compensação em até 3 dias úteis).'}, 'credit_card': {'max_installments_without_interest': 12, 'available_plans': [{'installments': 1, 'installment_value': 2199.0, 'total': 2199.0, 'interest_free': True}, {'installments': 2, 'installment_value': 1099.5, 'total': 2199.0, 'interest_free': True}, {'installments': 3, 'installment_value': 733.0, 'total': 2199.0, 'interest_free': True}, {'installments': 4, 'installment_value': 549.75, 'total': 2199.0, 'interest_free': True}, {'installments': 5, 'installment_value': 439.8, 'total': 2199.0, 'interest_free': True}, {'installments': 6, 'installment_value': 366.5, 'total': 2199.0, 'interest_free': True}, {'installments': 7, 'installment_value': 314.14, 'total': 2199.0, 'interest_free': True}, {'installments': 8, 'installment_value': 274.88, 'total': 2199.0, 'interest_free': True}, {'installments': 9, 'installment_value': 244.33, 'total': 2199.0, 'interest_free': True}, {'installments': 10, 'installment_value': 219.9, 'total': 2199.0, 'interest_free': True}, {'installments': 11, 'installment_value': 199.91, 'total': 2199.0, 'interest_free': True}, {'installments': 12, 'installment_value': 183.25, 'total': 2199.0, 'interest_free': True}], 'rules': 'Regra 3.1: até 3x (mín. R$ 50,00), 4x a 6x (mín. R$ 80,00), 7x a 12x (mín. R$ 100,00).'}, 'combined_payment': {'allowed': True, 'rule': 'Permitida combinação de formas de pagamento (ex.: PIX + cartão) pois o valor (R$ 2.199,00) é acima de R$ 2.000,00 (Seção 3.1).'}, 'shipping_campo_grande': {'free_shipping': True, 'shipping_fee': 0.0, 'total_with_shipping': 2199.0, 'note': 'Frete GRÁTIS para Campo Grande (pedido acima de R$ 500,00 — entrega por motoboy em 1 a 3 dias úteis).'}}, 'similar_available_alternatives': []}
```

### 🎸 Resposta do Tom (Empório da Música):
Olá! O violão **Takamine GD20 Dreadnought Natural** está disponível por **R$ 2.199,00**. Ele possui um tampo sólido em cedro, ideal para fingerstyle, com um timbre quente e definido.

### Formas de pagamento:
- **À vista no PIX**: R$ 2.089,05 (5% de desconto).
- **À vista no débito**: R$ 2.199,00.
- **À vista no boleto**: R$ 2.199,00 (compensação em até 3 dias úteis).
- **Cartão de crédito**: até 12x sem juros. As parcelas ficam assim:
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

Além disso, você pode combinar formas de pagamento, já que o valor total é acima de R$ 2.000,00.

Se precisar de mais alguma informação ou ajuda, é só avisar! 🎶

---

## 👤 Turno 2 — Cliente:
> **"E o violão Crafter HT-100? Ele está em promoção? Se eu pagar no PIX tenho mais 5% de desconto sobre o valor promocional?"**

### 🛠️ Chamadas de Ferramentas (Sistemas Consultados):
- **Ferramenta:** `get_product_details_and_pricing`
  - **Parâmetros:** `{'product_id_or_name': 'Crafter HT-100'}`
  - **Resposta do Sistema:**
```json
{'found': True, 'product_id': 90, 'name': 'Crafter HT-100 Folk Aço Natural', 'category_name': 'Violões', 'original_price': 2399.0, 'effective_price': 1967.18, 'has_active_promotion': True, 'active_promotion': {'promotion_id': 19, 'discount_percent': 18.0, 'description': 'Desconto Exclusivo', 'is_active': True}, 'expired_promotions': [], 'expired_promotions_guidance': None, 'stock_quantity': 3, 'status': 'active', 'is_clearance_opportunity': False, 'status_guidance_for_agent': 'Produto disponível em estoque para pronta entrega.', 'specs': {'top': 'Spruce Engelmann Sólido', 'back_sides': 'Mogno', 'neck': 'Mogno', 'strings': 'steel', 'scale': '648mm', 'electronics': 'no', 'color': 'Natural'}, 'description': 'Violão folk de alta qualidade com tampo sólido em Spruce Engelmann. Projeção sonora superior e acabamento impecável.', 'payment_conditions': {'effective_price': 1967.18, 'original_price': 2399.0, 'has_active_promo': True, 'pix': {'price': 1967.18, 'discount_percent': 0, 'discount_applied': False, 'note': 'Preço promocional ativo de R$ 1.967,18: desconto de 5% do PIX não cumulativo (Seção 6.2).'}, 'debit_card': {'price': 1967.18, 'note': 'À vista no débito (todas as bandeiras).'}, 'boleto': {'price': 1967.18, 'note': 'À vista no boleto bancário (compensação em até 3 dias úteis).'}, 'credit_card': {'max_installments_without_interest': 12, 'available_plans': [{'installments': 1, 'installment_value': 1967.18, 'total': 1967.18, 'interest_free': True}, {'installments': 2, 'installment_value': 983.59, 'total': 1967.18, 'interest_free': True}, {'installments': 3, 'installment_value': 655.73, 'total': 1967.18, 'interest_free': True}, {'installments': 4, 'installment_value': 491.8, 'total': 1967.18, 'interest_free': True}, {'installments': 5, 'installment_value': 393.44, 'total': 1967.18, 'interest_free': True}, {'installments': 6, 'installment_value': 327.86, 'total': 1967.18, 'interest_free': True}, {'installments': 7, 'installment_value': 281.03, 'total': 1967.18, 'interest_free': True}, {'installments': 8, 'installment_value': 245.9, 'total': 1967.18, 'interest_free': True}, {'installments': 9, 'installment_value': 218.58, 'total': 1967.18, 'interest_free': True}, {'installments': 10, 'installment_value': 196.72, 'total': 1967.18, 'interest_free': True}, {'installments': 11, 'installment_value': 178.83, 'total': 1967.18, 'interest_free': True}, {'installments': 12, 'installment_value': 163.93, 'total': 1967.18, 'interest_free': True}], 'rules': 'Regra 3.1: até 3x (mín. R$ 50,00), 4x a 6x (mín. R$ 80,00), 7x a 12x (mín. R$ 100,00).'}, 'combined_payment': {'allowed': False, 'rule': 'NÃO permitida combinação de formas de pagamento (ex.: PIX + cartão) pois o valor (R$ 1.967,18) não ultrapassa R$ 2.000,00 (Seção 3.1).'}, 'shipping_campo_grande': {'free_shipping': True, 'shipping_fee': 0.0, 'total_with_shipping': 1967.18, 'note': 'Frete GRÁTIS para Campo Grande (pedido acima de R$ 500,00 — entrega por motoboy em 1 a 3 dias úteis).'}}, 'similar_available_alternatives': []}
```

### 🎸 Resposta do Tom (Empório da Música):
O violão **Crafter HT-100 Folk Aço Natural** está em promoção com um preço especial de **R$ 1.967,18**, que já inclui um desconto de 18%!

### Formas de pagamento:
- **À vista no PIX**: R$ 1.967,18 (não há desconto adicional de 5% sobre o valor promocional, pois o desconto do PIX não é cumulativo).
- **À vista no débito**: R$ 1.967,18.
- **À vista no boleto**: R$ 1.967,18 (compensação em até 3 dias úteis).
- **Cartão de crédito**: até 12x sem juros. As parcelas ficam assim:
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

E o frete é GRÁTIS para Campo Grande!

Se precisar de mais alguma informação ou ajuda, é só avisar! 🎸

---
