"""Gera as 5 conversas de exemplo executando o agente real com o modelo OpenAI."""

import os
from pathlib import Path
from src.agent import EmporioAgent

EXAMPLES_DIR = Path("examples")
EXAMPLES_DIR.mkdir(exist_ok=True)

scenarios = [
    {
        "filename": "01_catalogo_violoes_ate_1000.md",
        "title": "Cenário 1: Consulta de Catálogo com Teto de Preço e Atendimento Consultivo",
        "description": "Demonstra o agente consultando violões até R$ 1.000, diferenciando estoque ativo de produtos esgotados (Giannini GF-3D) e descontinuados (Shelby SN-7C), e fornecendo orientação musical para iniciante.",
        "turns": [
            "Quais opções de violões disponíveis custando até R$1000?",
            "Sou iniciante e estou em dúvida entre cordas de nylon e de aço. Qual a diferença e qual você recomenda para começar?"
        ]
    },
    {
        "filename": "02_preco_promo_e_pagamento.md",
        "title": "Cenário 2: Consulta de Preços, Promoções Ativas e Regras de Pagamento (PIX e Cartão)",
        "description": "Demonstra o agente informando o preço do Takamine GD20 (sem promoção, com 5% de desconto no PIX e parcelamento sem juros) e comparando com o Crafter HT-100 (que possui promoção ativa de 18% e por isso NÃO acumula desconto de PIX conforme Seção 6.2).",
        "turns": [
            "Quanto custa o Takamine GD20 e quais as formas de pagamento disponíveis?",
            "E o violão Crafter HT-100? Ele está em promoção? Se eu pagar no PIX tenho mais 5% de desconto sobre o valor promocional?"
        ]
    },
    {
        "filename": "03_pedido_e_devolucao_arrependimento.md",
        "title": "Cenário 3: Situação Não-Trivial — Rastreio de Pedidos em Tempo Real, Privacidade (D3) e Aplicação do CDC",
        "description": "Demonstra o agente aplicando a Decisão D3 (solicitando o número do pedido quando o cliente informa apenas o nome, protegendo a privacidade), analisando em tempo real o prazo de 7 dias do Direito de Arrependimento (Art. 49 CDC) no pedido #1 e esclarecendo o motivo de cancelamento do pedido #19 com notas do sistema.",
        "turns": [
            "Olá, sou o Pedro Henrique Oliveira. Poderia verificar como estão meus pedidos na loja?",
            "Claro! Os números são o pedido #1 (violão Martin D-28) e o pedido #19. Sobre o pedido #1: me arrependi da minha compra, posso devolver meu pedido e receber o dinheiro de volta?",
            "Entendi a questão dos 7 dias corridos. E sobre o meu outro pedido (#19) que aparece como cancelado, por qual motivo ele foi cancelado?"
        ]
    },
    {
        "filename": "04_informacoes_gerais_e_frete.md",
        "title": "Cenário 4: Informações Institucionais, Horários e Política de Frete e Entregas",
        "description": "Demonstra o agente apresentando endereço físico, horários de funcionamento presencial/WhatsApp e detalhando as regras de frete (motoboy em Campo Grande com frete grátis acima de R$ 500 vs Correios/Jadlog para outras cidades e cotação individual para instrumentos de grande porte).",
        "turns": [
            "Qual o endereço da loja e os horários de atendimento?",
            "Como funciona a entrega? Eu moro aqui em Campo Grande, mas meu primo que vai comprar uma bateria acústica mora no interior, em Dourados/MS."
        ]
    },
    {
        "filename": "05_fora_de_escopo_e_ponta_de_estoque.md",
        "title": "Cenário 5: Guardrails (Itens Fora de Escopo), Categorias Vazias e Ponta de Estoque Comercial",
        "description": "Demonstra a recusa educada de acessórios avulsos (Seção 1 e 7.1), a explicação sobre categorias vazias do catálogo (Sopro/Violino) e a aplicação de gatilho comercial de Ponta de Estoque (últimas unidades) para o baixo Ibanez Bass 2X (descontinuado com 13 unidades em estoque).",
        "turns": [
            "Boa tarde! Vocês vendem encordoamento para violão de aço, palhetas e amplificador?",
            "Entendi. E vocês vendem saxofone ou violino?",
            "E o contra-baixo Ibanez Bass 2X, vocês ainda vendem?"
        ]
    }
]


def run():
    agent = EmporioAgent()

    for sc in scenarios:
        print(f"\n--- Gerando {sc['filename']} ---")
        agent.reset_conversation()

        doc_lines = [
            f"# {sc['title']}\n",
            f"**Arquivo:** `{sc['filename']}`  ",
            f"**Descrição do Cenário:** {sc['description']}\n",
            "---\n"
        ]

        for turn_idx, user_msg in enumerate(sc["turns"], 1):
            print(f"  [Turno {turn_idx}] Usuário: {user_msg}")
            reply, traces = agent.process_message(user_msg)
            print(f"  [Turno {turn_idx}] Tom respondeu ({len(traces)} tools chamadas)")

            doc_lines.append(f"## 👤 Turno {turn_idx} — Cliente:\n> **\"{user_msg}\"**\n")

            if traces:
                doc_lines.append("### 🛠️ Chamadas de Ferramentas (Sistemas Consultados):")
                for t in traces:
                    doc_lines.append(f"- **Ferramenta:** `{t['tool']}`")
                    doc_lines.append(f"  - **Parâmetros:** `{t['arguments']}`")
                    doc_lines.append(f"  - **Resposta do Sistema:**\n```json\n{t['result']}\n```")
                doc_lines.append("")

            doc_lines.append(f"### 🎸 Resposta do Tom (Empório da Música):\n{reply}\n")
            doc_lines.append("---\n")

        filepath = EXAMPLES_DIR / sc["filename"]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(doc_lines))
        print(f"Salvo em {filepath}")


if __name__ == "__main__":
    run()
