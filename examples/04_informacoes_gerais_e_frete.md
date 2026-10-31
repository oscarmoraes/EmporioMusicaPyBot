# Cenário 4: Informações Institucionais, Horários e Política de Frete e Entregas

**Arquivo:** `04_informacoes_gerais_e_frete.md`  
**Descri??o do Cen?rio:** Demonstra o agente apresentando endereço físico, horários de funcionamento presencial/WhatsApp e detalhando as regras de frete (motoboy em Campo Grande com frete grátis acima de R$ 500 vs Correios/Jadlog para outras cidades e cotação individual para instrumentos de grande porte).

---

## ?? Turno 1 ? Cliente:
> **"Qual o endereço da loja e os horários de atendimento?"**

### ?? Resposta do Tom (Emp?rio da M?sica):
A Empório da Música está localizada na Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, CEP 79202-333.

Nossos horários de atendimento são:
- **Segunda a Sexta-feira:** 09:00 às 18:00
- **Sábado:** 09:00 às 13:00
- **Domingo e Feriados:** Fechado

Se precisar de mais alguma informação, é só avisar! 🎶

---

## ?? Turno 2 ? Cliente:
> **"Como funciona a entrega? Eu moro aqui em Campo Grande, mas meu primo que vai comprar uma bateria acústica mora no interior, em Dourados/MS."**

### ??? Chamadas de Ferramentas (Sistemas Consultados):
- **Ferramenta:** `consult_store_policies`
  - **Par?metros:** `{'query': 'frete entregas', 'specific_topic': 'frete_entregas'}`
  - **Resposta do Sistema:**
```json
{'matched_topic': 'frete_entregas', 'sections': [{'section_key': 'frete_entregas', 'title': '5. Política de Frete, Entregas e Rastreamento', 'content': '5.1 Entregas na Região Metropolitana de Campo Grande/MS:\n• Frete GRÁTIS para pedidos acima de R$ 500,00.\n• Taxa fixa de R$ 35,00 para pedidos abaixo de R$ 500,00.\n• Prazo: 1 a 3 dias úteis (entrega por motoboy próprio; cliente contactado por telefone antes da entrega).\n\n5.2 Entregas para Outras Cidades e Estados (Interior de MS e Brasil):\n• PAC (Correios): 5 a 12 dias úteis (rastreamento e seguro inclusos).\n• SEDEX (Correios): 2 a 5 dias úteis (rastreamento e seguro inclusos).\n• Jadlog (.package): 3 a 8 dias úteis (rastreamento e seguro inclusos).\n• INSTRUMENTOS DE GRANDE PORTE: Baterias acústicas, pianos digitais e contrabaixos acústicos podem exigir frete especial com cotação individual.\n• SEGURO E PROCEDIMENTO EM CASO DE AVARIA NO TRANSPORTE: Todos os envios incluem seguro contra extravios e danos durante o transporte. Em caso de caixa amassada, rasgada ou avaria no transporte, o cliente DEVE RECUSAR O RECEBIMENTO NO ATO DA ENTREGA e entrar em contato imediatamente com a loja pelo WhatsApp (67) 3321-4500 ou telefone (67) 3341-4444 para acionamento do seguro e envio de novo instrumento.\n\n5.3 Código de Rastreamento:\n• Enviado por e-mail e WhatsApp assim que despachado. Formato padrão: BR seguido de 9 caracteres alfanuméricos e BR (ex.: BR4K7M2X9P1BR).'}], 'out_of_scope_alert': None}
```
- **Ferramenta:** `consult_store_policies`
  - **Par?metros:** `{'query': 'frete para dourados', 'specific_topic': 'frete_entregas'}`
  - **Resposta do Sistema:**
```json
{'matched_topic': 'frete_entregas', 'sections': [{'section_key': 'frete_entregas', 'title': '5. Política de Frete, Entregas e Rastreamento', 'content': '5.1 Entregas na Região Metropolitana de Campo Grande/MS:\n• Frete GRÁTIS para pedidos acima de R$ 500,00.\n• Taxa fixa de R$ 35,00 para pedidos abaixo de R$ 500,00.\n• Prazo: 1 a 3 dias úteis (entrega por motoboy próprio; cliente contactado por telefone antes da entrega).\n\n5.2 Entregas para Outras Cidades e Estados (Interior de MS e Brasil):\n• PAC (Correios): 5 a 12 dias úteis (rastreamento e seguro inclusos).\n• SEDEX (Correios): 2 a 5 dias úteis (rastreamento e seguro inclusos).\n• Jadlog (.package): 3 a 8 dias úteis (rastreamento e seguro inclusos).\n• INSTRUMENTOS DE GRANDE PORTE: Baterias acústicas, pianos digitais e contrabaixos acústicos podem exigir frete especial com cotação individual.\n• SEGURO E PROCEDIMENTO EM CASO DE AVARIA NO TRANSPORTE: Todos os envios incluem seguro contra extravios e danos durante o transporte. Em caso de caixa amassada, rasgada ou avaria no transporte, o cliente DEVE RECUSAR O RECEBIMENTO NO ATO DA ENTREGA e entrar em contato imediatamente com a loja pelo WhatsApp (67) 3321-4500 ou telefone (67) 3341-4444 para acionamento do seguro e envio de novo instrumento.\n\n5.3 Código de Rastreamento:\n• Enviado por e-mail e WhatsApp assim que despachado. Formato padrão: BR seguido de 9 caracteres alfanuméricos e BR (ex.: BR4K7M2X9P1BR).'}], 'out_of_scope_alert': None}
```

### ?? Resposta do Tom (Emp?rio da M?sica):
Aqui estão as informações sobre a entrega:

### Entregas em Campo Grande/MS:
- **Frete Grátis:** Para pedidos acima de R\$ 500,00.
- **Taxa Fixa:** R\$ 35,00 para pedidos abaixo de R\$ 500,00.
- **Prazo de Entrega:** 1 a 3 dias úteis, realizada por motoboy próprio. O cliente será contatado por telefone antes da entrega.

### Entregas para Dourados/MS (Interior):
- **PAC (Correios):** 5 a 12 dias úteis (com rastreamento e seguro inclusos).
- **SEDEX (Correios):** 2 a 5 dias úteis (com rastreamento e seguro inclusos).
- **Jadlog:** 3 a 8 dias úteis (com rastreamento e seguro inclusos).
- **Instrumentos de Grande Porte:** Baterias acústicas podem exigir frete especial com cotação individual.

### Seguro e Procedimento em Caso de Avaria:
Todos os envios incluem seguro contra extravios e danos. Se a caixa estiver amassada ou rasgada, o cliente deve **recusar o recebimento** e entrar em contato imediatamente com a loja para acionamento do seguro.

### Código de Rastreamento:
O código será enviado por e-mail e WhatsApp assim que o pedido for despachado.

Se precisar de mais alguma coisa, é só avisar! 🎶

---
