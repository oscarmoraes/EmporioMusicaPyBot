"""Gerenciamento de memória de sessão e histórico conversacional."""

from typing import Any, Dict, List, Optional


class ConversationMemory:
    """Armazena as mensagens e histórico de chamadas de ferramentas de uma sessão."""

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, Any]] = []
        self.tool_trace: List[Dict[str, Any]] = []
        self.reset()

    def reset(self) -> None:
        """Reinicia o histórico da conversa."""
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.tool_trace = []

    def add_user_message(self, content: str) -> None:
        """Adiciona uma mensagem enviada pelo usuário."""
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: Optional[str], tool_calls: Optional[List[Any]] = None) -> None:
        """Adiciona uma mensagem gerada pelo assistente, opcionalmente com chamadas de ferramentas."""
        msg: Dict[str, Any] = {"role": "assistant"}
        if content is not None:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)

    def add_tool_message(self, tool_call_id: str, content: str) -> None:
        """Adiciona a resposta de uma ferramenta executada."""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        })

    def record_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Registra a chamada da ferramenta para auditoria e exibição na UI."""
        self.tool_trace.append({
            "tool": tool_name,
            "arguments": arguments,
            "result": result
        })

    def get_messages(self) -> List[Dict[str, Any]]:
        """Retorna a lista atualizada de mensagens para a API."""
        return self.messages

    def export_transcript_markdown(self) -> str:
        """Gera um arquivo Markdown formatado com a transcrição completa da conversa."""
        lines = ["# Transcrição da Sessão de Atendimento — Empório da Música\n"]
        for msg in self.messages:
            role = msg["role"]
            if role == "system":
                continue
            elif role == "user":
                lines.append(f"### 👤 Cliente:\n{msg['content']}\n")
            elif role == "assistant":
                if msg.get("content"):
                    lines.append(f"### 🎸 Tom (Empório da Música):\n{msg['content']}\n")
                if msg.get("tool_calls"):
                    lines.append("<details><summary>🛠️ <i>Ferramentas consultadas pelo agente</i></summary>\n")
                    for tc in msg["tool_calls"]:
                        fn = tc.function if hasattr(tc, "function") else tc.get("function", {})
                        fname = getattr(fn, "name", fn.get("name", ""))
                        fargs = getattr(fn, "arguments", fn.get("arguments", ""))
                        lines.append(f"- **Tool:** `{fname}`\n- **Args:** `{fargs}`\n")
                    lines.append("</details>\n")
            elif role == "tool":
                continue

        return "\n".join(lines)
