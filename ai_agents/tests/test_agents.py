import pytest
from ai_agents.schemas import ReceiptOutput, InflationAnalysis, ChatMessage
from ai_agents.receipt_agent import ReceiptAgent
from ai_agents.inflation_agent import InflationAgent
from ai_agents.memory_agent import MemoryAgent
from ai_agents.orchestrator import AgentOrchestrator

def test_receipt_agent_mock():
    agent = ReceiptAgent()
    ocr_text = (
        "MIGROS TICARET A.S.\n"
        "TARIH: 12.07.2026\n"
        "PINAR SUT 1L  47.90\n"
        "DOMESTOS TEMIZLIK   35.50\n"
        "TOPLAM: 83.40"
    )
    
    # We use mock=True for unit testing to avoid network API dependencies
    result = agent.parse_ocr_text(ocr_text, mock=True)
    
    assert isinstance(result, ReceiptOutput)
    assert result.store == "Migros"
    assert result.date == "2026-07-12"
    assert result.total == 83.40
    assert len(result.items) >= 2
    
    # Check normalization and categorization
    pınar_süt = next((item for item in result.items if "Pınar" in item.name or "Sut" in item.name), None)
    assert pınar_süt is not None
    assert pınar_süt.category == "Gıda"
    
    domestos = next((item for item in result.items if "Domestos" in item.name), None)
    assert domestos is not None
    assert domestos.category == "Temizlik"

def test_inflation_calculation():
    agent = InflationAgent()
    
    base_basket = [
        {"name": "Pınar Süt", "category": "Gıda", "price": 40.0, "quantity": 2},
        {"name": "Duru Sabun", "category": "Temizlik", "price": 30.0, "quantity": 1}
    ]
    
    current_basket = [
        {"name": "Pınar Süt", "category": "Gıda", "price": 50.0, "quantity": 2},
        {"name": "Duru Sabun", "category": "Temizlik", "price": 33.0, "quantity": 1}
    ]
    
    # Calculate inflation
    calc_results = agent.calculate_personal_inflation(base_basket, current_basket)
    
    # Pınar Süt base spend = 80 TL (change = +25%)
    # Duru Sabun base spend = 30 TL (change = +10%)
    # Weighted Change = (80*0.25 + 30*0.10) / 110 = 23 / 110 = 20.909% -> 20.91%
    assert calc_results["personal_inflation"] == 20.91
    
    # Check category values
    categories = calc_results["categories"]
    assert "Gıda" in categories
    assert "Temizlik" in categories
    assert categories["Gıda"]["weight"] == round((80 / 110) * 100, 2)
    assert categories["Gıda"]["personal_inflation"] == 25.0
    assert categories["Temizlik"]["personal_inflation"] == 10.0

def test_inflation_analysis_mock():
    agent = InflationAgent()
    
    calc_results = {
        "personal_inflation": 20.91,
        "categories": {
            "Gıda": {"weight": 72.73, "personal_inflation": 25.0},
            "Temizlik": {"weight": 27.27, "personal_inflation": 10.0}
        }
    }
    
    official_tuik = {"TÜFE": 15.0, "Gıda": 12.0, "Temizlik": 8.0}
    
    analysis = agent.generate_analysis(calc_results, official_tuik, mock=True)
    
    assert isinstance(analysis, InflationAnalysis)
    assert analysis.personal_inflation == 20.91
    assert analysis.official_inflation == 15.0
    assert analysis.difference == 5.91
    assert "kişisel enflasyonunuz" in analysis.analysis.lower()

def test_memory_context_formatting():
    agent = MemoryAgent()
    user_memory = {
        "monthly_budget": 8000,
        "savings_target": 1500,
        "favorite_stores": ["Migros", "Bim"],
        "favorite_products": ["Süt", "Ekmek"],
        "goals_summary": "Tasarruf etmek istiyorum",
        "past_conversations_summary": "Daha önce bütçe konuştuk."
    }
    
    context = agent.format_memory_context(user_memory)
    
    assert "8000" in context
    assert "1500" in context
    assert "Migros" in context
    assert "Süt" in context

def test_memory_chat_mock():
    agent = MemoryAgent()
    user_memory = {
        "monthly_budget": 8000,
        "savings_target": 1500,
        "favorite_stores": ["Migros", "Bim"],
        "personal_inflation": 44.0
    }
    
    response = agent.generate_chat_response(
        user_memory=user_memory,
        user_message="Bütçem ne durumda?",
        history=[],
        mock=True
    )
    
    assert isinstance(response, str)
    assert "8000" in response

def test_orchestrator_mock():
    orchestrator = AgentOrchestrator()
    
    # 1. Test receipt parsing facade
    receipt_ocr = "BIM\nTARIH: 01.07.2026\nSUT 20.00\nTOPLAM: 20.00"
    receipt_res = orchestrator.process_receipt(receipt_ocr, mock=True)
    assert receipt_res.store == "Bim"
    
    # 2. Test inflation facade
    base = [{"name": "Sut", "category": "Gıda", "price": 10.0, "quantity": 1}]
    cur = [{"name": "Sut", "category": "Gıda", "price": 12.0, "quantity": 1}]
    official = {"TÜFE": 10.0}
    inf_res = orchestrator.analyze_inflation(base, cur, official, mock=True)
    assert inf_res.personal_inflation == 20.0
    
    # 3. Test chat facade
    chat_res = orchestrator.get_chat_response(
        user_memory={"monthly_budget": 5000},
        user_message="Bütçem?",
        history=[],
        mock=True
    )
    assert "5000" in chat_res
