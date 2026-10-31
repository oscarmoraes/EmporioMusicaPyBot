"""Definição dos Schemas de Ferramentas (Function Calling) e Executor de Tools."""

import json
from typing import Any, Dict, List

from src.data_engine import DataEngine
from src.policy_engine import PolicyEngine

# Schemas no padrão OpenAI Tools (compatíveis também com Groq e Gemini via OpenAI API)
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products_catalog",
            "description": (
                "Busca instrumentos musicais no catálogo da Empório da Música. "
                "Calcula preços promocionais ativos automaticamente. Permite filtrar por "
                "categoria (ex: violões, guitarras, baixos, baterias, teclados, ukuleles), "
                "faixa de preço efetivo (min_price e max_price), tipo de corda (nylon ou aço) "
                "e termos de busca no nome/especificações."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termo de busca textual (ex: 'Folk', 'Strato', 'Estudante', 'Yamaha')"
                    },
                    "category": {
                        "type": "string",
                        "description": "Categoria do instrumento (ex: 'violão', 'guitarra', 'baixo', 'bateria', 'teclado', 'ukulele', 'sopro')"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Preço máximo em Reais (R$) considerado sobre o preço efetivo/promocional. Preencha APENAS se o cliente citar um valor numérico explícito de teto (ex: 'até 1000'); NUNCA invente um teto se o cliente pedir apenas 'do mais barato ao mais caro'."
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Preço mínimo em Reais (R$). Preencha APENAS se o cliente citar um valor numérico explícito de piso (ex: 'acima de 10000')."
                    },
                    "strings_filter": {
                        "type": "string",
                        "enum": ["nylon", "aço", "steel"],
                        "description": "Tipo de encordoamento para violões e instrumentos de corda"
                    },
                    "electronics_filter": {
                        "type": "string",
                        "enum": ["yes", "no"],
                        "description": "'yes' para elétricos/eletroacústicos, 'no' para acústicos puros"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details_and_pricing",
            "description": (
                "Obtém a ficha técnica completa, disponibilidade exata de estoque, status comercial "
                "(incluindo se é ponta de estoque/últimas unidades), histórico de promoções ativas e expiradas, "
                "simulação de PIX (com desconto de 5% se não promocional), parcelas em até 12x sem juros no cartão "
                "e elegibilidade para pagamento combinado (> R$ 2.000,00). SEMPRE chame esta ferramenta quando o cliente "
                "mencionar um modelo específico de instrumento, mesmo que o cliente já cite um preço na mensagem."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id_or_name": {
                        "type": "string",
                        "description": "ID numérico do produto (ex: '95') ou nome/modelo (ex: 'Takamine GD20', 'Crafter HT-100', 'Ibanez Bass 2X')"
                    }
                },
                "required": ["product_id_or_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_customer_orders",
            "description": (
                "Consulta o status de pedidos de clientes, código de rastreamento, itens adquiridos "
                "e avalia automaticamente a elegibilidade para devolução por arrependimento (7 dias corridos do CDC) "
                "ou troca por defeito (30 dias na loja / 90 dias de garantia legal). Permite buscar por número do pedido, "
                "código de rastreio ou dados do cliente (nome, telefone ou email)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "Número de identificação do pedido (ex: 1, 8, 19)"
                    },
                    "tracking_code": {
                        "type": "string",
                        "description": "Código de rastreamento no padrão BR (ex: 'BRAB1234567BR', 'BRJL5544332BR')"
                    },
                    "customer_query": {
                        "type": "string",
                        "description": "Nome do cliente, telefone com DDD ou endereço de email"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consult_store_policies",
            "description": (
                "Consulta as políticas oficiais e normas operacionais da Empório da Música: "
                "horários de funcionamento, regras de frete e prazos (Campo Grande motoboy vs Correios/Jadlog), "
                "formas de pagamento e parcelamento, regras de devolução e arrependimento CDC, garantias, LGPD "
                "e identificação de itens fora de escopo (a loja não comercializa acessórios avulsos)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Dúvida ou termos a pesquisar nas normas (ex: 'prazo para devolução', 'endereço da loja', 'frete para dourados', 'garantia de violão')"
                    },
                    "specific_topic": {
                        "type": "string",
                        "enum": [
                            "institucional", "horarios", "pagamento", "trocas_devolucoes",
                            "frete_entregas", "promocoes", "atendimento_whatsapp",
                            "garantia", "privacidade_lgpd", "disposicoes_finais"
                        ],
                        "description": "Tópico normativo específico caso o assunto já esteja claramente identificado"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    data_engine: DataEngine,
    policy_engine: PolicyEngine
) -> Dict[str, Any]:
    """Executa a ferramenta solicitada pelo LLM e retorna o resultado estruturado em JSON."""
    if tool_name == "search_products_catalog":
        return data_engine.search_catalog(
            query=arguments.get("query"),
            category=arguments.get("category"),
            max_price=arguments.get("max_price"),
            min_price=arguments.get("min_price"),
            strings_filter=arguments.get("strings_filter"),
            electronics_filter=arguments.get("electronics_filter")
        )

    elif tool_name == "get_product_details_and_pricing":
        return data_engine.get_product_details(
            product_id_or_name=arguments.get("product_id_or_name")
        )

    elif tool_name == "lookup_customer_orders":
        return data_engine.lookup_orders(
            order_id=arguments.get("order_id"),
            tracking_code=arguments.get("tracking_code"),
            customer_query=arguments.get("customer_query")
        )

    elif tool_name == "consult_store_policies":
        return policy_engine.retrieve_policies(
            query=arguments.get("query", ""),
            specific_topic=arguments.get("specific_topic")
        )

    else:
        return {"error": f"Ferramenta desconhecida: '{tool_name}'"}
