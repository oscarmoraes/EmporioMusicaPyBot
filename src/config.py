"""Módulo de configuração do sistema Empório da Música."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env se existir
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Diretórios
DATA_DIR = BASE_DIR / "data"

# Configurações de LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.2"))

# Data de referência simulada para testes e auditoria de prazos de devolução/garantia
# (Último pedido nos dados é de 22/03/2026)
REFERENCE_DATE = os.getenv("REFERENCE_DATE", "2026-03-25")

# Dados Oficiais da Loja (Manual de Políticas)
STORE_INFO = {
    "name": "Empório da Música",
    "legal_name": "Empório da Música Instrumentos Musicais Ltda.",
    "cnpj": "12.345.678/0001-90",
    "address": "Rua 14 de Maio, 3200 — Centro, Campo Grande - MS, CEP 79202-333",
    "phone": "(67) 3341-4444",
    "whatsapp_support": "(67) 3321-4500",
    "email": "contato@emporiodamusica.com.br",
    "foundation_year": 2008,
    "hours": {
        "weekdays": "Segunda a Sexta-feira: 09:00 às 18:00",
        "saturday": "Sábado: 09:00 às 13:00",
        "sunday_and_holidays": "Domingo e Feriados: Fechado"
    }
}
