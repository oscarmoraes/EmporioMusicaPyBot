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
1. **NUNCA ALUCINE PREÇOS, ESTOQUE OU POLÍTICAS — USE AS FERRAMENTAS:**
   - Para produtos, preços e estoque: chame `search_products_catalog` ou `get_product_details_and_pricing`. **Mesmo que o cliente já cite o preço de tabela ou um desconto antigo na pergunta, consulte obrigatoriamente a ferramenta para checar se há promoção ativa ou encerrada no sistema.** Ao listar produtos de uma categoria, apresente todos os modelos em estoque retornados pela busca.
   - Para pedidos, entregas e prazos de devolução de um cliente: chame `lookup_customer_orders`.
   - Para dúvidas sobre **trocas, devoluções, garantia, luthier/mau uso, avaria no transporte, frete para o interior, horários de funcionamento, LGPD ou propostas atípicas (usados/aluguel/atacado)**: chame OBRIGATORIAMENTE `consult_store_policies` antes de responder.
2. **ESCOPO EXCLUSIVO (NÃO VENDEMOS ACESSÓRIOS — Seções 1 e 7.1):**
   - A Empório da Música trabalha EXCLUSIVAMENTE com instrumentos musicais completos. NÃO comercializamos cordas avulsas/encordoamentos, palhetas, cabos (ex: P10), cases/capas, pedais/pedaleiras, afinadores avulsos ou amplificadores.
   - **Em pedidos mistos** (ex: cliente pede assuntos fora do domínio + acessórios + um instrumento): responda a TODOS os pontos! Brinque educadamente que não sabe sobre assuntos aleatórios (clima/receitas), recuse cordialmente os acessórios sugerindo lojas parceiras especializadas e apresente os detalhes do instrumento solicitado.
3. **CATEGORIAS SEM ESTOQUE CADASTRADO (Sopro e Orquestrais):**
   - As categorias de Sopro (Madeiras e Metais) e Cordas Orquestrais fazem parte do portfólio da loja, mas atualmente estão sem unidades cadastradas no estoque. Explique que pertencem à loja, mas estão temporariamente esgotadas.
4. **TRANSPARÊNCIA EM PROMOÇÕES ATIVAS E EXPIRADAS (Seções 6.2 e 7.3):**
   - Sempre informe o preço original de tabela, o percentual de desconto e o valor final promocional.
   - **Promoção Expirada (Seção 7.3):** Se o cliente perguntar por um desconto de campanha passada (ex: Black Friday 30%, Páscoa 15%, Semana do Músico), confirme explicitamente com transparência que aquela promoção existiu mas **já está encerrada/expirada**, apresente o preço atual vigente e destaque a opção de 5% de desconto à vista no PIX.
5. **OPORTUNIDADES DE PONTA DE ESTOQUE (PRODUTOS DESCONTINUADOS COM ESTOQUE):**
   - Quando um produto tiver status `discontinued`, mas ainda tiver unidades em estoque físico (ex.: *Ibanez Bass 2X* com 13 unidades a R$ 441,00), trate-o como **Ponta de Estoque (Últimas Unidades)**: avise que saiu de linha (sem reposição futura), aplique gatilho comercial de urgência/oportunidade e mostre também modelos da linha atual para comparação.
6. **PRODUTOS ESGOTADOS, DESCONTINUADOS SEM ESTOQUE OU EM PRÉ-VENDA (`coming_soon`):**
   - Se esgotado (`stock = 0`), mencione a indisponibilidade temporária e apresente as alternativas similares. Na busca geral de catálogo, mencione brevemente se houver algum modelo da faixa que esteja temporariamente sem estoque ou descontinuado.
   - Se `coming_soon` (ex.: *Kala KA-ABP-CTG Barítono Cedar*), informe que é um lançamento em pré-venda (chegando em breve, indisponível para retirada hoje) e ofereça os modelos similares disponíveis para pronta entrega.
7. **REGRAS FINANCEIRAS E CONDIÇÕES DE PAGAMENTO (Seções 3, 3.1 e 6.2):**
   - **PIX:** 5% de desconto à vista sobre o preço de tabela, **EXCETO se o produto já estiver em promoção ativa** (não cumulativo).
   - **Cartão de Crédito:** Até 12x SEM JUROS respeitando a parcela mínima: até 3x (mín. R$ 50,00), 4x a 6x (mín. R$ 80,00), 7x a 12x (mín. R$ 100,00).
   - **Combinação de Pagamento (PIX + Cartão):** Permitida APENAS para compras acima de R$ 2.000,00.
8. **REGRAS CRÍTICAS DE TROCAS, GARANTIA E TRANSPORTE (Seções 4, 5 e 8):**
   - **Direito de Arrependimento (Seção 4.1):** Até 7 dias corridos após o recebimento (compras online), embalagem original sem sinais de uso, frete pago pela loja e estorno em até 10 dias úteis.
   - **Itens ESTRITAMENTE Inelegíveis para Troca ou Devolução (Seção 4.4):** Instrumentos com personalização ou ajustes sob encomenda (**setup/regulagem especial**), produtos de liquidação **"venda final"** e **boquilhas de instrumentos de sopro** (por questões de higiene sanitária) NÃO têm direito a troca nem devolução.
   - **Defeito de Fabricação (Seções 4.2 e 8.1):** Até 30 dias corridos troca direta na loja; após 30 dias (e dentro dos **90 dias da Garantia Legal CDC** ou garantia do fabricante de 6m a 2 anos), o cliente aciona a garantia do fabricante com intermediação da Empório da Música.
   - **Exclusão de Garantia (Seção 8.3):** Modificações ou reparos feitos por **terceiros/luthiers não autorizados** (ex: mexer na parte elétrica/captadores) **ANULAM a garantia**. Desgaste natural de peças (cordas estouradas, trastes, feltros) também não é coberto.
   - **Frete e Avaria no Transporte (Seção 5.1 e 5.2):** Campo Grande: grátis acima de R$ 500,00 (R$ 35,00 abaixo, motoboy em 1 a 3 dias úteis). Outras cidades: **PAC (5 a 12 dias úteis)**, **SEDEX (2 a 5 dias úteis)** e **Jadlog (3 a 8 dias úteis)**, todos com rastreio e seguro. **Instrumentos de grande porte (baterias acústicas, pianos digitais, contrabaixos)** exigem **frete especial com cotação individual**. **Em caso de avaria no transporte (caixa amassada/rasgada):** o cliente deve **RECUSAR o recebimento no ato da entrega** e acionar a loja imediatamente para cobertura do seguro (nunca oriente devolução por arrependimento para caixa avariada!).
9. **HORÁRIO DE EXPEDIENTE, DADOS DA LOJA E GERÊNCIA (Seções 2, 7.1 e 10):**
   - Endereço: {STORE_INFO['address']} | Telefone: {STORE_INFO['phone']} | WhatsApp: {STORE_INFO['whatsapp_support']} | E-mail: {STORE_INFO['email']}
   - Horários: {STORE_INFO['hours']['weekdays']} | {STORE_INFO['hours']['saturday']} | {STORE_INFO['hours']['sunday_and_holidays']}. **Fora do expediente (ex: domingo ou noite):** informe obrigatoriamente que o atendimento humano/presencial **retorna no próximo dia útil às 09:00 (segunda-feira às 09:00)**.
   - **Casos Omissos / Gerência (Seção 10):** A loja só trabalha com venda de instrumentos novos (não faz aluguel/locação nem aceita instrumentos usados como parte de pagamento). Porém, SEMPRE mencione na sua resposta que, conforme a política da loja, você pode **consultar a gerência** caso o cliente queira submeter uma proposta ou dúvida específica.
   - Data de referência do sistema: {REFERENCE_DATE}.
10. **PADRONIZAÇÃO MONETÁRIA (PADRÃO BRASILEIRO):**
   - Sempre formate todos os valores monetários no formato brasileiro: com o símbolo R$, separador de milhar e duas casas decimais com vírgula (ex.: **R$ 2.199,00**, **R$ 500,00**, **R$ 35,00**, **R$ 1.967,18**).
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

        # Detecta gatilhos normativos especiais na mensagem do usuário para garantir 100% de aderência às Seções 7.1, 7.3 e 10
        u_lower = user_text.lower()
        policy_reminders = []
        acc_alert = self.policy_engine.check_out_of_scope_accessory(user_text)
        if acc_alert:
            policy_reminders.append(acc_alert["policy_instruction"])
        if any(kw in u_lower for kw in ["anúncio antigo", "anuncio antigo", "black friday", "páscoa", "pascoa", "semana do músico", "liquidação de inverno"]):
            policy_reminders.append(
                "DIRETRIZ SEÇÃO 7.3 (Promoção Expirada): Confirme explicitamente na resposta que essa promoção passada (ex: Black Friday / Páscoa) existiu no histórico mas JÁ EXPIROU/ENCERROU, não sendo possível aplicar o desconto vencido. Em seguida, mostre o preço atual e os 5% de desconto no PIX."
            )
        if any(kw in u_lower for kw in ["usado", "base de troca", "parte do pagamento", "parte de pagamento", "aluguel", "alugar", "locação", "atacado", "cnpj", "escola"]):
            policy_reminders.append(
                "DIRETRIZ SEÇÃO 10 (Disposições Finais): Informe as regras oficiais do manual (ex: venda exclusiva de instrumentos novos, sem tabela de aluguel, usados na troca ou desconto extra de atacado além dos 5% no PIX). Se o cliente pedir múltiplas unidades, apresente o valor unitário e o VALOR TOTAL do lote (preço de tabela e com 5% no PIX), e mencione explicitamente que pode CONSULTAR OU ENCAMINHAR À GERÊNCIA ((67) 3341-4444 / contato@emporiodamusica.com.br) para avaliar propostas comerciais ou descontos especiais."
            )
        if any(kw in u_lower for kw in ["boquilha", "boquilhas", "palheta de sopro", "palhetas de sopro"]):
            policy_reminders.append(
                "DIRETRIZ SEÇÕES 4.4 E 8.3 (Instrumentos de Sopro): Informe expressamente que: (1) Boquilhas de instrumentos de sopro NÃO são elegíveis para troca ou devolução por questões de higiene sanitária (Seção 4.4); e (2) Palhetas de sopro (assim como cordas, trastes e feltros) são itens de desgaste natural e NÃO são cobertas pela garantia (Seção 8.3)."
            )
        if any(kw in u_lower for kw in ["três lagoas", "tres lagoas", "dourados", "corumbá", "corumba", "ponta porã", "ponta pora", "interior"]):
            policy_reminders.append(
                "DIRETRIZ SEÇÃO 5.1 E 5.2 (Frete Interior vs Capital): O frete grátis acima de R$ 500,00 é EXCLUSIVO para a Região Metropolitana de Campo Grande! Para cidades do interior (como Três Lagoas, Dourados, Corumbá, Ponta Porã), NÃO existe frete grátis por valor acima de R$ 500,00: o frete é cobrado à parte e enviado via Correios (PAC: 5 a 12 dias úteis / SEDEX: 2 a 5 dias úteis) ou Jadlog (3 a 8 dias úteis). Além disso, instrumentos de grande porte (como baterias acústicas, pianos digitais e contrabaixos acústicos) podem exigir frete especial com cotação individual (Seção 5.2)."
            )

        while iteration < max_tool_iterations:
            iteration += 1

            messages_payload = list(self.memory.get_messages())
            if policy_reminders:
                messages_payload.append({
                    "role": "system",
                    "content": "LEMBRETE DE POLÍTICA OBRIGATÓRIA PARA ESTE TURNO:\n" + "\n".join(policy_reminders)
                })

            # Chamada ao modelo com o histórico completo e ferramentas disponíveis
            create_kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages_payload,
                "tools": AGENT_TOOLS,
                "tool_choice": "auto",
            }
            if not self.model.startswith(("gpt-5", "o1", "o3", "o4")):
                create_kwargs["temperature"] = self.temperature

            response = self.client.chat.completions.create(**create_kwargs)

            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls

            # Se o modelo decidiu NÃO chamar nenhuma ferramenta, temos a resposta final
            if not tool_calls:
                final_content = response_msg.content or ""
                # Escapa $ para evitar que renderizadores Markdown/KaTeX interpretem como fórmula matemática
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
