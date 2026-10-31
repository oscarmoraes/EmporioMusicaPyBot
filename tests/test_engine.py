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
            assert val >= 50.0 or n == 1
        elif 4 <= n <= 6:
            assert val >= 80.0
        elif 7 <= n <= 12:
            assert val >= 100.0

    # Não deve permitir parcelas que violem o piso mínimo
    assert max_inst <= 4


def test_customer_order_lookup_and_cdc_returns(data_engine):
    """Valida busca de pedidos por cliente e contagem de prazo para devolução por arrependimento."""
    # Pedro Henrique Oliveira (customer_id=3)
    orders = data_engine.lookup_orders(customer_query="Pedro Henrique")
    assert orders["found"] is True
    assert orders["total_orders"] >= 2

    # Pedido 1: entregue em out/2025 -> prazo de 7 dias de arrependimento expirado em 25/03/2026
    ord1 = [o for o in orders["orders"] if o["order_id"] == 1][0]
    assert ord1["status"] == "delivered"
    assert ord1["return_and_warranty_analysis"]["eligible_for_7d_regret_return"] is False
    assert "PRAZO EXPIRADO" in ord1["return_and_warranty_analysis"]["regret_status"]

    # Pedido 19: cancelado por falta de pagamento
    ord19 = [o for o in orders["orders"] if o["order_id"] == 19][0]
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
