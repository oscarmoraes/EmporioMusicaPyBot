# Cenário 5: Guardrails (Itens Fora de Escopo), Categorias Vazias e Ponta de Estoque Comercial

**Arquivo:** `05_fora_de_escopo_e_ponta_de_estoque.md`  
**Descrição do Cenário:** Demonstra a recusa educada de acessórios avulsos (Seção 1 e 7.1), a explicação sobre categorias vazias do catálogo (Sopro/Violino) e a aplicação de gatilho comercial de Ponta de Estoque (últimas unidades) para o baixo Ibanez Bass 2X (descontinuado com 13 unidades em estoque).

---

## 👤 Turno 1 — Cliente:
> **"Boa tarde! Vocês vendem encordoamento para violão de aço, palhetas e amplificador?"**

### 🎸 Resposta do Tom (Empório da Música):
Boa tarde! 😊 Na Empório da Música, nós trabalhamos exclusivamente com instrumentos musicais completos, então não vendemos acessórios avulsos como encordoamentos, palhetas ou amplificadores. 

Recomendo que você procure lojas parceiras especializadas em acessórios. Se precisar de ajuda com algum instrumento específico, estou aqui para ajudar! 🎸

---

## 👤 Turno 2 — Cliente:
> **"Entendi. E vocês vendem saxofone ou violino?"**

### 🛠️ Chamadas de Ferramentas (Sistemas Consultados):
- **Ferramenta:** `search_products_catalog`
  - **Parâmetros:** `{'category': 'sopro', 'query': 'saxofone'}`
  - **Resposta do Sistema:**
```json
{'query_criteria': {'query': 'saxofone', 'category': 'sopro', 'max_price': None, 'min_price': None, 'strings_filter': None}, 'total_available_in_stock': 0, 'available_products': [], 'clearance_opportunities': [], 'out_of_stock_products': [], 'discontinued_products': [], 'coming_soon_products': [], 'empty_category_notice': {'category_id': 6, 'name': 'Instrumentos de Sopro (Madeiras)', 'description': 'Flautas, clarinetes, saxofones, oboés e outros instrumentos de sopro em madeira', 'notice': "A categoria 'Instrumentos de Sopro (Madeiras)' faz parte do catálogo da Empório da Música, porém no momento todos os modelos estão temporariamente sem unidades cadastradas no estoque."}}
```
- **Ferramenta:** `search_products_catalog`
  - **Parâmetros:** `{'category': 'cordas', 'query': 'violino'}`
  - **Resposta do Sistema:**
```json
{'query_criteria': {'query': 'violino', 'category': 'cordas', 'max_price': None, 'min_price': None, 'strings_filter': None}, 'total_available_in_stock': 0, 'available_products': [], 'clearance_opportunities': [], 'out_of_stock_products': [], 'discontinued_products': [], 'coming_soon_products': [], 'empty_category_notice': {'category_id': 8, 'name': 'Cordas Orquestrais', 'description': 'Violinos, violas, violoncelos e contrabaixos acústicos', 'notice': "A categoria 'Cordas Orquestrais' faz parte do catálogo da Empório da Música, porém no momento todos os modelos estão temporariamente sem unidades cadastradas no estoque."}}
```

### 🎸 Resposta do Tom (Empório da Música):
Infelizmente, no momento, tanto os saxofones quanto os violinos estão temporariamente sem unidades cadastradas no nosso estoque. 😔

Esses instrumentos fazem parte do nosso catálogo, mas estão esgotados no momento. Se você estiver interessado, posso ajudar a encontrar alternativas ou modelos que estejam disponíveis. É só me avisar! 🎶

---

## 👤 Turno 3 — Cliente:
> **"E o contra-baixo Ibanez Bass 2X, vocês ainda vendem?"**

### 🛠️ Chamadas de Ferramentas (Sistemas Consultados):
- **Ferramenta:** `get_product_details_and_pricing`
  - **Parâmetros:** `{'product_id_or_name': 'Ibanez Bass 2X'}`
  - **Resposta do Sistema:**
```json
{'found': True, 'product_id': 136, 'name': 'Ibanez Bass 2X Electric Bass', 'category_name': 'Baixos', 'original_price': 441.0, 'effective_price': 441.0, 'has_active_promotion': False, 'active_promotion': None, 'expired_promotions': [], 'stock_quantity': 13, 'status': 'discontinued', 'is_clearance_opportunity': True, 'status_guidance_for_agent': '[OPORTUNIDADE DE PONTA DE ESTOQUE]: Este modelo foi descontinuado pelo fabricante, mas a loja ainda conta com 13 unidades em saldo físico a um preço excelente. Incentive o cliente a fechar rápido pois são as últimas unidades e não haverá reposição!', 'specs': {'body': 'Ash', 'neck': 'Maple', 'strings': '4', 'color': 'Red'}, 'description': 'Contrabaixo Precision de 4 cordas com captação split-coil. O clássico peso e punch nos graves, perfeito para gravações em estúdio.', 'payment_conditions': {'effective_price': 441.0, 'original_price': 441.0, 'has_active_promo': False, 'pix': {'price': 418.95, 'discount_percent': 5, 'discount_applied': True, 'note': 'À vista no PIX com 5% de desconto: R$ 418.95 (economia de R$ 22.05).'}, 'debit_card': {'price': 441.0, 'note': 'À vista no débito (todas as bandeiras).'}, 'boleto': {'price': 441.0, 'note': 'À vista no boleto bancário (compensação em até 3 dias úteis).'}, 'credit_card': {'max_installments_without_interest': 5, 'available_plans': [{'installments': 1, 'installment_value': 441.0, 'total': 441.0, 'interest_free': True}, {'installments': 2, 'installment_value': 220.5, 'total': 441.0, 'interest_free': True}, {'installments': 3, 'installment_value': 147.0, 'total': 441.0, 'interest_free': True}, {'installments': 4, 'installment_value': 110.25, 'total': 441.0, 'interest_free': True}, {'installments': 5, 'installment_value': 88.2, 'total': 441.0, 'interest_free': True}], 'rules': 'Regra 3.1: até 3x (mín. R$ 50), 4x a 6x (mín. R$ 80), 7x a 12x (mín. R$ 100).'}}, 'similar_available_alternatives': [{'product_id': 138, 'name': 'Music Man Bass 4X Electric Bass', 'price': 7157.0, 'stock_quantity': 9}, {'product_id': 135, 'name': 'Music Man Bass 1X Electric Bass', 'price': 8732.0, 'stock_quantity': 9}, {'product_id': 137, 'name': 'Yamaha Bass 3X Electric Bass', 'price': 11445.0, 'stock_quantity': 11}]}
```

### 🎸 Resposta do Tom (Empório da Música):
Sim, nós ainda temos o **Ibanez Bass 2X** disponível! 🎸

Aqui estão os detalhes:

- **Descrição:** Contrabaixo Precision de 4 cordas com captação split-coil. O clássico peso e punch nos graves, perfeito para gravações em estúdio.
- **Cor:** Vermelho
- **Material do corpo:** Ash
- **Material do braço:** Maple
- **Preço:** R$ 441,00
- **Últimas Unidades:** Temos 13 unidades em estoque, mas atenção: esse modelo foi descontinuado pelo fabricante, então não haverá reposição!

### Condições de Pagamento:
- **À vista no PIX:** R$ 418,95 (5% de desconto)
- **À vista no débito:** R$ 441,00
- **À vista no boleto:** R$ 441,00
- **Cartão de crédito:** Até 5x sem juros (mínimo de R$ 50,00 por parcela).

Se você estiver interessado, é uma ótima oportunidade para garantir o seu! 😊

---
