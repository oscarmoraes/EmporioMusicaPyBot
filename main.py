"""Interface de Linha de Comando (CLI) Interativa da Empório da Música.

Permite conversar em tempo real com o assistente Tom, visualizando as respostas
formatadas com Rich e inspecionando as ferramentas acionadas sob o capô.
"""

import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.agent import EmporioAgent
from src.config import STORE_INFO


def display_welcome_banner(console: Console) -> None:
    """Exibe o cabeçalho inicial da CLI."""
    banner_text = f"""[bold yellow]🎸 EMPÓRIO DA MÚSICA — ATENDIMENTO INTELIGENTE[/bold yellow]
[cyan]Sua música começa aqui | Campo Grande - MS[/cyan]

Bem-vindo ao canal de atendimento interativo do assistente virtual [bold green]Tom[/bold green].
Tire dúvidas sobre violões, guitarras, teclados, estoque, rastreamento de pedidos e políticas da loja!

[dim]Comandos especiais:
  /tools       - Inspeciona as ferramentas (tools) chamadas no último turno
  /reset       - Limpa a memória da conversa e reinicia a sessão
  /salvar      - Salva a transcrição da conversa atual em arquivo Markdown
  /ajuda       - Exibe sugestões de perguntas do desafio
  /sair        - Encerra a conversa[/dim]
"""
    console.print(Panel(banner_text, border_style="yellow", expand=False))


def display_help(console: Console) -> None:
    """Exibe exemplos de perguntas recomendadas do desafio."""
    table = Table(title="Exemplos de Perguntas para Testar o Agente", border_style="cyan")
    table.add_column("Cenário", style="bold white", width=25)
    table.add_column("Sugestão de Mensagem", style="green")

    table.add_row(
        "Catálogo com Teto de Preço",
        "Quais opções de violões disponíveis custando até R$ 1000?"
    )
    table.add_row(
        "Informações Institucionais",
        "Qual o endereço e o horário de funcionamento da loja?"
    )
    table.add_row(
        "Preço e Condições PIX",
        "Quanto custa o Takamine GD20 e quais as opções de pagamento?"
    )
    table.add_row(
        "Promoção Ativa & Desconto",
        "O Crafter HT-100 está em promoção? Tem mais 5% de desconto no PIX?"
    )
    table.add_row(
        "Ponta de Estoque (Descontinuado)",
        "Vocês têm o baixo Ibanez Bass 2X? Ainda é vendido?"
    )
    table.add_row(
        "Status de Pedido & Devolução",
        "Sou o Pedro Henrique Oliveira. Como está meu pedido? Posso devolver por arrependimento?"
    )
    table.add_row(
        "Item Fora de Escopo (Acessórios)",
        "Vocês vendem encordoamento para violão de aço e palhetas?"
    )
    console.print(table)


def main() -> None:
    """Loop principal de interação via terminal."""
    console = Console()
    display_welcome_banner(console)

    try:
        with console.status("[bold green]Inicializando bases de dados e conectando ao modelo..."):
            agent = EmporioAgent()
        console.print("[green]✓ Agente pronto para atendimento![/green]\n")
    except Exception as e:
        console.print(f"[bold red]Erro ao inicializar o agente:[/bold red] {e}")
        console.print("[yellow]Verifique se a chave de API está configurada corretamente no arquivo .env[/yellow]")
        sys.exit(1)

    last_traces = []

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]👤 Você[/bold cyan]")
            if not user_input.strip():
                continue

            cmd = user_input.strip().lower()

            if cmd in ["/sair", "/exit", "sair", "exit"]:
                console.print("\n[yellow]Tom: Valeu pelo papo! Qualquer coisa é só chamar a Empório da Música. Até a próxima! 🎸[/yellow]")
                break

            elif cmd in ["/ajuda", "/help", "ajuda", "help"]:
                display_help(console)
                continue

            elif cmd in ["/reset", "/limpar"]:
                agent.reset_conversation()
                last_traces = []
                console.print("[green]✓ Memória da sessão reiniciada com sucesso.[/green]")
                continue

            elif cmd == "/tools":
                if not last_traces:
                    console.print("[yellow]Nenhuma ferramenta foi acionada na última resposta.[/yellow]")
                else:
                    console.print(f"\n[bold yellow]🛠️ Ferramentas acionadas no último turno ({len(last_traces)}):[/bold yellow]")
                    for idx, trace in enumerate(last_traces, 1):
                        console.print(Panel(
                            f"[bold cyan]Tool:[/bold cyan] {trace['tool']}\n"
                            f"[bold cyan]Parâmetros:[/bold cyan] {trace['arguments']}\n\n"
                            f"[bold cyan]Resultado Retornado:[/bold cyan]\n{trace['result']}",
                            title=f"Chamada #{idx}",
                            border_style="blue"
                        ))
                continue

            elif cmd == "/salvar":
                md_content = agent.memory.export_transcript_markdown()
                filename = "transcricao_sessao.md"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(md_content)
                console.print(f"[green]✓ Transcrição salva em '{filename}'.[/green]")
                continue

            # Processa a mensagem do usuário com o agente
            with console.status("[bold yellow]Tom está consultando o sistema e redigindo a resposta..."):
                reply, traces = agent.process_message(user_input)
                last_traces = traces

            # Exibe resumo das ferramentas caso tenham sido chamadas
            if traces:
                tools_summary = ", ".join([f"`{t['tool']}`" for t in traces])
                console.print(f"[dim]🛠️ Sistemas consultados: {tools_summary}[/dim]")

            # Renderiza resposta formatada em Markdown
            console.print("\n[bold green]🎸 Tom (Empório da Música)[/bold green]:")
            console.print(Panel(Markdown(reply), border_style="green"))

        except KeyboardInterrupt:
            console.print("\n[yellow]Sessão encerrada pelo usuário.[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Erro durante o atendimento:[/bold red] {e}")


if __name__ == "__main__":
    main()
