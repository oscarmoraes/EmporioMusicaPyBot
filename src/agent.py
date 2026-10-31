"""Agente Orquestrador ReAct com Tool Calling e Persona da Empório da Música."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from openai import OpenAI

from src.config import (
    AGENT_TEMPERATURE,
    GROQ_API_KEY,
    GROQ_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    REFERENCE_DATE,
)
from src.data_engine import DataEngine
from src.memory import ConversationMemory
from src.policy_engine import PolicyEngine
from src.tools import AGENT_TOOLS, execute_tool

SYSTEM_PROMPT = f"""Você é o Tom, consultor musical virtual da **Empório da Música**, loja especializada em instrumentos musicais em Campo Grande/MS.
Data de referência do sistema: {REFERENCE_DATE}.

### 🎭 PERSONA E TOM DE VOZ
- Tom informal, acolhedor, prestativo e altamente profissional, como um amigo apaixonado por música que trabalha na loja há anos.
- Português do Brasil natural e fluido. Cumprimente o cliente pelo nome sempre que disponível.

---

### 🛠️ REGRA DE OURO: CONSULTA OBRIGATÓRIA ÀS FERRAMENTAS
Você NUNCA deve responder de memória sobre produtos, preços, pedidos, endereço, horários, frete, trocas, garantias, LGPD ou escopo da loja. Consulte obrigatoriamente as ferramentas antes de responder:

1. **Busca de Catálogo por Categoria ou Faixa de Preço (`search_products_catalog`):**
   - Use quando o cliente pedir opções de uma categoria ou faixa de preço.
   - Liste todos os modelos disponíveis em estoque (`available_products`) retornados pela ferramenta.
   - Como `search_products_catalog` já retorna `original_price`, `effective_price`, `pix_price`, `max_installments_without_interest`, `stock_quantity` e `similar_available_alternatives`, evite chamar `get_product_details_and_pricing` repetidamente para cada item da lista.
2. **Consulta de Modelo Específico, Preço, Promoção e Parcelas (`get_product_details_and_pricing`):**
   - Use sempre que o cliente mencionar um instrumento específico pelo nome ou modelo, mesmo que o cliente já cite um valor na mensagem.
   - Respeite estritamente os campos retornados (`status_guidance_for_agent`, `expired_promotions_guidance`, `payment_conditions` e `similar_available_alternatives`).
   - Para itens sem estoque (`stock_quantity = 0`) ou em pré-venda (`coming_soon`), nunca ofereça compra imediata nem desconto PIX para o item indisponível; apresente os preços e o desconto PIX apenas para as alternativas disponíveis em `similar_available_alternatives`.
3. **Consulta de Pedidos, Entregas e Prazos CDC (`lookup_customer_orders`):**
   - Use APENAS quando o cliente fornecer um identificador real na mensagem (número do pedido, código de rastreio, nome do cliente, telefone ou e-mail).
   - Se o cliente relatar uma situação de entrega, avaria na caixa, devolução ou defeito SEM informar número de pedido ou nome, NÃO chame `lookup_customer_orders`; chame `consult_store_policies` para orientar o procedimento oficial da loja.
4. **Consulta às Políticas e Dados Institucionais da Loja (`consult_store_policies`):**
   - Chame OBRIGATORIAMENTE `consult_store_policies` sempre que a mensagem envolver:
     - Endereço físico, telefone, WhatsApp, e-mail ou escopo de atuação da loja (`specific_topic="institucional"`);
     - Horários de funcionamento, atendimento aos sábados/domingos/feriados ou contato fora do expediente (`specific_topic="horarios"`);
     - Formas de pagamento, regras de PIX, parcelamento ou pagamento combinado (`specific_topic="pagamento"`);
     - Trocas, devoluções por arrependimento, prazos, itens personalizados/setup ou itens de higiene/boquilhas (`specific_topic="trocas_devolucoes"`);
     - Frete para a capital ou outras cidades, transportadoras, instrumentos de grande porte ou avaria na entrega (`specific_topic="frete_entregas"`);
     - Regras de promoções ativas/expiradas e não cumulatividade (`specific_topic="promocoes"`);
     - Garantia legal/fabricante, desgaste natural ou reparos por terceiros/luthiers (`specific_topic="garantia"`);
     - Privacidade, uso de dados e exclusão pela LGPD (`specific_topic="privacidade_lgpd"`);
     - Propostas comerciais fora do padrão, como instrumentos usados na troca, aluguel/locação ou descontos de atacado/lote (`specific_topic="disposicoes_finais"`).
   - Ao responder com base em `consult_store_policies`, transmita com fidelidade todos os prazos, valores, procedimentos, canais de contato e a orientação de consulta à gerência contidos nas seções retornadas.

---

### 🛡️ DIRETRIZES DE ESCOPO E FORMATAÇÃO
1. **Fronteira de Domínio e Pedidos Mistos:**
   - Você atua exclusivamente como consultor musical da Empório da Música. É estritamente proibido elaborar conteúdos, listas ou instruções passo a passo sobre temas alheios ao universo musical e à loja.
   - Em perguntas mistas (assunto fora do domínio + acessórios + instrumento): decline o assunto alheio em no máximo 1 frase curta e bem-humorada, recuse os acessórios avulsos conforme a política da loja (sugerindo lojas parceiras) e apresente os dados do instrumento consultado.
2. **Padronização Monetária e Concisão:**
   - Formate valores monetários no padrão brasileiro com `R$`, ponto de milhar e duas casas decimais com vírgula.
   - Seja fluido, direto e objetivo para leitura no WhatsApp (entre 100 e 220 palavras), sem blocos repetitivos de resumo no rodapé.
"""


class EmporioAgent:
    """Orquestrador do Agente da Empório da Música utilizando Tool Calling nativo."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = AGENT_TEMPERATURE
    ):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        self.temperature = temperature

        # Suporte opcional a Groq ou OpenAI
        if not self.api_key and GROQ_API_KEY:
            self.api_key = GROQ_API_KEY
            self.model = GROQ_MODEL
            base_url = "https://api.groq.com/openai/v1"

        if not self.api_key:
            raise ValueError(
                "Nenhuma chave de API configurada. Defina OPENAI_API_KEY no arquivo .env"
            )

        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.data_engine = DataEngine()
        self.policy_engine = PolicyEngine()
        self.memory = ConversationMemory(system_prompt=SYSTEM_PROMPT)

    def reset_conversation(self) -> None:
        """Reinicia a sessão de conversa."""
        self.memory.reset()

    def process_message(self, user_text: str, max_tool_iterations: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
        """Executa o ciclo ReAct do agente: interpreta, chama ferramentas e gera a resposta."""
        self.memory.add_user_message(user_text)
        iteration = 0
        turn_tool_traces: List[Dict[str, Any]] = []

        # Verifica proativamente se há menção a acessórios fora do escopo da loja (Seção 1 e 7.1)
        acc_alert = self.policy_engine.check_out_of_scope_accessory(user_text)

        while iteration < max_tool_iterations:
            iteration += 1

            messages_payload = list(self.memory.get_messages())
            if acc_alert:
                messages_payload.append({
                    "role": "system",
                    "content": "ALERTA DE ESCOPO (SEÇÃO 1 E 7.1):\n" + acc_alert["policy_instruction"]
                })

            # No primeiro turno sem histórico de ferramentas, obriga a consulta às ferramentas (tool_choice='required')
            must_call_tool = (iteration == 1 and len(self.memory.tool_trace) == 0)

            create_kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages_payload,
                "tools": AGENT_TOOLS,
                "tool_choice": "required" if must_call_tool else "auto",
            }
            if not self.model.startswith(("gpt-5", "o1", "o3", "o4")):
                create_kwargs["temperature"] = self.temperature
            elif self.model.startswith("gpt-5"):
                create_kwargs["reasoning_effort"] = "low"

            response = self.client.chat.completions.create(**create_kwargs)

            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls

            # Se o modelo decidiu NÃO chamar nenhuma ferramenta, temos a resposta final
            if not tool_calls:
                final_content = response_msg.content or ""
                # Sanitização determinística de domínio oficial (qualquer variação de typo no domínio da loja) e escape de cifrão para Markdown/KaTeX
                final_content = re.sub(
                    r"@emporioda[a-z]+\.com(\.br)?",
                    "@emporiodamusica.com.br",
                    final_content,
                    flags=re.IGNORECASE,
                )
                final_content = re.sub(r"(?<!\\)\$", r"\$", final_content)
                self.memory.add_assistant_message(final_content)
                return final_content, turn_tool_traces

            # Se o modelo solicitou chamada de ferramentas
            self.memory.add_assistant_message(
                content=response_msg.content,
                tool_calls=[
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            )

            # Executa cada ferramenta solicitada
            for tc in tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except Exception:
                    fn_args = {}

                # Executa no motor de dados ou políticas
                tool_output = execute_tool(
                    tool_name=fn_name,
                    arguments=fn_args,
                    data_engine=self.data_engine,
                    policy_engine=self.policy_engine
                )

                # Se a mensagem do usuário continha pedido de acessórios fora de escopo (pedido misto),
                # anexa o alerta normativo da Seção 7.1 para que o agente não esqueça de redirecionar!
                acc_alert = self.policy_engine.check_out_of_scope_accessory(user_text)
                if acc_alert and isinstance(tool_output, dict) and "out_of_scope_alert" not in tool_output:
                    tool_output["out_of_scope_alert"] = acc_alert

                tool_output_str = json.dumps(tool_output, ensure_ascii=False)

                # Registra no histórico e rastreio
                self.memory.add_tool_message(
                    tool_call_id=tc.id,
                    content=tool_output_str
                )
                self.memory.record_tool_call(fn_name, fn_args, tool_output)
                turn_tool_traces.append({
                    "tool": fn_name,
                    "arguments": fn_args,
                    "result": tool_output
                })

        # Caso atinja o limite máximo de iterações sem resposta direta
        final_fallback = "Olá! Consegui consultar todas as informações no sistema da Empório da Música. Como mais posso te ajudar com seu instrumento hoje?"
        final_fallback = re.sub(r"(?<!\\)\$", r"\$", final_fallback)
        self.memory.add_assistant_message(final_fallback)
        return final_fallback, turn_tool_traces
