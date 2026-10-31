"""Interface Web Interativa (Streamlit) para o Agente da Empório da Música.

Permite testar visualmente o atendimento do assistente Tom, com persistência
de histórico na sessão, inspeção detalhada das ferramentas acionadas e
botões de atalho para os principais cenários do desafio.
"""

import streamlit as st
from src.agent import EmporioAgent
from src.config import STORE_INFO

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
    st.markdown("### ⚡ Cenários de Teste Rápidos")
    st.caption("Clique em um botão para testar cenários do desafio:")

    scenario_prompts = {
        "Violões até R$ 1000": "Quais opções de violões disponíveis custando até R$ 1000?",
        "Preço Takamine GD20": "Quanto custa o Takamine GD20 e quais as formas de pagamento?",
        "Promoção Crafter HT-100": "O Crafter HT-100 está em promoção? Consigo mais 5% de desconto no PIX?",
        "Ponta de Estoque Ibanez Bass": "Vocês têm o baixo Ibanez Bass 2X? Ainda é vendido?",
        "Status de Pedido & Arrependimento": "Sou o Pedro Henrique Oliveira. Gostaria de saber o status do meu pedido e se ainda posso devolver por arrependimento.",
        "Acessórios (Fora de Escopo)": "Vocês vendem encordoamento para violão de aço, palhetas e amplificador?",
        "Endereço e Frete": "Qual o endereço da loja e como funciona o frete para Campo Grande e para o interior?"
    }

    selected_prompt = None
    for label, prompt_text in scenario_prompts.items():
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
        st.markdown(msg["content"])
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
        st.markdown(user_message)

    # 2. Executa o agente
    with st.chat_message("assistant", avatar="🎸"):
        with st.spinner("Tom está consultando o catálogo e as normas da loja..."):
            reply, traces = st.session_state.agent.process_message(user_message)

        st.markdown(reply)

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
