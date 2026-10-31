"""Motor de dados relacionais e regras de negócio para a Empório da Música.

Carrega os dados dos CSVs em um banco relacional SQLite em memória,
implementa cálculo de preços com promoções ativas, histórico de promoções expiradas,
classificação inteligente de status (incluindo Ponta de Estoque para descontinuados com saldo),
simulação precisa de pagamento e avaliação de elegibilidade de trocas/devoluções pelo CDC.
"""

import csv
import json
import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import DATA_DIR, REFERENCE_DATE


def normalize_text(text: str) -> str:
    """Remove acentos, pontuação excessiva e converte para minúsculas."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).strip()


def format_brl(val: float) -> str:
    """Formata valores numéricos para o padrão monetário brasileiro (ex: R$ 2.199,00)."""
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")




class DataEngine:
    """Gerencia as consultas relacionais aos dados operacionais da Empório da Música."""

    def __init__(self, data_dir: Optional[Path] = None, reference_date: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.reference_date_str = reference_date or REFERENCE_DATE
        self.reference_date = datetime.strptime(self.reference_date_str, "%Y-%m-%d")
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_database()

    def _init_database(self) -> None:
        """Cria as tabelas e carrega os 6 CSVs com tratamento de dados e tipos."""
        cur = self.conn.cursor()

        # 1. Categories
        cur.execute("""
            CREATE TABLE categories (
                category_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT
            );
        """)

        # 2. Products
        cur.execute("""
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                price_brl REAL NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                description TEXT,
                stock_quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                specs TEXT,
                created_at TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (category_id)
            );
        """)

        # 3. Promotions
        cur.execute("""
            CREATE TABLE promotions (
                promotion_id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                discount_percent REAL NOT NULL,
                description TEXT,
                is_active INTEGER NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );
        """)

        # 4. Customers
        cur.execute("""
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                city TEXT NOT NULL
            );
        """)

        # 5. Orders
        cur.execute("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL,
                total_brl REAL NOT NULL,
                payment_method TEXT NOT NULL,
                tracking_code TEXT,
                estimated_delivery TEXT,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            );
        """)

        # 6. Order Items
        cur.execute("""
            CREATE TABLE order_items (
                order_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );
        """)

        self.conn.commit()
        self._load_csv_data()
        self._create_views_and_indices()

    def _load_csv_data(self) -> None:
        """Carrega os arquivos CSV tratando codificação e tipos."""
        cur = self.conn.cursor()

        files_map = {
            "categories": ("desafio_tecnico_ai_eng - categories.csv", [
                ("category_id", int), ("name", str), ("description", str)
            ]),
            "products": ("desafio_tecnico_ai_eng - products.csv", [
                ("product_id", int), ("price_brl", float), ("name", str),
                ("category_id", int), ("description", str), ("stock_quantity", int),
                ("status", str), ("specs", str), ("created_at", str)
            ]),
            "promotions": ("desafio_tecnico_ai_eng - promotions.csv", [
                ("promotion_id", int), ("product_id", int), ("discount_percent", float),
                ("description", str), ("is_active", int)
            ]),
            "customers": ("desafio_tecnico_ai_eng - customers.csv", [
                ("customer_id", int), ("name", str), ("phone", str),
                ("email", str), ("city", str)
            ]),
            "orders": ("desafio_tecnico_ai_eng - orders.csv", [
                ("order_id", int), ("customer_id", int), ("order_date", str),
                ("status", str), ("total_brl", float), ("payment_method", str),
                ("tracking_code", str), ("estimated_delivery", str), ("notes", str)
            ]),
            "order_items": ("desafio_tecnico_ai_eng - order_items.csv", [
                ("order_id", int), ("quantity", int), ("product_id", int)
            ]),
        }

        for table, (filename, col_specs) in files_map.items():
            path = self.data_dir / filename
            if not path.exists():
                continue
            with open(path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows_to_insert = []
                cols = [c[0] for c in col_specs]
                placeholders = ",".join(["?"] * len(cols))
                for row in reader:
                    values = []
                    for col_name, col_type in col_specs:
                        val = row.get(col_name, "")
                        if val is None or val == "":
                            values.append("" if col_type == str else 0)
                        else:
                            try:
                                values.append(col_type(val.strip()))
                            except (ValueError, TypeError):
                                values.append(val)
                    rows_to_insert.append(values)

                cur.executemany(
                    f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})",
                    rows_to_insert
                )

        self.conn.commit()

    def _create_views_and_indices(self) -> None:
        """Cria índices e views úteis para queries de alto desempenho."""
        cur = self.conn.cursor()
        cur.execute("CREATE INDEX idx_products_cat ON products(category_id);")
        cur.execute("CREATE INDEX idx_promotions_prod ON promotions(product_id);")
        cur.execute("CREATE INDEX idx_orders_cust ON orders(customer_id);")
        cur.execute("CREATE INDEX idx_order_items_order ON order_items(order_id);")
        self.conn.commit()

    # =========================================================================
    # REGRAS DE NEGÓCIO: PROMOÇÕES, PREÇO EFETIVO E PARCELAMENTO
    # =========================================================================

    def calculate_payment_plans(self, original_price: float, effective_price: float, has_active_promo: bool) -> Dict[str, Any]:
        """Calcula as condições de pagamento conforme Seções 3, 3.1 e 6.2 do manual."""
        # Seção 6.2: O desconto de PIX (5%) NÃO se aplica sobre preços já promocionais.
        if has_active_promo:
            pix_price = round(effective_price, 2)
            pix_discount_applied = False
            pix_note = f"Preço promocional ativo de {format_brl(effective_price)}: desconto de 5% do PIX não cumulativo (Seção 6.2)."
        else:
            pix_price = round(effective_price * 0.95, 2)
            pix_discount_applied = True
            pix_note = f"À vista no PIX com 5% de desconto: {format_brl(pix_price)} (economia de {format_brl(effective_price - pix_price)})."

        # Parcelamento no Cartão de Crédito sem juros (Seção 3.1):
        # • Até 3x: sem juros, parcela mínima R$ 50.
        # • De 4x a 6x: sem juros, parcela mínima R$ 80.
        # • De 7x a 12x: sem juros, parcela mínima R$ 100.
        installments = []
        base_credit = effective_price

        for n in range(1, 13):
            val = round(base_credit / n, 2)
            if n <= 3:
                allowed = (val >= 50.0) or (n == 1)
                min_req = 50.0
            elif 4 <= n <= 6:
                allowed = (val >= 80.0)
                min_req = 80.0
            else:
                allowed = (val >= 100.0)
                min_req = 100.0

            if allowed:
                installments.append({
                    "installments": n,
                    "installment_value": val,
                    "total": base_credit,
                    "interest_free": True
                })

        max_allowed_installments = max([i["installments"] for i in installments]) if installments else 1
        combined_allowed = effective_price > 2000.0
        cg_free_shipping = effective_price >= 500.0
        cg_shipping_cost = 0.0 if cg_free_shipping else 35.0

        return {
            "effective_price": effective_price,
            "original_price": original_price,
            "has_active_promo": has_active_promo,
            "pix": {
                "price": pix_price,
                "discount_percent": 5 if pix_discount_applied else 0,
                "discount_applied": pix_discount_applied,
                "note": pix_note
            },
            "debit_card": {
                "price": effective_price,
                "note": "À vista no débito (todas as bandeiras)."
            },
            "boleto": {
                "price": effective_price,
                "note": "À vista no boleto bancário (compensação em até 3 dias úteis)."
            },
            "credit_card": {
                "max_installments_without_interest": max_allowed_installments,
                "available_plans": installments,
                "rules": "Regra 3.1: até 3x (mín. R$ 50,00), 4x a 6x (mín. R$ 80,00), 7x a 12x (mín. R$ 100,00)."
            },
            "combined_payment": {
                "allowed": combined_allowed,
                "rule": (
                    f"Permitida combinação de formas de pagamento (ex.: PIX + cartão) pois o valor ({format_brl(effective_price)}) é acima de R$ 2.000,00 (Seção 3.1)."
                    if combined_allowed else
                    f"NÃO permitida combinação de formas de pagamento (ex.: PIX + cartão) pois o valor ({format_brl(effective_price)}) não ultrapassa R$ 2.000,00 (Seção 3.1)."
                )
            },
            "shipping_campo_grande": {
                "free_shipping": cg_free_shipping,
                "shipping_fee": cg_shipping_cost,
                "total_with_shipping": round(effective_price + cg_shipping_cost, 2),
                "note": (
                    "Frete GRÁTIS para Campo Grande (pedido acima de R$ 500,00 — entrega por motoboy em 1 a 3 dias úteis)."
                    if cg_free_shipping else
                    f"Taxa fixa de R$ 35,00 para Campo Grande (pedido abaixo de R$ 500,00 — total com frete: {format_brl(effective_price + cg_shipping_cost)}, entrega por motoboy em 1 a 3 dias úteis)."
                )
            }
        }

    # =========================================================================
    # CATÁLOGO DE PRODUTOS
    # =========================================================================

    def _get_product_promo_info(self, product_id: int) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Retorna a promoção ativa (se houver) e o histórico de promoções expiradas."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM promotions WHERE product_id = ?", (product_id,))
        rows = cur.fetchall()

        active_promo = None
        expired_promos = []

        for r in rows:
            p_dict = {
                "promotion_id": r["promotion_id"],
                "discount_percent": r["discount_percent"],
                "description": r["description"],
                "is_active": bool(r["is_active"])
            }
            if r["is_active"] == 1:
                active_promo = p_dict
            else:
                expired_promos.append(p_dict)

        return active_promo, expired_promos

    def _resolve_category_id(self, category_str: Optional[str]) -> Optional[int]:
        """Identifica o category_id de forma tolerante a acentos, plurais e sinônimos."""
        if not category_str:
            return None
        norm_cat = normalize_text(category_str)

        # Mapeamento semântico direto
        aliases = {
            "violao": 5, "violoes": 5, "violão": 5, "violões": 5,
            "guitarra": 1, "guitarras": 1,
            "baixo": 2, "baixos": 2, "contrabaixo": 2, "bass": 2,
            "bateria": 3, "baterias": 3, "percussao": 3, "percussão": 3,
            "teclado": 4, "teclados": 4, "piano": 4, "pianos": 4, "sintetizador": 4,
            "sopro": 6, "madeira": 6, "flauta": 6, "clarinete": 6, "sax": 6, "saxofone": 6,
            "metal": 7, "metais": 7, "trompete": 7, "trombone": 7, "tuba": 7, "trompa": 7,
            "orquestral": 8, "orquestrais": 8, "violino": 8, "violoncelo": 8,
            "ukulele": 9, "ukuleles": 9, "uke": 9
        }

        for alias, cid in aliases.items():
            if alias in norm_cat:
                return cid

        cur = self.conn.cursor()
        cur.execute("SELECT category_id, name FROM categories")
        for r in cur.fetchall():
            if normalize_text(r["name"]) in norm_cat or norm_cat in normalize_text(r["name"]):
                return r["category_id"]

        return None

    def search_catalog(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        strings_filter: Optional[str] = None,
        electronics_filter: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Busca no catálogo com filtros avançados, calculando preços promocionais ativos."""
        cur = self.conn.cursor()

        cat_id_filter = self._resolve_category_id(category)
        requested_empty_cat = None

        if cat_id_filter in [6, 7, 8]:
            cur.execute("SELECT name, description FROM categories WHERE category_id = ?", (cat_id_filter,))
            cat_row = cur.fetchone()
            requested_empty_cat = {
                "category_id": cat_id_filter,
                "name": cat_row["name"],
                "description": cat_row["description"],
                "notice": (
                    f"A categoria '{cat_row['name']}' faz parte do catálogo da Empório da Música, "
                    f"porém no momento todos os modelos estão temporariamente sem unidades cadastradas no estoque."
                )
            }

        # Busca todos os produtos para filtragem com preço efetivo e specs
        sql = """
            SELECT p.*, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE 1=1
        """
        params = []
        if cat_id_filter:
            sql += " AND p.category_id = ?"
            params.append(cat_id_filter)

        cur.execute(sql, params)
        raw_products = cur.fetchall()

        available_items = []
        clearance_items = []  # Ponta de Estoque (descontinuados com saldo > 0)
        out_of_stock_items = []
        discontinued_items = []
        coming_soon_items = []

        def _stem_pt(word: str) -> str:
            w = normalize_text(word)
            if w.endswith("oes"):
                return w[:-3] + "ao"
            if w.endswith("res") and len(w) > 4:
                return w[:-2]
            if w.endswith("s") and len(w) > 3:
                return w[:-1]
            return w

        query_terms = [_stem_pt(t) for t in query.split()] if query else []

        for p in raw_products:
            p_name = p["name"]
            p_desc = p["description"] or ""
            p_specs_raw = p["specs"] or "{}"
            try:
                specs_dict = json.loads(p_specs_raw)
            except Exception:
                specs_dict = {}

            # Filtro textual tolerante a acentos e plural
            if query_terms:
                combined_text = normalize_text(f"{p_name} {p_desc} {p_specs_raw} {p['category_name']}")
                if not all(term in combined_text for term in query_terms):
                    continue

            # Filtros de specs (ex.: cordas de nylon ou aço)
            if strings_filter:
                p_strings = normalize_text(specs_dict.get("strings", ""))
                if normalize_text(strings_filter) not in p_strings:
                    continue

            # Filtro elétrico / eletroacústico
            if electronics_filter:
                p_elec = specs_dict.get("electronics", "").lower()
                if electronics_filter.lower() == "yes" and p_elec not in ["yes", "sim", "true"]:
                    continue
                if electronics_filter.lower() == "no" and p_elec not in ["no", "não", "nao", "false"]:
                    continue

            # Preço e promoções
            orig_price = float(p["price_brl"])
            active_promo, expired_promos = self._get_product_promo_info(p["product_id"])

            if active_promo:
                discount_val = (orig_price * active_promo["discount_percent"]) / 100.0
                effective_price = round(orig_price - discount_val, 2)
                has_promo = True
            else:
                effective_price = orig_price
                has_promo = False

            # Filtros de preço sobre o PREÇO EFETIVO
            if max_price is not None and effective_price > max_price:
                continue
            if min_price is not None and effective_price < min_price:
                continue

            stock = int(p["stock_quantity"])
            status = p["status"].lower()

            item_data = {
                "product_id": p["product_id"],
                "name": p_name,
                "category_id": p["category_id"],
                "category_name": p["category_name"],
                "original_price": orig_price,
                "effective_price": effective_price,
                "has_active_promotion": has_promo,
                "promotion_details": active_promo,
                "expired_promotions": expired_promos,
                "stock_quantity": stock,
                "status": status,
                "specs": specs_dict,
                "short_description": p_desc
            }

            # Classificação de status
            if status == "active" and stock > 0:
                available_items.append(item_data)
            elif status == "discontinued" and stock > 0:
                # Regra de negócio: Ponta de Estoque (gatilho comercial de últimas unidades!)
                item_data["commercial_badge"] = "PONTA DE ESTOQUE (Últimas Unidades - Modelo Descontinuado)"
                item_data["urgency_note"] = (
                    f"Atenção: Este modelo saiu de linha pelo fabricante, mas a loja ainda possui "
                    f"{stock} unidades remanescentes com preço de oportunidade imperdível! "
                    f"Não haverá reposição de estoque."
                )
                clearance_items.append(item_data)
            elif status == "active" and stock == 0:
                item_data["stock_notice"] = "Temporariamente fora de estoque (Seção 7.3 do manual)."
                out_of_stock_items.append(item_data)
            elif status == "discontinued" and stock == 0:
                item_data["stock_notice"] = "Descontinuado e esgotado. Não faz mais parte do catálogo regular."
                discontinued_items.append(item_data)
            elif status == "coming_soon":
                item_data["stock_notice"] = "Lançamento / Chegando em breve ao estoque."
                coming_soon_items.append(item_data)

        # Ordena disponíveis e ponta de estoque por preço
        available_items.sort(key=lambda x: x["effective_price"])
        clearance_items.sort(key=lambda x: x["effective_price"])

        response = {
            "query_criteria": {
                "query": query,
                "category": category,
                "max_price": max_price,
                "min_price": min_price,
                "strings_filter": strings_filter
            },
            "total_available_in_stock": len(available_items),
            "available_products": available_items[:limit],
            "clearance_opportunities": clearance_items,
            "out_of_stock_products": out_of_stock_items,
            "discontinued_products": discontinued_items,
            "coming_soon_products": coming_soon_items,
            "empty_category_notice": requested_empty_cat
        }

        return response

    def get_product_details(self, product_id_or_name: Any) -> Dict[str, Any]:
        """Retorna a ficha completa de um produto, simulação financeira e sugestões similares."""
        cur = self.conn.cursor()

        product = None
        if isinstance(product_id_or_name, int) or (isinstance(product_id_or_name, str) and product_id_or_name.isdigit()):
            cur.execute("""
                SELECT p.*, c.name as category_name
                FROM products p
                JOIN categories c ON p.category_id = c.category_id
                WHERE p.product_id = ?
            """, (int(product_id_or_name),))
            product = cur.fetchone()
        else:
            name_term = f"%{str(product_id_or_name).strip()}%"
            cur.execute("""
                SELECT p.*, c.name as category_name
                FROM products p
                JOIN categories c ON p.category_id = c.category_id
                WHERE p.name LIKE ?
                ORDER BY p.product_id ASC
                LIMIT 1
            """, (name_term,))
            product = cur.fetchone()

            # Fallback de busca por tokens normalizados (ex: 'Kala Barítono Cedar (KA-ABP-CTG)' -> 'Kala KA-ABP-CTG Barítono Cedar')
            if not product:
                stopwords = {"violao", "violoes", "ukulele", "ukuleles", "guitarra", "guitarras", "baixo", "baixos", "bateria", "teclado", "de", "do", "da", "com", "para"}
                q_tokens = [t for t in re.findall(r"[a-z0-9]+", normalize_text(str(product_id_or_name))) if t not in stopwords and len(t) >= 2]
                if q_tokens:
                    cur.execute("""
                        SELECT p.*, c.name as category_name
                        FROM products p
                        JOIN categories c ON p.category_id = c.category_id
                    """)
                    best_row = None
                    best_score = 0
                    for row in cur.fetchall():
                        target_norm = normalize_text(f"{row['name']} {row['description'] or ''}")
                        matched_count = sum(1 for tok in q_tokens if tok in target_norm)
                        if matched_count > best_score and matched_count >= max(1, len(q_tokens) // 2):
                            best_score = matched_count
                            best_row = row
                    product = best_row

        if not product:
            return {"found": False, "message": f"Produto '{product_id_or_name}' não encontrado no catálogo."}

        orig_price = float(product["price_brl"])
        pid = product["product_id"]
        active_promo, expired_promos = self._get_product_promo_info(pid)

        if active_promo:
            disc = (orig_price * active_promo["discount_percent"]) / 100.0
            effective_price = round(orig_price - disc, 2)
            has_promo = True
        else:
            effective_price = orig_price
            has_promo = False

        payment_plans = self.calculate_payment_plans(orig_price, effective_price, has_promo)

        specs_dict = {}
        if product["specs"]:
            try:
                specs_dict = json.loads(product["specs"])
            except Exception:
                pass

        stock = int(product["stock_quantity"])
        status = product["status"].lower()

        # Busca similares disponíveis caso o item esteja fora de estoque, descontinuado ou em pré-venda (coming_soon)
        similar_options = []
        if stock == 0 or status in ["discontinued", "coming_soon"]:
            cur.execute("""
                SELECT p.product_id, p.name, p.price_brl, p.stock_quantity, p.status, p.specs
                FROM products p
                WHERE p.category_id = ? AND p.product_id != ? AND p.status = 'active' AND p.stock_quantity > 0
            """, (product["category_id"], pid))
            candidates = cur.fetchall()
            prod_norm_name = normalize_text(product["name"])
            subtypes = [kw for kw in ["7 cordas", "baritono", "tenor", "concert", "soprano", "dreadnought", "folk"] if kw in prod_norm_name]

            scored_candidates = []
            for sim in candidates:
                sim_active_promo, _ = self._get_product_promo_info(sim["product_id"])
                sim_price = float(sim["price_brl"])
                if sim_active_promo:
                    sim_price = round(sim_price * (1 - sim_active_promo["discount_percent"] / 100.0), 2)
                    sim_pix = sim_price
                else:
                    sim_pix = round(sim_price * 0.95, 2)
                sim_norm_name = normalize_text(sim["name"])
                subtype_match = any(st in sim_norm_name for st in subtypes) if subtypes else False
                price_diff = abs(sim_price - effective_price)
                scored_candidates.append((0 if subtype_match else 1, price_diff, {
                    "product_id": sim["product_id"],
                    "name": sim["name"],
                    "price": sim_price,
                    "pix_price_5_percent_off": sim_pix,
                    "stock_quantity": sim["stock_quantity"]
                }))

            scored_candidates.sort(key=lambda x: (x[0], x[1]))
            similar_options = [item[2] for item in scored_candidates[:4]]

        if stock == 0 or status == "coming_soon":
            payment_plans["unavailable_item_warning"] = (
                "ATENÇÃO: Este produto NÃO está disponível para pronta entrega hoje (sem estoque ou em pré-venda). "
                "NÃO ofereça compra nem desconto no PIX para este item indisponível; apresente os preços e o desconto no PIX apenas dos modelos similares disponíveis em similar_available_alternatives."
            )

        # Montagem do status comercial e diretrizes da Seção 7.3
        status_guidance = ""
        is_clearance = False
        if status == "active" and stock > 0:
            status_guidance = "Produto disponível em estoque para pronta entrega."
        elif status == "discontinued" and stock > 0:
            is_clearance = True
            status_guidance = (
                f"[OPORTUNIDADE DE PONTA DE ESTOQUE]: Este modelo foi descontinuado pelo fabricante, "
                f"mas a loja ainda conta com {stock} unidades em saldo físico a um preço excelente. "
                f"Incentive o cliente a fechar rápido pois são as últimas unidades e não haverá reposição!"
            )
        elif status == "active" and stock == 0:
            status_guidance = (
                "Produto temporariamente esgotado no estoque. Conforme Seção 7.3 do manual, "
                "informe a indisponibilidade temporária e apresente os modelos similares sugeridos."
            )
        elif status == "discontinued" and stock == 0:
            status_guidance = (
                "Produto descontinuado e sem estoque. Conforme Seção 7.3 do manual, "
                "informe que saiu de linha e sugira os modelos sucessores/equivalentes sugeridos."
            )
        elif status == "coming_soon":
            status_guidance = (
                "Lançamento em pré-venda (status 'coming_soon' — chegando em breve ao estoque). "
                "Não está disponível para retirada imediata hoje; apresente os modelos similares disponíveis para pronta entrega."
            )

        expired_guidance = None
        if expired_promos and not has_promo:
            exp_list = ", ".join([f"{ep['description']} ({int(ep['discount_percent'])}% off)" for ep in expired_promos])
            expired_guidance = (
                f"ATENÇÃO (Seção 7.3 — Promoção Expirada): Este produto já teve promoção(ões) anterior(es) que estão ENCERRADAS/VENCIDAS no sistema: [{exp_list}]. "
                f"Você DEVE informar explicitamente na sua resposta que a campanha ({exp_list}) já foi encerrada/expirou, apresentar o preço atual ({format_brl(effective_price)}) "
                f"e destacar o desconto de 5% no PIX ({format_brl(payment_plans['pix']['price'])})."
            )
            status_guidance = f"{status_guidance} | {expired_guidance}"

        return {
            "found": True,
            "product_id": pid,
            "name": product["name"],
            "category_name": product["category_name"],
            "original_price": orig_price,
            "effective_price": effective_price,
            "has_active_promotion": has_promo,
            "active_promotion": active_promo,
            "expired_promotions": expired_promos,
            "expired_promotions_guidance": expired_guidance,
            "stock_quantity": stock,
            "status": status,
            "is_clearance_opportunity": is_clearance,
            "status_guidance_for_agent": status_guidance,
            "specs": specs_dict,
            "description": product["description"],
            "payment_conditions": payment_plans,
            "similar_available_alternatives": similar_options
        }

    # =========================================================================
    # PEDIDOS, RASTREAMENTO E ELEGIBILIDADE DE TROCA/DEVOLUÇÃO
    # =========================================================================

    def lookup_orders(
        self,
        order_id: Optional[int] = None,
        tracking_code: Optional[str] = None,
        customer_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Localiza pedidos e analisa elegibilidade de devolução por arrependimento e garantia CDC."""
        cur = self.conn.cursor()

        sql = """
            SELECT o.*, c.name as customer_name, c.phone as customer_phone,
                   c.email as customer_email, c.city as customer_city
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            WHERE 1=1
        """
        params = []
        if order_id and customer_query:
            term = f"%{customer_query.strip()}%"
            sql += " AND (o.order_id = ? OR c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ?)"
            params.extend([order_id, term, term, term])
        elif order_id:
            sql += " AND o.order_id = ?"
            params.append(order_id)
        elif tracking_code:
            sql += " AND UPPER(o.tracking_code) = UPPER(?)"
            params.append(tracking_code.strip())
        elif customer_query:
            term = f"%{customer_query.strip()}%"
            sql += " AND (c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ?)"
            params.extend([term, term, term])

        cur.execute(sql, params)
        orders_rows = cur.fetchall()

        # Fallback por tokens normalizados para nomes compostos / homônimos (ex: 'Bruno Martins' -> 'Bruno Carvalho Martins')
        if not orders_rows and customer_query:
            q_tokens = [t for t in re.findall(r"\w+", normalize_text(customer_query)) if len(t) >= 2]
            if q_tokens:
                cur.execute("""
                    SELECT o.*, c.name as customer_name, c.phone as customer_phone,
                           c.email as customer_email, c.city as customer_city
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.customer_id
                """)
                all_orders = cur.fetchall()
                orders_rows = [
                    r for r in all_orders
                    if all(
                        tok in normalize_text(f"{r['customer_name']} {r['customer_email']} {r['customer_phone']}")
                        for tok in q_tokens
                    )
                ]

        if not orders_rows:
            return {
                "found": False,
                "message": f"Nenhum pedido encontrado com os critérios fornecidos (ID: {order_id}, Rastreio: {tracking_code}, Cliente: {customer_query})."
            }

        orders_result = []
        for o in orders_rows:
            oid = o["order_id"]

            # Busca itens do pedido
            cur.execute("""
                SELECT oi.quantity, p.product_id, p.name as product_name, p.price_brl,
                       p.status as product_status, c.name as category_name
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN categories c ON p.category_id = c.category_id
                WHERE oi.order_id = ?
            """, (oid,))
            items = [dict(r) for r in cur.fetchall()]

            # Status e datas
            status = o["status"].lower()
            order_date_str = o["order_date"]
            estimated_del_str = o["estimated_delivery"]
            order_date = datetime.strptime(order_date_str, "%Y-%m-%d")

            # Avaliação de prazos para trocas e devoluções (Seção 4 e 8 do manual)
            # A data de referência é REFERENCE_DATE (25/03/2026)
            return_eligibility = {
                "order_status": status,
                "eligible_for_7d_regret_return": False,
                "days_since_estimated_delivery": None,
                "regret_return_policy": "Art. 49 CDC e Seção 4.1: devolução em até 7 dias corridos após o recebimento, com frete pago pela loja e estorno integral em até 10 dias úteis.",
                "defect_exchange_policy": "Seção 4.2 e 8.1: até 30 dias corridos na loja para defeitos de fabricação; após 30 dias aciona garantia do fabricante com intermediação da loja (garantia legal de 90 dias pelo CDC)."
            }

            if status == "delivered":
                # Assume entrega realizada na data estimada ou na data do pedido se sem estimativa
                delivery_date = datetime.strptime(estimated_del_str, "%Y-%m-%d") if estimated_del_str else order_date
                days_since_del = (self.reference_date - delivery_date).days
                return_eligibility["days_since_estimated_delivery"] = days_since_del

                # Se entregue há 7 dias ou menos da data de referência
                if 0 <= days_since_del <= 7:
                    return_eligibility["eligible_for_7d_regret_return"] = True
                    return_eligibility["regret_status"] = f"DENTRO DO PRAZO: Entregue há {days_since_del} dias (prazo de 7 dias vigente)."
                else:
                    return_eligibility["eligible_for_7d_regret_return"] = False
                    return_eligibility["regret_status"] = f"PRAZO EXPIRADO: Entregue há {days_since_del} dias (o prazo de 7 dias para arrependimento já encerrou)."

                # Defeito de fabricação (30 dias loja vs 90 dias CDC legal vs Fabricante)
                within_30d = (0 <= days_since_del <= 30)
                within_90d = (0 <= days_since_del <= 90)
                return_eligibility["within_30d_store_defect_window"] = within_30d
                return_eligibility["within_90d_legal_warranty"] = within_90d

                if within_30d:
                    return_eligibility["defect_warranty_status"] = (
                        f"DENTRO DOS 30 DIAS DA LOJA ({days_since_del} dias da entrega): elegível para troca direta na loja por defeito de fabricação (Seção 4.2)."
                    )
                elif within_90d:
                    return_eligibility["defect_warranty_status"] = (
                        f"FORA DOS 30 DIAS DA LOJA ({days_since_del} dias da entrega), MAS DENTRO DA GARANTIA LEGAL DE 90 DIAS DO CDC (Seção 8.1) E GARANTIA DO FABRICANTE (Seção 8.2). "
                        "Conforme Seção 4.2, após 30 dias o cliente deve acionar a garantia do fabricante, e a Empório da Música pode intermediar o processo mediante solicitação."
                    )
                else:
                    return_eligibility["defect_warranty_status"] = (
                        f"Prazo de 30 dias da loja e 90 dias da garantia legal CDC expirados ({days_since_del} dias da entrega). "
                        "Verifique o certificado da Garantia do Fabricante (que varia de 6 meses a 2 anos conforme a marca — Seção 8.2)."
                    )

            elif status in ["pending", "confirmed"]:
                coming_soon_items = [it["product_name"] for it in items if it.get("product_status") == "coming_soon"]
                if coming_soon_items:
                    return_eligibility["regret_status"] = (
                        f"Pedido pendente aguardando chegada de lote de pré-venda/lançamento ('coming_soon') para: {', '.join(coming_soon_items)}. "
                        "O cliente pode optar por aguardar o despacho ou solicitar cancelamento/troca imediata sem custo."
                    )
                else:
                    return_eligibility["regret_status"] = "Pedido ainda em processamento/envio. O cliente pode solicitar cancelamento imediato antes do despacho."
            elif status == "shipped":
                is_delayed = False
                days_overdue = 0
                if estimated_del_str:
                    est_date = datetime.strptime(estimated_del_str, "%Y-%m-%d")
                    if self.reference_date > est_date:
                        is_delayed = True
                        days_overdue = (self.reference_date - est_date).days
                return_eligibility["is_delayed_in_transit"] = is_delayed
                return_eligibility["days_overdue"] = days_overdue
                if is_delayed:
                    return_eligibility["regret_status"] = (
                        f"ATENÇÃO — ENTREGA EM ATRASO ({days_overdue} dias além da previsão {estimated_del_str}). "
                        "Conforme Seção 7.3 (Reclamação), ouça o cliente com empatia, informe o código de rastreio, "
                        "registre a reclamação e encaminhe ao setor responsável com prazo de retorno de até 24 horas úteis. "
                        "O direito de arrependimento (7 dias) valerá a partir do recebimento, ou o cliente pode recusar/cancelar."
                    )
                else:
                    return_eligibility["regret_status"] = "Pedido em trânsito. O direito de arrependimento (7 dias) começará a contar a partir da data efetiva de recebimento."
            elif status == "cancelled":
                return_eligibility["regret_status"] = f"Pedido já cancelado. Motivo registrado: {o['notes'] or 'Não informado'}."

            cust_city = o["customer_city"]
            if normalize_text(cust_city) == "campo grande":
                shipping_rule_note = (
                    "Cliente em Campo Grande/MS (Seção 5.1): Frete GRÁTIS para pedidos acima de R$ 500,00 (motoboy em 1 a 3 dias úteis); "
                    "taxa fixa de R$ 35,00 abaixo de R$ 500,00."
                )
            else:
                shipping_rule_note = (
                    f"ATENÇÃO — CLIENTE DO INTERIOR ({cust_city}/MS — Seção 5.1 e 5.2): O frete grátis acima de R$ 500,00 é EXCLUSIVO para Campo Grande! "
                    f"Para {cust_city}, NÃO há frete grátis por valor; o envio é cobrado à parte e realizado via Correios (PAC: 5 a 12 dias úteis / SEDEX: 2 a 5 dias úteis) ou Jadlog (3 a 8 dias úteis)."
                )

            orders_result.append({
                "order_id": oid,
                "customer": {
                    "customer_id": o["customer_id"],
                    "name": o["customer_name"],
                    "phone": o["customer_phone"],
                    "email": o["customer_email"],
                    "city": cust_city
                },
                "order_date": order_date_str,
                "status": status,
                "total_brl": float(o["total_brl"]),
                "payment_method": o["payment_method"],
                "tracking_code": o["tracking_code"] or "Ainda não gerado (aguardando despacho / mudança para status 'shipped')",
                "estimated_delivery": estimated_del_str or "Em definição",
                "shipping_policy_for_customer_city": shipping_rule_note,
                "notes": o["notes"],
                "items": items,
                "return_and_warranty_analysis": return_eligibility
            })

        return {
            "found": True,
            "total_orders": len(orders_result),
            "orders": orders_result
        }
