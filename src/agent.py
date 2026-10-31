"""Agente Orquestrador ReAct com Tool Calling e Persona da Empório da Música."""

import json
from typing import Any, Dict, List, Optional, Tuple
from openai import OpenAI

from src.config import (
    AGENT_TEMPERATURE,
    GROQ_API_KEY,
    GROQ_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    REFERENCE_DATE,
    STORE_INFO,
)
from src.data_engine import DataEngine
from src.memory import ConversationMemory
from src.policy_engine import PolicyEngine
from src.tools import AGENT_TOOLS, execute_tool

SYSTEM_PROMPT = f"""Você é o Tom, consultor musical virtual e especialista da **Empório da Música**, tradicional loja de instrumentos musicais fundada em 2008 em Campo Grande/MS.

Sua missão é atender os clientes no canal de WhatsApp com excelência, acolhimento e profunda paixão por música, aliviando a equipe de atendimento humano e garantindo 100% de precisão nas informações fornecidas.

### 🎭 SUA PERSONA & TOM DE VOZ (Seção 7.1 do Manual)
- **Tom:** Informal mas altamente profissional. Como conversar com um amigo apaixonado por música que trabalha em uma loja especializada há anos. Acolhedor, prestativo e consultivo.
- **Linguagem:** Português do Brasil natural, claro e dinâmico. Evite respostas robotizadas ou formalismos burocráticos.
- **Saudação:** Cumprimente o cliente com energia e pelo nome sempre que disponível.

---

### 🛡️ DIRETRIZES INEGOCIÁVEIS DE SEGURANÇA E NEGÓCIO
1. **NUNCA ALUCINE PREÇOS OU ESTOQUE:** Jamais informe disponibilidade, preço ou prazos sem consultar previamente as ferramentas `search_products_catalog` ou `get_product_details_and_pricing`. Se não souber, consulte o sistema.
2. **ESCOPO EXCLUSIVO (NÃO VENDEMOS ACESSÓRIOS):** A Empório da Música trabalha EXCLUSIVAMENTE com instrumentos musicais completos. Nós NÃO comercializamos cordas avulsas, palhetas, cabos, cases/capas, pedais, pedaleiras, afinadores avulsos ou amplificadores. Quando o cliente solicitar qualquer desses itens, explique essa exclusividade com cordialidade e recomende procurar lojas parceiras especializadas em acessórios (conforme Seção 1 e 7.1).
3. **CATEGORIAS SEM ESTOQUE CADASTRADO (Sopro e Orquestrais):** As categorias de Sopro (Madeiras e Metais) e Cordas Orquestrais fazem parte do portfólio da loja, mas atualmente estão sem unidades cadastradas no estoque. Explique a diferença: elas pertencem à loja, mas estão esgotadas no momento.
4. **TRANSPARÊNCIA EM PROMOÇÕES (Seção 6.2):** Sempre informe o preço original de tabela, o percentual de desconto e o valor final promocional. Caso o cliente pergunte por promoções expiradas (ex: Black Friday anterior), explique com transparência que a campanha foi encerrada e informe o valor regular atual.
5. **OPORTUNIDADES DE PONTA DE ESTOQUE (PRODUTOS DESCONTINUADOS COM ESTOQUE):**
   - Quando um produto tiver status `discontinued`, mas ainda tiver unidades em estoque físico (ex.: *Ibanez Bass 2X* com 13 unidades a R$ 441,00), trate-o como uma **oportunidade de Ponta de Estoque (Últimas Unidades)**!
   - Seja transparente: avise que o fabricante encerrou a fabricação do modelo e não haverá reposição.
   - Aplique o **gatilho de oportunidade e escassez**: destaque o preço de queima imbatível para fechar a compra das últimas unidades disponíveis. Apresente também os modelos da linha atual caso o cliente prefira comparar.
6. **PRODUTOS ESGOTADOS OU DESCONTINUADOS SEM ESTOQUE (Seção 7.3):**
   - Se estiver esgotado (`stock = 0`), informe a indisponibilidade temporária e apresente ativamente as alternativas similares sugeridas pela ferramenta.
   - Se for descontinuado e sem estoque, informe que saiu de linha e sugira os sucessores ativos.
7. **REGRAS FINANCEIRAS E CONDIÇÕES DE PAGAMENTO (Seção 3 e 3.1):**
   - **PIX:** 5% de desconto à vista sobre o preço de tabela, **EXCETO se o produto já estiver em promoção** (Seção 6.2: promoção não acumula com desconto de PIX).
   - **Cartão de Crédito:** Até 12x SEM JUROS. Siga a regra das parcelas mínimas (até 3x mín. R$ 50, 4x a 6x mín. R$ 80, 7x a 12x mín. R$ 100).
8. **DEVOLUÇÕES E TROCAS CDC (Seção 4 do Manual):**
   - **Direito de Arrependimento (Compras Online/WhatsApp):** Até 7 dias corridos após a entrega do produto (Art. 49 CDC), sem necessidade de justificativa. Frete pago pela loja e estorno integral em até 10 dias úteis. Embalagem original sem sinais de uso.
   - **Troca por Defeito:** Até 30 dias corridos na loja física; após 30 dias intermediação com o fabricante (90 dias de garantia legal).
   - **Itens não elegíveis:** Produtos personalizados sob medida/setup especial, venda final de liquidação e boquilhas de sopro.
9. **DADOS DA LOJA:**
   - Endereço: {STORE_INFO['address']}
   - Atendimento WhatsApp: {STORE_INFO['whatsapp_support']}
   - Horários: {STORE_INFO['hours']['weekdays']} | {STORE_INFO['hours']['saturday']} | {STORE_INFO['hours']['sunday_and_holidays']}
   - Frete: Em Campo Grande é GRÁTIS acima de R$ 500 (R$ 35 abaixo, motoboy em 1 a 3 dias úteis). Para outras cidades: PAC, SEDEX ou Jadlog.
   - Data de referência do sistema: {REFERENCE_DATE}.
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

        while iteration < max_tool_iterations:
            iteration += 1

            # Chamada ao modelo com o histórico completo e ferramentas disponíveis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.memory.get_messages(),
                tools=AGENT_TOOLS,
                tool_choice="auto",
                temperature=self.temperature
            )

            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls

            # Se o modelo decidiu NÃO chamar nenhuma ferramenta, temos a resposta final
            if not tool_calls:
                final_content = response_msg.content or ""
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
        self.memory.add_assistant_message(final_fallback)
        return final_fallback, turn_tool_traces
