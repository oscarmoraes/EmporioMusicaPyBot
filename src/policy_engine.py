"""Motor de conhecimento normativo e políticas da Empório da Música.

Indexa as seções estruturadas do manual 'políticas_da_loja.pdf' preservando
tabelas e notas de exceção conjuntas, garantindo recuperação de alta precisão
e detecção proativa de itens fora de escopo (acessórios não comercializados).
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import DATA_DIR, STORE_INFO
from src.data_engine import normalize_text


class PolicyEngine:
    """Gerencia a consulta estruturada às políticas e diretrizes internas da loja."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.pdf_path = self.data_dir / "políticas_da_loja.pdf"
        self.sections: Dict[str, Dict[str, Any]] = {}
        self._load_policy_sections()

    def _load_policy_sections(self) -> None:
        """Estrutura as 10 seções do manual com metadados e palavras-chave de busca."""
        self.sections = {
            "institucional": {
                "title": "1. Sobre a Empório da Música & Escopo de Atuação",
                "keywords": ["sobre", "historia", "fundacao", "endereco", "cnpj", "telefone", "onde fica", "localizacao", "missao", "contato"],
                "content": (
                    f"Razão Social: {STORE_INFO['legal_name']}\n"
                    f"Nome Fantasia: {STORE_INFO['name']} (Fundada em 2008 em Campo Grande/MS)\n"
                    f"CNPJ: {STORE_INFO['cnpj']}\n"
                    f"Endereço: {STORE_INFO['address']}\n"
                    f"Telefone Geral: {STORE_INFO['phone']} | WhatsApp Atendimento: {STORE_INFO['whatsapp_support']}\n"
                    f"E-mail: {STORE_INFO['email']}\n"
                    "Missão: Democratizar o acesso a instrumentos musicais de qualidade na região Centro-Oeste.\n"
                    "ESCOPO EXCLUSIVO: Trabalhamos EXCLUSIVAMENTE com instrumentos musicais (guitarras, baixos, violões, baterias, teclados, sopros, cordas orquestrais e ukuleles).\n"
                    "REGRA FUNDAMENTAL: NÃO comercializamos acessórios como cordas, palhetas, cabos, cases, pedais ou amplificadores. Pedidos desses itens devem ser educadamente redirecionados a lojas parceiras."
                )
            },
            "horarios": {
                "title": "2. Horário de Funcionamento e Retorno de Expediente",
                "keywords": ["horario", "horarios", "funcionamento", "aberto", "abre", "fecha", "atendimento", "sabado", "domingo", "feriado", "expediente", "noite"],
                "content": (
                    "Horário de atendimento presencial na loja e humano via WhatsApp:\n"
                    "• Segunda a Sexta-feira: 09:00 às 18:00\n"
                    "• Sábado: 09:00 às 13:00\n"
                    "• Domingo e Feriados: Fechado\n"
                    "• REGRA FORA DO EXPEDIENTE (Seção 7.1): Caso o cliente entre em contato fora do horário de funcionamento (ex.: domingos, feriados ou à noite), informe obrigatoriamente o horário de retorno do atendimento humano/presencial (ex.: se for no domingo, informe que o atendimento retorna na segunda-feira às 09:00).\n"
                    "• Em datas especiais (Black Friday, Aniversário da Loja, Natal), os horários podem ser estendidos com aviso prévio nas redes sociais e WhatsApp."
                )
            },
            "pagamento": {
                "title": "3 e 3.1. Formas de Pagamento e Regras de Parcelamento",
                "keywords": ["pagamento", "pix", "cartao", "credito", "debito", "boleto", "parcelamento", "parcelas", "juros", "desconto pix"],
                "content": (
                    "Formas de pagamento aceitas:\n"
                    "• PIX: Pagamento à vista com 5% de desconto sobre o preço de tabela (ATENÇÃO: não cumulativo com produtos já em promoção).\n"
                    "• Cartão de Débito: À vista, todas as bandeiras aceitas.\n"
                    "• Boleto Bancário: À vista, compensação em até 3 dias úteis.\n"
                    "• Cartão de Crédito: Até 12x SEM JUROS.\n\n"
                    "Regras Específicas de Parcelamento no Cartão (Seção 3.1):\n"
                    "• Em até 3x sem juros: sem valor mínimo de parcela (exceto abaixo de R$ 50,00).\n"
                    "• De 4x a 6x sem juros: parcela mínima de R$ 80,00.\n"
                    "• De 7x a 12x sem juros: parcela mínima de R$ 100,00.\n"
                    "• Combinação de pagamentos (ex.: PIX + Cartão): permitida para compras acima de R$ 2.000,00."
                )
            },
            "trocas_devolucoes": {
                "title": "4. Política de Trocas e Devoluções (CDC)",
                "keywords": ["troca", "trocar", "devolucao", "devolver", "arrependimento", "defeito", "cancelamento", "reembolso", "estorno", "prazo troca", "setup", "regulagem", "encomenda", "boquilha", "liquidacao", "venda final"],
                "content": (
                    "A Empório da Música segue rigorosamente o Código de Defesa do Consumidor (Lei nº 8.078/90):\n\n"
                    "4.1 Direito de Arrependimento (Compras Online / WhatsApp):\n"
                    "• O cliente pode solicitar a devolução em até 7 (sete) dias corridos após o recebimento do produto, sem necessidade de justificativa.\n"
                    "• O produto deve estar em sua embalagem original, sem sinais de uso, acompanhado de todos os manuais e acessórios originais.\n"
                    "• O frete de devolução por arrependimento é 100% por conta da loja.\n"
                    "• O reembolso/estorno é realizado na mesma forma de pagamento original em até 10 dias úteis.\n\n"
                    "4.2 Trocas por Defeito de Fabricação:\n"
                    "• Produtos com defeito podem ser trocados diretamente na loja em até 30 (trinta) dias corridos após a compra.\n"
                    "• Após os 30 dias (e até o término da garantia), o cliente aciona a garantia do fabricante, com intermediação da Empório da Música mediante solicitação.\n"
                    "• Não são cobertos danos causados por mau uso, quedas, umidade excessiva ou intervenções de terceiros não autorizados.\n\n"
                    "4.3 Trocas por Preferência (cor, modelo, tamanho):\n"
                    "• Permitidas em até 7 dias, condicionadas à disponibilidade em estoque. Produto em perfeito estado na embalagem original (exceto itens da Seção 4.4).\n\n"
                    "4.4 Itens ESTRITAMENTE NÃO Elegíveis para Troca ou Devolução:\n"
                    "• Instrumentos com personalização ou ajustes sob encomenda (setup, regulagem especial solicitada pelo cliente): NÃO podem ser trocados por preferência nem devolvidos por arrependimento após a customização;\n"
                    "• Produtos adquiridos em promoções de liquidação com aviso explícito de 'venda final';\n"
                    "• Boquilhas de instrumentos de sopro, por rígidas questões de higiene sanitária (mesmo dentro de 7 dias, boquilhas NÃO são elegíveis para troca)."
                )
            },
            "frete_entregas": {
                "title": "5. Política de Frete, Entregas e Rastreamento",
                "keywords": ["frete", "entrega", "prazo", "motoboy", "campo grande", "correios", "sedex", "pac", "jadlog", "rastreamento", "codigo rastreio", "avaria", "amassada", "rasgada", "danificada", "transportadora", "dourados", "interior", "bateria", "grande porte"],
                "content": (
                    "5.1 Entregas na Região Metropolitana de Campo Grande/MS:\n"
                    "• Frete GRÁTIS para pedidos acima de R$ 500,00.\n"
                    "• Taxa fixa de R$ 35,00 para pedidos abaixo de R$ 500,00.\n"
                    "• Prazo: 1 a 3 dias úteis (entrega por motoboy próprio; cliente contactado por telefone antes da entrega).\n\n"
                    "5.2 Entregas para Outras Cidades e Estados (Interior de MS e Brasil):\n"
                    "• PAC (Correios): 5 a 12 dias úteis (rastreamento e seguro inclusos).\n"
                    "• SEDEX (Correios): 2 a 5 dias úteis (rastreamento e seguro inclusos).\n"
                    "• Jadlog (.package): 3 a 8 dias úteis (rastreamento e seguro inclusos).\n"
                    "• INSTRUMENTOS DE GRANDE PORTE: Baterias acústicas, pianos digitais e contrabaixos acústicos podem exigir frete especial com cotação individual.\n"
                    "• SEGURO E PROCEDIMENTO EM CASO DE AVARIA NO TRANSPORTE: Todos os envios incluem seguro contra extravios e danos durante o transporte. Em caso de caixa amassada, rasgada ou avaria no transporte, o cliente DEVE RECUSAR O RECEBIMENTO NO ATO DA ENTREGA e entrar em contato imediatamente com a loja pelo WhatsApp (67) 3321-4500 ou telefone (67) 3341-4444 para acionamento do seguro e envio de novo instrumento.\n\n"
                    "5.3 Código de Rastreamento:\n"
                    "• Enviado por e-mail e WhatsApp assim que despachado. Formato padrão: BR seguido de 9 caracteres alfanuméricos e BR (ex.: BR4K7M2X9P1BR)."
                )
            },
            "promocoes": {
                "title": "6. Regras de Promoções e Descontos",
                "keywords": ["promocao", "promocoes", "desconto", "black friday", "aniversario", "queima", "semana do musico", "cumulativo", "campanha"],
                "content": (
                    "6.1 Campanhas Periódicas:\n"
                    "• Aniversário da Loja (Agosto): 10% a 25% de desconto.\n"
                    "• Black Friday (Novembro): 15% a 30% em todo o catálogo.\n"
                    "• Volta às Aulas (Fevereiro): descontos para estudantes.\n"
                    "• Semana do Músico (semana do dia 22 de Novembro).\n"
                    "• Queima de Estoque pontual.\n\n"
                    "6.2 Regras Estritas de Promoções:\n"
                    "• NÃO CUMULATIVIDADE: O desconto de 5% no PIX NÃO se aplica sobre preços já promocionais.\n"
                    "• ESTOQUE: Não há reserva de preço ('rain check') para itens promocionais esgotados.\n"
                    "• TRANSPARÊNCIA: Preços promocionais devem sempre ser apresentados acompanhados do preço original de tabela e do percentual de desconto."
                )
            },
            "atendimento_whatsapp": {
                "title": "7. Diretrizes de Atendimento e Persona (Tom de Voz)",
                "keywords": ["whatsapp", "tom de voz", "atendimento", "persona", "diretrizes", "fora de estoque", "descontinuado", "reclamacao"],
                "content": (
                    "7.1 Diretrizes de Atendimento:\n"
                    "• Tom de voz: Informal mas profissional. Amigo que entende profundamente de música, acolhedor e prestativo. Evitar robotização.\n"
                    "• Tempo de resposta: até 5 minutos no horário de funcionamento.\n"
                    "• PRECISÃO OBRIGATÓRIA: Jamais fornecer informações de preço, estoque ou prazos sem consultar o sistema.\n"
                    "• ESCOPO: Lembrar que a loja comercializa exclusivamente instrumentos musicais. Pedidos de cordas, palhetas, cabos, cases, pedais ou amplificadores devem ser educadamente redirecionados.\n\n"
                    "7.3 Situações Especiais:\n"
                    "• Fora de estoque: Informar indisponibilidade temporária e sugerir alternativas semelhantes disponíveis.\n"
                    "• Descontinuado: Se sem estoque, informar que saiu de linha e sugerir sucessores ativos. Se houver saldo em estoque, aproveitar como oportunidade de Ponta de Estoque (últimas unidades).\n"
                    "• Promoção expirada: Explicar com transparência que a promoção foi encerrada e apresentar o preço atual. Nunca prometer desconto não vigente.\n"
                    "• Reclamações: Ouvir com empatia, registrar e informar prazo de retorno de 24 horas úteis."
                )
            },
            "garantia": {
                "title": "8. Garantia Legal e do Fabricante",
                "keywords": ["garantia", "defeito", "assistencia", "conserto", "mau uso", "fabricante", "luthier", "eletrica", "captador", "estourou", "terceiros", "modificacao", "pele", "peles", "queda", "amassar", "estetico", "palhetas de sopro"],
                "content": (
                    "8.1 Garantia Legal:\n"
                    "• Todos os produtos contam com garantia legal de 90 (noventa) dias contra defeitos de fabricação (CDC), a contar do recebimento.\n\n"
                    "8.2 Garantia do Fabricante:\n"
                    "• Varia de 6 meses a 2 anos dependendo da marca (detalhada no certificado que acompanha o produto).\n\n"
                    "8.3 O que NÃO é coberto pela garantia (EXCLUSÃO IMEDIATA DE GARANTIA):\n"
                    "• Desgaste natural de peças (trastes, cordas estouradas/gastas, feltros, peles de bateria, palhetas de sopro);\n"
                    "• Danos decorrentes de mau uso, quedas, exposição a condições climáticas extremas;\n"
                    "• Modificações, ajustes na parte elétrica/captadores ou reparos realizados por terceiros/luthiers NÃO autorizados (isso anula a cobertura da garantia para o defeito);\n"
                    "• Danos meramente estéticos que não afetem a funcionalidade do instrumento."
                )
            },
            "privacidade_lgpd": {
                "title": "9. Privacidade e Proteção de Dados (LGPD)",
                "keywords": ["lgpd", "privacidade", "dados", "seguranca", "exclusao", "excluir", "dados pessoais", "marketing"],
                "content": (
                    "A Empório da Música cumpre integralmente a LGPD (Lei nº 13.709/2018).\n"
                    "Dados cadastrais (nome, telefone, e-mail, endereço) são utilizados estritamente para:\n"
                    "• Processamento e entrega de pedidos;\n"
                    "• Comunicação sobre status de pedidos e rastreamento;\n"
                    "• Envio de promoções e novidades (mediante consentimento explícito do cliente);\n"
                    "• Cumprimento de obrigações legais e fiscais.\n"
                    "A loja NÃO compartilha dados com terceiros para fins de marketing. O cliente pode solicitar a exclusão de seus dados a qualquer momento pelo WhatsApp ou e-mail (contato@emporiodamusica.com.br)."
                )
            },
            "disposicoes_finais": {
                "title": "10. Disposições Finais e Escalonamento à Gerência",
                "keywords": ["gerencia", "gerente", "duvida", "usado", "usados", "base de troca", "aluguel", "locacao", "consignacao", "excecao", "atacado", "lote", "escola", "cnpj"],
                "content": (
                    "10. Disposições Finais:\n"
                    "• Este manual é referência obrigatória para toda a equipe de atendimento e assistente virtual.\n"
                    "• A loja comercializa exclusivamente instrumentos musicais novos (não há modalidade prevista no manual para aluguel/locação, recebimento de instrumentos usados como parte de pagamento ou descontos extras de atacado/CNPJ além dos 5% à vista no PIX).\n"
                    "• Em caso de dúvidas sobre a aplicação de qualquer política ou solicitações comerciais atípicas (como propostas corporativas/atacado, locação ou usados), o atendente deve consultar ou encaminhar à gerência ((67) 3341-4444 / (67) 3321-4500 ou contato@emporiodamusica.com.br) antes de fornecer informações definitivas ao cliente."
                )
            }
        }

    def check_out_of_scope_accessory(self, text: str) -> Optional[Dict[str, Any]]:
        """Detecta se o cliente está buscando acessórios que a loja deliberadamente NÃO comercializa."""
        # Ignora 'Correia' quando grafado como sobrenome próprio após prenome (ex: 'João Correia', 'Matheus Ramos Correia')
        text_no_surnames = re.sub(r"\b[A-ZÀ-Ú][a-zà-ú]+\s+Correia\b", "", text)
        cleaned = text_no_surnames.lower()

        # Remove menções legítimas a especificações técnicas de instrumentos ou regulagem
        cleaned = re.sub(r"\b\d+\s*cordas\b", "", cleaned)
        cleaned = re.sub(r"\bcordas\s+(orquestrais|de\s+nylon|de\s+aco|de\s+aço|nylon|aco|aço)\b", "", cleaned)
        cleaned = re.sub(r"\b(acao|ação|altura|ajuste)\s+das\s+cordas\b", "", cleaned)
        cleaned = re.sub(r"\bpalheta(s)?\s+(de\s+sopro|gasta|gastas)\b", "", cleaned)

        accessory_patterns = [
            r"\bcorda(s)?\b", r"\bencordoamento(s)?\b", r"\bpalheta(s)?\b",
            r"\bcabo(s)?\b", r"\bcase(s)?\b", r"\bcapa(s)?\b", r"\bbag(s)?\b",
            r"\bpedal\b", r"\bpedais\b", r"\bpedaleira(s)?\b", r"\bamplificador(es)?\b",
            r"\bamp(s)?\b", r"\bafinador(es)?\b", r"\bsuporte(s)?\b", r"\bcorreia(s)?\b"
        ]

        matched = []
        for pat in accessory_patterns:
            if re.search(pat, cleaned):
                matched.append(pat.replace(r"\b", "").replace("(s)?", "s").replace("(es)?", "es"))

        if matched:
            return {
                "is_out_of_scope": True,
                "detected_items": matched,
                "policy_instruction": (
                    "Conforme a Seção 1 e Seção 7.1 do manual, a Empório da Música trabalha "
                    "EXCLUSIVAMENTE com instrumentos musicais completos para garantir atendimento especializado, "
                    "não comercializando acessórios como cordas avulsas, palhetas, cabos, cases, pedais ou amplificadores. "
                    "O assistente deve explicar isso com cordialidade e sugerir educadamente que o cliente procure lojas parceiras especializadas em acessórios. "
                    "Caso a mensagem contenha perguntas sobre temas fora do domínio da loja, recuse-as em no máximo 1 frase curta sem desenvolver o conteúdo alheio."
                )
            }
        return None

    def retrieve_policies(self, query: str, specific_topic: Optional[str] = None) -> Dict[str, Any]:
        """Recupera as seções normativas mais relevantes com base em tópico ou termos de busca."""
        # Checa primeiro se há menção a acessórios fora de escopo
        out_of_scope_alert = self.check_out_of_scope_accessory(query)

        if specific_topic and specific_topic.lower() in self.sections:
            sec = self.sections[specific_topic.lower()]
            return {
                "matched_topic": specific_topic.lower(),
                "sections": [{
                    "section_key": specific_topic.lower(),
                    "title": sec["title"],
                    "content": sec["content"]
                }],
                "out_of_scope_alert": out_of_scope_alert
            }

        # Busca baseada em pontuação de palavras-chave (tolerante a acentos)
        norm_query = normalize_text(query)
        q_tokens = set(re.findall(r"\w+", norm_query))
        scores: List[Tuple[str, int]] = []

        for key, sec in self.sections.items():
            score = 0
            # Pontuação por keywords cadastradas
            for kw in sec["keywords"]:
                if normalize_text(kw) in norm_query:
                    score += 3
            # Pontuação por termos no conteúdo
            c_norm = normalize_text(sec["content"])
            for token in q_tokens:
                if len(token) > 3 and token in c_norm:
                    score += 1
            if score > 0:
                scores.append((key, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        if not scores:
            # Fallback: retorna institucional, atendimento e disposições finais
            matched_keys = ["institucional", "atendimento_whatsapp", "disposicoes_finais"]
        else:
            # Retorna até as 3 seções mais relevantes
            matched_keys = [k for k, _ in scores[:3]]

        retrieved = []
        for k in matched_keys:
            sec = self.sections[k]
            retrieved.append({
                "section_key": k,
                "title": sec["title"],
                "content": sec["content"]
            })

        return {
            "query": query,
            "total_sections_matched": len(retrieved),
            "sections": retrieved,
            "out_of_scope_alert": out_of_scope_alert
        }
