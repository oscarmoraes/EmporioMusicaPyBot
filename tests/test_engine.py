"""Testes automatizados unitários e de integração para o Agente Empório da Música."""

import pytest
from src.data_engine import DataEngine, normalize_text
from src.policy_engine import PolicyEngine


@pytest.fixture
def data_engine():
    """Instância do motor de dados."""
    return DataEngine()


@pytest.fixture
def policy_engine():
    """Instância do motor de políticas."""
    return PolicyEngine()


def test_normalize_text():
    """Testa a remoção de acentos e tolerância textual."""
    assert normalize_text("Violões") == "violoes"
    assert normalize_text("Aço") == "aco"
    assert normalize_text("  Promoção de Páscoa!  ") == "promocao de pascoa!"


def test_catalog_search_violões_under_1000(data_engine):
    """Valida a busca de violões até R$ 1000 e a separação de estoque/descontinuados."""
    result = data_engine.search_catalog(category="violão", max_price=1000.0)

    # Devem existir violões disponíveis abaixo de R$ 1000
    assert len(result["available_products"]) > 0

    # Todos os disponíveis devem custar <= 1000 e ter estoque > 0
    for prod in result["available_products"]:
        assert prod["effective_price"] <= 1000.0
        assert prod["stock_quantity"] > 0
        assert prod["status"] == "active"

    # Giannini GF-3D deve constar como esgotado (stock=0)
    out_of_stock_names = [p["name"] for p in result["out_of_stock_products"]]
    assert any("GF-3D" in name for name in out_of_stock_names)

    # Shelby SN-7C deve constar como descontinuado
    discontinued_names = [p["name"] for p in result["discontinued_products"]]
    assert any("SN-7C" in name for name in discontinued_names)


def test_active_promotion_and_pix_rule(data_engine):
    """Testa cálculo de promoção ativa e veto à cumulatividade com PIX (Seção 6.2)."""
    # Crafter HT-100 tem promoção ativa de 18% (ID 19)
    crafter = data_engine.get_product_details("Crafter HT-100")
    assert crafter["found"] is True
    assert crafter["has_active_promotion"] is True
    assert crafter["original_price"] == 2399.0
    # 2399 * 0.82 = 1967.18
    assert crafter["effective_price"] == 1967.18

    # PIX não deve ter desconto adicional cumulativo
    pix_info = crafter["payment_conditions"]["pix"]
    assert pix_info["discount_applied"] is False
    assert pix_info["price"] == 1967.18


def test_regular_product_pix_discount(data_engine):
    """Testa aplicação de 5% de desconto no PIX em produto sem promoção."""
    # Takamine GD20 custa 2199.0 e não tem promoção ativa
    gd20 = data_engine.get_product_details("Takamine GD20")
    assert gd20["found"] is True
    assert gd20["has_active_promotion"] is False
    assert gd20["effective_price"] == 2199.0

    pix_info = gd20["payment_conditions"]["pix"]
    assert pix_info["discount_applied"] is True
    # 2199 * 0.95 = 2089.05
    assert pix_info["price"] == 2089.05


def test_clearance_opportunity_ibanez_bass(data_engine):
    """Testa a regra de Ponta de Estoque para produto descontinuado com saldo em estoque."""
    # ID 136: Ibanez Bass 2X (status=discontinued, stock=13)
    ibanez = data_engine.get_product_details(136)
    assert ibanez["found"] is True
    assert ibanez["status"] == "discontinued"
    assert ibanez["stock_quantity"] == 13
    assert ibanez["is_clearance_opportunity"] is True
    assert "PONTA DE ESTOQUE" in ibanez["status_guidance_for_agent"]


def test_installment_ladder_rules(data_engine):
    """Valida as regras de parcelamento sem juros da Seção 3.1."""
    # Um produto de R$ 359,00:
    # 1x a 3x (mín. R$ 50): 359/3 = 119.67 (permitido)
    # 4x (mín. R$ 80): 359/4 = 89.75 (permitido)
    # 5x (mín. R$ 80): 359/5 = 71.80 (NÃO permitido pois < 80)
    kalani = data_engine.get_product_details(127)  # Kalani KAL-700T (efetivo 323.10)
    plans = kalani["payment_conditions"]["credit_card"]["available_plans"]
    max_inst = kalani["payment_conditions"]["credit_card"]["max_installments_without_interest"]

    for plan in plans:
        n = plan["installments"]
        val = plan["installment_value"]
        if n <= 3:
            assert val >= 50.0
        elif 4 <= n <= 6:
            assert val >= 80.0
        elif 7 <= n <= 12:
            assert val >= 100.0

    # Não deve permitir parcelas que violem o piso mínimo
    assert max_inst <= 4

    # Produto de R$ 900,00: 9x de R$ 100,00 é permitido (>= 100), 10x de R$ 90,00 violaria piso da faixa 7-12
    p900 = data_engine.calculate_payment_plans(900.0, 900.0, False)
    assert p900["credit_card"]["max_installments_without_interest"] == 9

    # Teste de fronteira de frete: R$ 500,00 exatos exige R$ 35,00 de frete em Campo Grande
    p500 = data_engine.calculate_payment_plans(500.0, 500.0, False)
    assert p500["shipping_campo_grande"]["free_shipping"] is False
    assert p500["shipping_campo_grande"]["shipping_fee"] == 35.0


def test_customer_order_lookup_and_cdc_returns(data_engine):
    """Valida busca de pedidos por order_id obrigatório e contagem de prazo para devolução por arrependimento."""
    # Chamada sem order_id deve falhar (Decisão D3 / LGPD)
    sem_id = data_engine.lookup_orders()
    assert sem_id["found"] is False
    assert sem_id["error"] == "order_id_required"

    # Pedido 1: entregue em out/2025 -> prazo de 7 dias de arrependimento expirado em 25/03/2026
    res1 = data_engine.lookup_orders(order_id=1)
    assert res1["found"] is True
    ord1 = res1["orders"][0]
    assert ord1["status"] == "delivered"
    assert ord1["return_and_warranty_analysis"]["eligible_for_7d_regret_return"] is False
    assert "PRAZO EXPIRADO" in ord1["return_and_warranty_analysis"]["regret_status"]

    # Valida que dados sensíveis PII (telefone, email, cidade) foram removidos do retorno
    cust = ord1["customer"]
    assert "phone" not in cust
    assert "email" not in cust
    assert "city" not in cust

    # Pedido 19: cancelado por falta de pagamento
    res19 = data_engine.lookup_orders(order_id=19)
    assert res19["found"] is True
    ord19 = res19["orders"][0]
    assert ord19["status"] == "cancelled"
    assert "Pagamento" in ord19["notes"]


def test_empty_catalog_categories(data_engine):
    """Valida identificação de categorias do escopo da loja sem produtos em estoque."""
    result = data_engine.search_catalog(category="sopro")
    assert result["empty_category_notice"] is not None
    assert "Sopro" in result["empty_category_notice"]["name"]


def test_policy_engine_retrieval(policy_engine):
    """Valida recuperação semântica de seções normativas do manual."""
    res = policy_engine.retrieve_policies("como funciona o frete para fora de campo grande")
    assert len(res["sections"]) > 0
    sec_keys = [s["section_key"] for s in res["sections"]]
    assert "frete_entregas" in sec_keys


def test_out_of_scope_detection(policy_engine):
    """Valida detecção proativa de acessórios proibidos para venda."""
    check1 = policy_engine.check_out_of_scope_accessory("gostaria de comprar um jogo de cordas e duas palhetas")
    assert check1 is not None
    assert check1["is_out_of_scope"] is True
    assert "cordas" in check1["detected_items"] or "palhetas" in check1["detected_items"]

    check2 = policy_engine.check_out_of_scope_accessory("vocês têm violão takamine aço?")
    assert check2 is None


# =============================================================================
# EXPANSÃO: 20 NOVOS CASOS DE ATENDIMENTO (BATERIAS A, B, C, D, E)
# =============================================================================

# --- BATERIA A: Consultoria Musical & Filtros Complexos de Catálogo ---

def test_case_01_violao_7_cordas_descontinuado_e_sucessores(data_engine, policy_engine):
    """Caso 01: Shelby SN-7C 7 Cordas descontinuado deve sugerir os sucessores de 7 cordas ativos."""
    # '7 cordas' NÃO deve ser confundido com acessório avulso
    assert policy_engine.check_out_of_scope_accessory("Quero um violão de 7 cordas Shelby SN-7C") is None

    shelby = data_engine.get_product_details("Shelby SN-7C")
    assert shelby["found"] is True
    assert shelby["status"] == "discontinued"
    assert shelby["stock_quantity"] == 0
    sim_names = [s["name"] for s in shelby["similar_available_alternatives"]]
    assert any("7 Cordas" in name for name in sim_names)


def test_case_02_produto_ativo_sem_estoque_giannini_gf3d(data_engine):
    """Caso 02: Giannini GF-3D ativo com estoque 0, promoções expiradas e similares."""
    gf3d = data_engine.get_product_details("Giannini GF-3D")
    assert gf3d["found"] is True
    assert gf3d["status"] == "active"
    assert gf3d["stock_quantity"] == 0
    assert len(gf3d["expired_promotions"]) == 2
    assert len(gf3d["similar_available_alternatives"]) > 0


def test_case_03_lancamento_coming_soon_kala_baritono(data_engine):
    """Caso 03: Ukulele Kala Barítono Cedar com status coming_soon e busca por tokens fora de ordem."""
    kala_bar = data_engine.get_product_details("Kala Barítono Cedar (KA-ABP-CTG)")
    assert kala_bar["found"] is True
    assert kala_bar["product_id"] == 130
    assert kala_bar["status"] == "coming_soon"
    assert "coming_soon" in kala_bar["status_guidance_for_agent"]
    sim_names = [s["name"] for s in kala_bar["similar_available_alternatives"]]
    assert any("Barítono" in n for n in sim_names)


def test_case_04_instrumentos_high_end_acima_10000(data_engine):
    """Caso 04: Busca de guitarras e teclados profissionais acima de R$ 10.000,00."""
    guitars = data_engine.search_catalog(category="guitarra", min_price=10000.0)
    g_names = [p["name"] for p in guitars["available_products"]]
    assert any("Stratocaster" in n for n in g_names)
    assert any("Les Paul" in n for n in g_names)

    synths = data_engine.search_catalog(category="teclado", min_price=10000.0)
    s_names = [p["name"] for p in synths["available_products"]]
    assert any("Nord Synth 2 Pro" in n for n in s_names)


# --- BATERIA B: Regras Financeiras, Parcelamento e Promoções Expiradas ---

def test_case_05_promocoes_expiradas_tagima_e_martin(data_engine):
    """Caso 05: Histórico de promoções encerradas (Black Friday e Páscoa) para transparência (Seção 7.3)."""
    woodstock = data_engine.get_product_details("Tagima Woodstock")
    assert woodstock["has_active_promotion"] is False
    assert any(p["description"] == "Black Friday" and p["discount_percent"] == 30.0 for p in woodstock["expired_promotions"])

    martin = data_engine.get_product_details("Martin D-28 Dreadnought")
    assert martin["has_active_promotion"] is False
    assert len(martin["expired_promotions"]) == 2


def test_case_06_escada_parcelamento_shelby_soprano(data_engine):
    """Caso 06: Ukulele de R$ 159,90 deve parcelar em no máximo 3x de R$ 53,30 (4x violaria mín. R$ 80)."""
    shelby_uke = data_engine.get_product_details(119)
    assert shelby_uke["effective_price"] == 159.9
    cc = shelby_uke["payment_conditions"]["credit_card"]
    assert cc["max_installments_without_interest"] == 3
    assert cc["available_plans"][-1]["installment_value"] == 53.3


def test_case_07_pagamento_combinado_limite_2000(data_engine):
    """Caso 07: Combinação PIX + Cartão permitida apenas acima de R$ 2.000,00 (Seção 3.1)."""
    apx = data_engine.get_product_details("Yamaha APX600")
    assert apx["effective_price"] == 1899.0
    assert apx["payment_conditions"]["combined_payment"]["allowed"] is False

    taylor = data_engine.get_product_details("Taylor 110e")
    assert taylor["effective_price"] == 5519.08
    assert taylor["payment_conditions"]["combined_payment"]["allowed"] is True


def test_case_08_desconto_ativo_ohana_impacta_frete_campo_grande(data_engine):
    """Caso 08: Ohana CK-20 cai de R$ 549 para R$ 439,20 (-20%), ficando abaixo de R$ 500 (frete R$ 35)."""
    ohana = data_engine.get_product_details("Ohana CK-20")
    assert ohana["original_price"] == 549.0
    assert ohana["effective_price"] == 439.2
    ship_cg = ohana["payment_conditions"]["shipping_campo_grande"]
    assert ship_cg["free_shipping"] is False
    assert ship_cg["shipping_fee"] == 35.0
    assert ship_cg["total_with_shipping"] == 474.2


# --- BATERIA C: Rastreio de Pedidos, Logística e Situações Críticas de Entrega ---

def test_case_09_pedido_em_transito_com_atraso_e_reclamacao(data_engine):
    """Caso 09: Pedido #8 (Ana Carolina) em trânsito com entrega prevista vencida (28/02 vs 25/03)."""
    res = data_engine.lookup_orders(order_id=8)
    assert res["found"] is True
    ord8 = res["orders"][0]
    assert ord8["status"] == "shipped"
    assert ord8["tracking_code"] == "BRJL5544332BR"
    analysis = ord8["return_and_warranty_analysis"]
    assert analysis["is_delayed_in_transit"] is True
    assert analysis["days_overdue"] == 25
    assert "24 horas úteis" in analysis["regret_status"]


def test_case_10_pedido_pendente_por_item_coming_soon(data_engine):
    """Caso 10: Pedido #14 (Diego) pendente por conter o Ukulele Kala Barítono em pré-venda ('coming_soon')."""
    res = data_engine.lookup_orders(order_id=14)
    ord14 = res["orders"][0]
    assert ord14["status"] == "pending"
    assert ord14["items"][0]["product_status"] == "coming_soon"
    assert "coming_soon" in ord14["return_and_warranty_analysis"]["regret_status"]


def test_case_11_pedido_multi_itens_alto_valor_aline(data_engine):
    """Caso 11: Pedido #15 (Aline Borges) possui 2 instrumentos somando R$ 8.348,00 e está pendente."""
    res = data_engine.lookup_orders(order_id=15)
    ord15 = res["orders"][0]
    assert ord15["order_id"] == 15
    assert len(ord15["items"]) == 2
    assert ord15["total_brl"] == 8348.0
    assert "cancelamento imediato" in ord15["return_and_warranty_analysis"]["regret_status"]


def test_case_12_pedidos_multiplos_thiago_endereco_invalido(data_engine):
    """Caso 12: Pedido #2 (entregue) e Pedido #20 (cancelado por endereço inválido de Thiago Barbosa Lima)."""
    res2 = data_engine.lookup_orders(order_id=2)
    assert res2["found"] is True
    assert res2["orders"][0]["status"] == "delivered"

    res20 = data_engine.lookup_orders(order_id=20)
    assert res20["found"] is True
    ord20 = res20["orders"][0]
    assert ord20["status"] == "cancelled"
    assert "inválido" in ord20["notes"]


# --- BATERIA D: Trocas, Devoluções CDC e Garantias Complexas ---

def test_case_13_defeito_apos_30d_dentro_90d_garantia_legal_leticia(data_engine):
    """Caso 13: Pedido #7 (Letícia) entregue há 36 dias -> fora dos 30d da loja, mas dentro dos 90d do CDC."""
    res = data_engine.lookup_orders(order_id=7)
    ord7 = res["orders"][0]
    analysis = ord7["return_and_warranty_analysis"]
    assert analysis["days_since_estimated_delivery"] == 36
    assert analysis["within_30d_store_defect_window"] is False
    assert analysis["within_90d_legal_warranty"] is True
    assert "DENTRO DA GARANTIA LEGAL DE 90 DIAS" in analysis["defect_warranty_status"]


def test_case_14_itens_nao_elegiveis_para_troca_setup_boquilha(policy_engine):
    """Caso 14: Recuperação da Seção 4.4 sobre itens inelegíveis (setup sob encomenda, venda final, boquilhas)."""
    pol = policy_engine.retrieve_policies("posso trocar violão com regulagem especial ou boquilha de sopro?")
    contents = " ".join([s["content"] for s in pol["sections"]])
    assert "4.4 Itens ESTRITAMENTE NÃO Elegíveis para Troca" in contents
    assert "Boquilhas" in contents


def test_case_15_exclusao_garantia_mau_uso_e_terceiros(policy_engine):
    """Caso 15: Recuperação da Seção 8.3 sobre perda de garantia por reparo não autorizado e desgaste natural."""
    pol = policy_engine.retrieve_policies("levei no luthier e a corda estourou, a garantia cobre?")
    contents = " ".join([s["content"] for s in pol["sections"]])
    assert "8.3 O que NÃO é coberto pela garantia" in contents
    assert "não autorizados" in contents


def test_case_16_avaria_transporte_recusa_no_ato(policy_engine):
    """Caso 16: Orientação da Seção 5.2 para recusar entrega em caso de avaria aparente no transporte."""
    pol = policy_engine.retrieve_policies("caixa chegou amassada com avaria no frete da transportadora")
    contents = " ".join([s["content"] for s in pol["sections"]])
    assert "RECUSAR O RECEBIMENTO NO ATO DA ENTREGA" in contents


# --- BATERIA E: LGPD, Fora de Expediente e Guardrails Avançados ---

def test_case_17_lgpd_exclusao_dados_e_nao_compartilhamento(policy_engine):
    """Caso 17: Conformidade LGPD (Lei 13.709/2018) sobre marketing e exclusão de dados."""
    pol = policy_engine.retrieve_policies("quero excluir meus dados pessoais pela LGPD")
    sec_keys = [s["section_key"] for s in pol["sections"]]
    assert "privacidade_lgpd" in sec_keys
    contents = " ".join([s["content"] for s in pol["sections"]])
    assert "13.709/2018" in contents


def test_case_18_horario_funcionamento_domingo_e_sabado(policy_engine):
    """Caso 18: Consulta de horários aos sábados (09h-13h), domingos/feriados (fechado) e datas especiais."""
    pol = policy_engine.retrieve_policies("qual o horário de funcionamento no sábado e no domingo?")
    sec_keys = [s["section_key"] for s in pol["sections"]]
    assert "horarios" in sec_keys


def test_case_19_pedido_misto_acessorios_e_fender_telecaster(data_engine, policy_engine):
    """Caso 19: Detecta acessórios proibidos (cabo/pedal) na frase mista, mas encontra a Fender Telecaster."""
    acc = policy_engine.check_out_of_scope_accessory("Quero um cabo P10, um pedal e uma guitarra Fender Telecaster")
    assert acc is not None
    assert acc["is_out_of_scope"] is True

    tele = data_engine.get_product_details("Fender Telecaster")
    assert tele["found"] is True
    assert tele["effective_price"] == 5400.0
    assert tele["stock_quantity"] == 15


def test_case_20_escalonamento_gerencia_usados_e_aluguel(policy_engine):
    """Caso 20: Dúvidas fora das políticas previstas (instrumento usado na troca / aluguel) escalonam à gerência (Seção 10)."""
    pol = policy_engine.retrieve_policies("vocês aceitam violão usado como parte de pagamento ou fazem aluguel?")
    sec_keys = [s["section_key"] for s in pol["sections"]]
    assert "disposicoes_finais" in sec_keys
    contents = " ".join([s["content"] for s in pol["sections"]])
    assert "gerência" in contents


# --- BATERIA F: 10 Novos Cenários Avançados de Ponta a Ponta (Casos 21 a 30) ---

def test_case_21_desconto_ativo_crafter_ht100_derruba_pagamento_combinado(data_engine):
    """Caso 21: Promoção ativa de 18% no Crafter HT-100 reduz preço de R$ 2.399 para R$ 1.967,18 (< R$ 2.000)."""
    prod = data_engine.get_product_details("Crafter HT-100")
    assert prod["found"] is True
    assert prod["original_price"] == 2399.0
    assert prod["has_active_promotion"] is True
    assert prod["effective_price"] == 1967.18
    assert prod["payment_conditions"]["pix"]["discount_applied"] is False
    assert prod["payment_conditions"]["combined_payment"]["allowed"] is False


def test_case_22_pedido_10_confirmado_e_bloqueio_busca_sem_order_id(data_engine):
    """Caso 22: Pedido #10 (confirmed, R$ 8.732) e validação de bloqueio de busca sem order_id (D3 / LGPD)."""
    res_sem_id = data_engine.lookup_orders()
    assert res_sem_id["found"] is False
    assert res_sem_id["error"] == "order_id_required"

    res10 = data_engine.lookup_orders(order_id=10)
    assert res10["found"] is True
    o10 = res10["orders"][0]
    assert o10["order_id"] == 10
    assert o10["status"] == "confirmed"
    assert "phone" not in o10["customer"]
    assert "email" not in o10["customer"]
    assert "city" not in o10["customer"]


def test_case_23_historico_duplo_pedro_oliveira_boleto_cancelado_e_garantia_expirada(data_engine):
    """Caso 23: Pedidos #1 (entregue há 151 dias, fora dos 90d) e #19 (boleto não confirmado) de Pedro Henrique Oliveira."""
    res1 = data_engine.lookup_orders(order_id=1)
    assert res1["found"] is True
    o1 = res1["orders"][0]
    assert o1["status"] == "delivered"
    assert o1["return_and_warranty_analysis"]["days_since_estimated_delivery"] == 151
    assert o1["return_and_warranty_analysis"]["within_90d_legal_warranty"] is False

    res19 = data_engine.lookup_orders(order_id=19)
    assert res19["found"] is True
    o19 = res19["orders"][0]
    assert o19["status"] == "cancelled"
    assert "Pagamento não confirmado" in o19["notes"]


def test_case_24_pedido_18_cancelado_sem_estoque_mas_rozini_rc104_disponivel_hoje(data_engine):
    """Caso 24: Pedido #18 (Gustavo Nunes) cancelado por falta de estoque na época, mas Rozini RC-104 tem 10 un. hoje."""
    res = data_engine.lookup_orders(order_id=18)
    assert res["found"] is True
    o18 = res["orders"][0]
    assert o18["status"] == "cancelled"
    assert "Item fora de estoque" in o18["notes"]

    prod = data_engine.get_product_details("Rozini RC-104")
    assert prod["found"] is True
    assert prod["status"] == "active"
    assert prod["stock_quantity"] == 10
    assert prod["effective_price"] == 459.9


def test_case_25_pedido_17_cancelado_antes_processamento_e_troca_preferencia(data_engine, policy_engine):
    """Caso 25: Pedido #17 (Matheus Correia) cancelado antes do processamento e política de troca por preferência (Seção 4.3)."""
    res = data_engine.lookup_orders(order_id=17)
    assert res["found"] is True
    assert res["orders"][0]["status"] == "cancelled"
    assert "antes do processamento" in res["orders"][0]["notes"]

    pol = policy_engine.retrieve_policies("trocar de modelo por preferência diferença de valor")
    contents = " ".join([s["content"] for s in pol["sections"]])
    assert "4.3 Trocas por Preferência" in contents


def test_case_26_promocoes_ativas_taylor_110e_e_kalani_tenor(data_engine):
    """Caso 26: Promoções ativas no Taylor 110e (8% OFF -> R$ 5.519,08 em 12x) e Kalani KAL-700T (10% OFF -> R$ 323,10 em 4x)."""
    taylor = data_engine.get_product_details("Taylor 110e")
    assert taylor["has_active_promotion"] is True
    assert taylor["effective_price"] == 5519.08
    assert taylor["payment_conditions"]["credit_card"]["max_installments_without_interest"] == 12

    kalani = data_engine.get_product_details("Kalani KAL-700T")
    assert kalani["has_active_promotion"] is True
    assert kalani["effective_price"] == 323.10
    assert kalani["payment_conditions"]["credit_card"]["max_installments_without_interest"] == 4


def test_case_27_baterias_acusticas_frete_grande_porte_e_exclusao_pele_queda(data_engine, policy_engine):
    """Caso 27: Listagem das 3 baterias acústicas, frete especial de grande porte (Seção 5.2) e exclusão de garantia (Seção 8.3)."""
    drums = data_engine.search_catalog(category="Baterias e Percussão")
    assert len(drums["available_products"]) == 3

    pol_ship = policy_engine.retrieve_policies("frete bateria acústica grande porte Dourados")
    assert "INSTRUMENTOS DE GRANDE PORTE" in " ".join([s["content"] for s in pol_ship["sections"]])

    pol_war = policy_engine.retrieve_policies("garantia pele rasgada queda mau uso")
    assert "8.3 O que NÃO é coberto pela garantia" in " ".join([s["content"] for s in pol_war["sections"]])


def test_case_28_teclados_sintetizadores_e_bloqueio_pedal_suporte_cabo(data_engine, policy_engine):
    """Caso 28: Busca dos 3 teclados sintetizadores (Korg, Roland, Nord) e bloqueio de pedal/suporte/cabo avulso."""
    keys = data_engine.search_catalog(category="Teclados e Pianos")
    assert len(keys["available_products"]) == 3
    prices = sorted([p["effective_price"] for p in keys["available_products"]])
    assert prices == [1127.0, 9351.0, 19567.0]

    acc = policy_engine.check_out_of_scope_accessory("Quero levar o Korg Synth 1 Pro junto com um pedal de sustain, um suporte em X e um cabo P10")
    assert acc is not None
    assert acc["is_out_of_scope"] is True


def test_case_29_categorias_vazias_orquestra_e_higiene_boquilha_palheta_sopro(data_engine, policy_engine):
    """Caso 29: Categorias vazias (Cordas Orquestrais e Sopros) e não falso-positivo em 'palhetas de sopro'."""
    orq = data_engine.search_catalog(category="Cordas Orquestrais")
    assert len(orq["available_products"]) == 0

    acc = policy_engine.check_out_of_scope_accessory("qual a regra sobre troca de boquilhas e garantia de palhetas de sopro?")
    assert acc is None


def test_case_30_compra_lote_escola_yamaha_c40_e_escalonamento_atacado(data_engine, policy_engine):
    """Caso 30: Estoque de 12 unidades do Yamaha C40 (R$ 599,90) para lote de 5 un. e escalonamento de desconto CNPJ à gerência."""
    c40 = data_engine.get_product_details("Yamaha C40 Nylon")
    assert c40["found"] is True
    assert c40["stock_quantity"] == 12
    assert c40["effective_price"] == 599.9

    pol = policy_engine.retrieve_policies("desconto de atacado para CNPJ escola de música lote")
    sec_keys = [s["section_key"] for s in pol["sections"]]
    assert "disposicoes_finais" in sec_keys


def test_policy_engine_real_pdf_extraction(policy_engine):
    """Valida a extração real das 10 seções do PDF 'políticas_da_loja.pdf' e normalização."""
    assert len(policy_engine.sections) == 10
    # Verifica que todas as seções extraíram texto do PDF
    for key, sec in policy_engine.sections.items():
        assert "pdf_extracted_text" in sec
        assert len(sec["pdf_extracted_text"]) > 40
        # Nenhum typo com acento no domínio
        assert "empóriodamusica" not in sec["content"]


def test_lookup_orders_tool_enforces_d3(data_engine, policy_engine):
    """Valida que a ferramenta de pedido exige order_id e remove dados sensíveis (D3 / LGPD)."""
    from src.tools import execute_tool

    # Chamada sem order_id
    res_err = execute_tool("lookup_customer_orders", {}, data_engine, policy_engine)
    assert res_err["found"] is False
    assert res_err["error"] == "order_id_required"

    # Chamada com order_id válido
    res_ok = execute_tool("lookup_customer_orders", {"order_id": 1}, data_engine, policy_engine)
    assert res_ok["found"] is True
    assert len(res_ok["orders"]) == 1
    cust = res_ok["orders"][0]["customer"]
    assert cust["customer_id"] == 3
    assert cust["name"] == "Pedro Henrique Oliveira"
    assert "phone" not in cust
    assert "email" not in cust
    assert "city" not in cust



