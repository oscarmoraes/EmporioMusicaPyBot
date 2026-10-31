"""Interface Web Interativa (Streamlit) para o Agente da Empório da Música.

Permite testar visualmente o atendimento do assistente Tom, com persistência
de histórico na sessão, inspeção detalhada das ferramentas acionadas e
botões de atalho para os principais cenários do desafio.
"""

import re
import streamlit as st
from src.agent import EmporioAgent
from src.config import STORE_INFO


def sanitize_markdown(text: str) -> str:
    """Escapa cifrões não-escapados ($ -> \\$) para impedir que o KaTeX do Streamlit

    interprete valores monetários como fórmulas matemáticas (o que causava texto verde/itálico).
    """
    if not text:
        return ""
    return re.sub(r"(?<!\\)\$", r"\$", text)


# Configuração da página
st.set_page_config(
    page_title="Empório da Música — Atendimento Virtual",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização customizada inspirada em chat de atendimento moderno
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #f59e0b;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 8px;
    }
    .status-badge {
        background-color: #10b981;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Inicialização do Agente na sessão
if "agent" not in st.session_state:
    try:
        st.session_state.agent = EmporioAgent()
    except Exception as e:
        st.error(f"Erro ao inicializar o Agente: {e}. Verifique o arquivo .env.")
        st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": (
                "Olá! Seja muito bem-vindo à **Empório da Música**! 🎸🎶\n\n"
                "Eu sou o **Tom**, consultor musical da loja. Posso te ajudar a escolher o instrumento ideal, "
                "verificar preços, promoções ativas, estoque em tempo real ou tirar dúvidas sobre entregas e devoluções.\n\n"
                "Como posso te ajudar hoje?"
            ),
            "traces": []
        }
    ]


# Barra Lateral (Sidebar)
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500&q=80", use_container_width=True)
    st.markdown("### 🎸 Empório da Música")
    st.markdown(f"**Cidade:** {STORE_INFO['address']}")
    st.markdown(f"**WhatsApp:** {STORE_INFO['whatsapp_support']}")
    st.markdown(f"**Horário:**\n- {STORE_INFO['hours']['weekdays']}\n- {STORE_INFO['hours']['saturday']}")

    st.divider()
    st.markdown("### ⚡ Central de Testes (37 Cenários)")
    st.caption("Selecione a bateria e clique em um cenário para enviar ao Tom:")

    scenario_batteries = {
        "⭐ Principais do Edital (7)": {
            "Violões até R$ 1000": "Quais opções de violões disponíveis custando até R$ 1000?",
            "Preço Takamine GD20": "Quanto custa o Takamine GD20 e quais as formas de pagamento?",
            "Promoção Crafter HT-100": "O Crafter HT-100 está em promoção? Consigo mais 5% de desconto no PIX?",
            "Ponta de Estoque Ibanez Bass": "Vocês têm o baixo Ibanez Bass 2X? Ainda é vendido?",
            "Status de Pedido & Arrependimento": "Sou o Pedro Henrique Oliveira. Gostaria de saber o status do meu pedido e se ainda posso devolver por arrependimento.",
            "Acessórios (Fora de Escopo)": "Vocês vendem encordoamento para violão de aço, palhetas e amplificador?",
            "Endereço e Frete": "Qual o endereço da loja e como funciona o frete para Campo Grande e para o interior?"
        },
        "🎸 Bateria A: Catálogo Avançado (01-04)": {
            "01. Violão 7 Cordas (Shelby Descontinuado)": "Quero um violão de 7 cordas para tocar choro. Vi o Shelby SN-7C por R$ 749,00, vocês têm ele?",
            "02. Esgotado Giannini GF-3D + Similares": "Quero comprar o violão Giannini GF-3D Dreadnought Sunburst de R$ 799,90. Tem pronta entrega?",
            "03. Pré-venda Kala Barítono (Coming Soon)": "Vocês têm o ukulele Kala Barítono Cedar (KA-ABP-CTG)? Posso retirar hoje na loja?",
            "04. High-End Estúdio (> R$ 10.000)": "Estou montando um estúdio profissional. Quais são as guitarras e sintetizadores topo de linha que vocês têm acima de R$ 10.000,00?"
        },
        "💳 Bateria B: Finanças & Promoções (05-08)": {
            "05. Cobrança de Promoção Expirada": "Vi num anúncio antigo que o violão Tagima Woodstock estava com 30% de desconto na Black Friday e o Martin D-28 tinha 15% na Páscoa. Ainda consigo esse preço?",
            "06. Escada de Parcelas (Shelby vs Kalani)": "Quero comprar o ukulele Shelby SU-21S Soprano de R$ 159,90 ou o Kalani KAL-700T na promoção. Em quantas vezes sem juros consigo parcelar cada um no cartão?",
            "07. Pagamento Combinado (PIX + Cartão)": "Quero levar o Yamaha APX600 (R$ 1.899,00). Posso dar R$ 500,00 no PIX e parcelar o resto no cartão? E se eu levar o Taylor 110e?",
            "08. Promoção Ohana CK-20 + Regra Frete CG": "Moro em Campo Grande. Se eu comprar o ukulele Ohana CK-20 Concert hoje, quanto pago no total com frete?"
        },
        "📦 Bateria C: Logística & Pedidos (09-12)": {
            "09. Entrega Atrasada + Reclamação (#8)": "Aqui é a Ana Carolina Ferreira, meu telefone é (67) 99654-7821. Meu pedido #8 era pra ter chegado dia 28/02 e até agora nada! Quero abrir uma reclamação!",
            "10. Pedido Pendente Pré-Venda (#14)": "Sou o Diego Fernandes Castro (pedido #14). Paguei no débito dia 15/03 e meu pedido ainda está pendente e sem rastreio. Por quê?",
            "11. Pedido Multi-Itens Alto Valor (#15)": "Olá, sou a Aline Borges Monteiro. Quais itens estão no meu pedido #15? Como ele ainda está pendente, posso cancelar apenas um item ou o pedido todo?",
            "12. Pedidos Múltiplos & Endereço Inválido (#20)": "Sou o Thiago Barbosa Lima. Vi que tenho dois pedidos na loja (#2 e #20). O que aconteceu com o pedido #20?"
        },
        "⚖️ Bateria D: Trocas, CDC & Garantia (13-16)": {
            "13. Defeito 36 Dias (Fora 30d / Dentro 90d CDC)": "Sou a Letícia Gonçalves Rocha (pedido #7, entregue em 17/02/2026). Meu ukulele Shelby deu defeito na tarraxa hoje. Vocês trocam direto na loja?",
            "14. Item Inelegível (Setup Especial / Boquilha)": "Comprei um violão há 3 dias, mas pedi para fazerem um setup e regulagem especial sob encomenda. Não curti a cor, posso trocar? E uma boquilha de sax?",
            "15. Garantia Negada (Luthier / Corda Estourada)": "Comprei uma guitarra há 2 meses, levei num luthier amigo meu pra mexer na elétrica e agora o captador parou, além de uma corda ter estourado. A garantia cobre?",
            "16. Avaria no Transporte (Bateria Amassada)": "Comprei uma bateria acústica Pearl para entregar por transportadora e a caixa acabou de chegar toda amassada e rasgada. O que eu faço?"
        },
        "🛡️ Bateria E: LGPD & Guardrails (17-20)": {
            "17. Exclusão de Dados Pessoais (LGPD)": "Sou a Mariana Costa Santos (mariana.costa@inlook.com). Vocês vendem meus dados para outras empresas de marketing? Quero saber como excluir meu cadastro pela LGPD.",
            "18. Atendimento Domingo & Horário Sábado": "Olá! Estou mandando mensagem no domingo à noite. Tem algum vendedor na loja agora? E no sábado até que horas posso ir aí testar uma bateria?",
            "19. Fora de Domínio + Acessório + Telecaster": "Qual a previsão do tempo em Campo Grande hoje e a receita de bolo de milho? Ah, e quero comprar um cabo P10, um pedal de distorção e uma guitarra Fender Telecaster.",
            "20. Usado na Troca / Aluguel (Gerência)": "Vocês aceitam meu violão usado como parte do pagamento (base de troca) ou fazem aluguel de instrumentos para eventos em Campo Grande?"
        },
        "🔥 Bateria F: Casos Avançados Extras (21-30)": {
            "21. Promoção Crafter HT-100 vs Pagto Combinado": "Vi que o violão Crafter HT-100 Folk Aço Natural tem preço de tabela de R$ 2.399,00. Como ele passa de R$ 2.000, posso dar R$ 900 de entrada no PIX com mais 5% de desconto e parcelar o restante no cartão de crédito?",
            "22. Homônimos Bruno Martins & Frete Interior (#10)": "Olá! Meu e-mail é bruno.martins@jmail.com, sou de Três Lagoas. Quero saber se o meu baixo Music Man do pedido #10 já tem código de rastreio e se o frete saiu grátis por passar de R$ 500.",
            "23. Boleto Vencido (#19) & Garantia >90d (#1)": "Aqui é o Pedro Henrique Oliveira (pedro.oliveira@jmail.com). Por que o meu pedido #19 do Taylor 214ce no boleto foi cancelado? Aproveitando, o Martin D-28 que comprei no pedido #1 em outubro do ano passado ainda está na garantia da loja se der defeito hoje?",
            "24. Cancelado s/ Estoque (#18) & Rozini Hoje": "Sou o Gustavo Teixeira Nunes (gustavo.nunes@inlook.com), de Ponta Porã. Vi que meu pedido #18 foi cancelado. Qual foi o motivo, qual o prazo de reembolso na forma de pagamento original e esse violão Rozini RC-104 já voltou pro estoque hoje?",
            "25. Cancelado no PIX (#17) & Troca por Preferência": "Oi, sou o Matheus Ramos Correia (matheus.correia@hayoo.com.br). Quero confirmar se meu pedido #17 pago no PIX foi cancelado mesmo e em quantos dias úteis sai o reembolso. Se eu comprar outro violão hoje e quiser trocar de modelo em até 7 dias por um mais caro, como funciona a diferença de valor?",
            "26. Promoções Ativas (Taylor 110e vs Kalani Tenor)": "Quero aproveitar as promoções de hoje! Vocês têm desconto ativo no violão Taylor 110e Dreadnought e no ukulele Kalani KAL-700T Tenor? Me passe o preço original, o preço promocional e em quantas vezes sem juros consigo parcelar cada um separado.",
            "27. Baterias Acústicas, Frete Grande Porte & Pele": "Quais baterias acústicas vocês têm em estoque hoje? Moro em Dourados/MS: o frete de bateria acústica segue a tabela comum ou tem regra especial? E se eu rasgar a pele ou amassar o casco numa queda no show, a garantia cobre?",
            "28. Sintetizadores (Korg/Roland/Nord) + Acessórios": "Me mostre todos os teclados e sintetizadores disponíveis no catálogo, do mais barato ao mais caro. Quero levar o Korg Synth 1 Pro junto com um pedal de sustain, um suporte em X e um cabo P10. Quanto fica tudo?",
            "29. Orquestra (Categorias Vazias) & Sopro Higiene": "Estou montando uma orquestra escolar e preciso comprar 2 violinos, 1 violoncelo, 1 saxofone alto e 1 trompete. Vocês têm esses instrumentos em estoque? E se comprarmos instrumentos de sopro, qual é a regra da loja sobre troca de boquilhas e garantia de palhetas de sopro?",
            "30. Lote Escola 5x Yamaha C40 & Atacado CNPJ": "Sou diretor de uma escola de música aqui em Campo Grande e quero comprar 5 unidades do violão Yamaha C40 Nylon Natural de uma vez no PIX. Vocês têm estoque pra isso hoje? Além dos 5% do PIX, consigo mais 15% de desconto de atacado para CNPJ?"
        }
    }

    selected_battery = st.selectbox("Categoria de Teste:", list(scenario_batteries.keys()))
    selected_prompt = None
    for label, prompt_text in scenario_batteries[selected_battery].items():
        if st.button(label, use_container_width=True):
            selected_prompt = prompt_text

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Limpar Chat", use_container_width=True):
            st.session_state.agent.reset_conversation()
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": "Conversa reiniciada! Como posso te ajudar agora? 🎸",
                    "traces": []
                }
            ]
            st.rerun()

    with col2:
        transcript_md = st.session_state.agent.memory.export_transcript_markdown()
        st.download_button(
            "💾 Baixar .md",
            data=transcript_md,
            file_name="conversa_emporio_musica.md",
            mime="text/markdown",
            use_container_width=True
        )


# Cabeçalho Principal
st.markdown('<div class="main-header">Empório da Música <span class="status-badge">Tom Online</span></div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Atendimento Inteligente com Tool Calling & Políticas Oficiais da Loja</div>', unsafe_allow_html=True)


# Renderização das mensagens existentes
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar="🎸" if msg["role"] == "assistant" else "👤"):
        st.markdown(sanitize_markdown(msg["content"]))
        if msg.get("traces"):
            with st.expander("🛠️ Bastidores: Ferramentas Acionadas pelo Agente", expanded=False):
                for idx, t in enumerate(msg["traces"], 1):
                    st.markdown(f"**Chamada #{idx}:** `{t['tool']}`")
                    st.json({"parametros": t["arguments"], "resultado": t["result"]})


# Processamento de nova mensagem
user_message = st.chat_input("Digite sua mensagem para o Tom...")

if selected_prompt:
    user_message = selected_prompt

if user_message:
    # 1. Exibe a mensagem do usuário
    st.session_state.chat_history.append({"role": "user", "content": user_message})
    with st.chat_message("user", avatar="👤"):
        st.markdown(sanitize_markdown(user_message))

    # 2. Executa o agente
    with st.chat_message("assistant", avatar="🎸"):
        with st.spinner("Tom está consultando o catálogo e as normas da loja..."):
            reply, traces = st.session_state.agent.process_message(user_message)

        st.markdown(sanitize_markdown(reply))

        if traces:
            with st.expander("🛠️ Bastidores: Ferramentas Acionadas pelo Agente", expanded=False):
                for idx, t in enumerate(traces, 1):
                    st.markdown(f"**Chamada #{idx}:** `{t['tool']}`")
                    st.json({"parametros": t["arguments"], "resultado": t["result"]})

    # 3. Salva no histórico da sessão
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": reply,
        "traces": traces
    })
    st.rerun()
