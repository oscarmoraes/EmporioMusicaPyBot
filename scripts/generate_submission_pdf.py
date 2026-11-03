"""Gera o PDF oficial de entrega do desafio técnico conforme requisitos da Artefact."""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "Oscar de Moraes - AI Engineer – Full-Stack para Aplicações com IA Generativa.pdf"

doc = SimpleDocTemplate(
    str(PDF_PATH),
    pagesize=letter,
    leftMargin=40,
    rightMargin=40,
    topMargin=36,
    bottomMargin=36
)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "TitleStyle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=colors.HexColor("#1E293B")
)
subtitle_style = ParagraphStyle(
    "SubStyle",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=16,
    textColor=colors.HexColor("#0284C7")
)
body_style = ParagraphStyle(
    "BodyStyle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#334155")
)
h2_style = ParagraphStyle(
    "H2",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=15,
    textColor=colors.HexColor("#0F172A"),
    spaceBefore=8,
    spaceAfter=4
)
bullet_style = ParagraphStyle(
    "BulletStyle",
    parent=body_style,
    leftIndent=12,
    bulletIndent=4
)

story = []

# Header
story.append(Paragraph("Technical Case Resolution — AI Engineer", title_style))
story.append(Paragraph("Artefact Brasil | Selection Process", subtitle_style))
story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284C7"), spaceBefore=2, spaceAfter=8))

# Metadata Table
meta_data = [
    [
        Paragraph("<b>Candidate:</b> Oscar de Moraes", body_style),
        Paragraph("<b>Role:</b> AI Engineer – Full-Stack para Aplicações com IA Generativa", body_style)
    ],
    [
        Paragraph("<b>Email:</b> oscarmoraes0@gmail.com", body_style),
        Paragraph("<b>LinkedIn:</b> linkedin.com/in/oscar-de-moraes-b81684116", body_style)
    ],
    [
        Paragraph("<b>GitHub:</b> <font color='#0284C7'><u>https://github.com/oscarmoraes/EmporioMusicaPyBot</u></font>", body_style),
        Paragraph("<b>Stack:</b> Python 3.12 / 3.13, SQLite, OpenAI API, Streamlit, Rich, Pytest", body_style)
    ]
]
t = Table(meta_data, colWidths=[240, 290])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
]))
story.append(t)
story.append(Spacer(1, 10))

# 1. Executive Summary
story.append(Paragraph("1. Executive Overview & Business Scenario", h2_style))
story.append(Paragraph(
    "<b>Empório da Música</b> is a traditional musical instruments store in Campo Grande/MS facing high customer service inquiry volumes. "
    "This project implements an autonomous conversational support agent (<b>Tom</b>) equipped with structured database retrieval, "
    "normative store policy adherence, zero-hallucination guardrails, and deterministic financial calculations.",
    body_style
))
story.append(Spacer(1, 6))

# 2. Key Architecture & Decisions
story.append(Paragraph("2. Technical Decisions & Architectural Highlights", h2_style))
story.append(Paragraph(
    "• <b>ReAct Orchestration via Native Tool Calling:</b> Avoids bloated, fragile frameworks (LangChain/CrewAI). "
    "Implements typed Pydantic tool schemas directly interfacing with OpenAI/Groq APIs with full multi-turn session memory.",
    bullet_style
))
story.append(Paragraph(
    "• <b>Relational SQLite in Memory:</b> Ingests the 6 operation CSVs into relational indexed tables. Deserializes semi-structured JSON "
    "specifications and eliminates Text-to-SQL hallucination risks by routing queries through safe, parameterized functions.",
    bullet_style
))
story.append(Paragraph(
    "• <b>Real PDF Normative Extraction (pypdf):</b> Parses the official store manual (<i>políticas_da_loja.pdf</i>) directly, "
    "collapsing whitespaces, resolving domain typos, and retaining complete contextual coherence without vector DB chunking loss.",
    bullet_style
))
story.append(Paragraph(
    "• <b>Deterministic Financial & Legal Computations in Python:</b> Installment ladders (§3.1: 1-3x min R$ 50, 4-6x min R$ 80, 7-12x min R$ 100), "
    "non-cumulative PIX 5% discounts (§6.2), strict R$ 500 Campo Grande shipping threshold, and statutory CDC time windows (7-day online regret, "
    "30-day store defect, 90-day legal warranty) computed in Python code, preventing LLM arithmetic hallucination.",
    bullet_style
))
story.append(Paragraph(
    "• <b>Strict LGPD Compliance & Privacy (Decision D3):</b> Customer order status lookup enforces mandatory <code>order_id</code>, "
    "eliminating CRM homonym leakage. All personal identifiable information (PII: phone, email, city) is stripped from LLM payloads.",
    bullet_style
))
story.append(Spacer(1, 6))

# 3. Test Suite & Verification
story.append(Paragraph("3. Automated Testing & Empirical Benchmark", h2_style))
story.append(Paragraph(
    "• <b>42 Pytest Automated Tests:</b> 100% pass rate covering edge cases (clearance items, out-of-stock active products, CDC deadlines, "
    "shipping tiers, and scope guardrails).",
    bullet_style
))
story.append(Paragraph(
    "• <b>Reproducible Automated Benchmark (<code>scripts/evaluate_agent.py</code>):</b> 10/10 scenarios passed (100.0% accuracy), "
    "~3.5s average latency, zero data leakage.",
    bullet_style
))
story.append(Paragraph(
    "• <b>5 Real Conversation Transcripts:</b> Documented in <code>examples/</code> with raw system tool inspection.",
    bullet_style
))
story.append(Spacer(1, 6))

# 4. How to Run
story.append(Paragraph("4. How to Execute the Project", h2_style))
story.append(Paragraph(
    "• <b>Clone:</b> <code>git clone https://github.com/oscarmoraes/EmporioMusicaPyBot.git</code><br/>"
    "• <b>Web UI (Streamlit):</b> <code>streamlit run app.py</code> (Interactive WhatsApp-style layout with 1-click test scenarios)<br/>"
    "• <b>CLI Interface (Rich):</b> <code>python main.py</code><br/>"
    "• <b>Automated Tests:</b> <code>python -m pytest -v tests/test_engine.py</code>",
    body_style
))

doc.build(story)
print(f"PDF successfully generated at: {PDF_PATH}")
