from typing import List, Dict, Any, Optional
from .schemas import ReceiptOutput, InflationAnalysis, ChatMessage
from .receipt_agent import ReceiptAgent
from .inflation_agent import InflationAgent
from .memory_agent import MemoryAgent
from .config import DEFAULT_MODEL

class AgentOrchestrator:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Initializes the AI Agents Orchestrator and all underlying agents.
        """
        self.model_name = model_name
        self.receipt_agent = ReceiptAgent(model_name=self.model_name)
        self.inflation_agent = InflationAgent(model_name=self.model_name)
        self.memory_agent = MemoryAgent(model_name=self.model_name)

    def process_receipt(
        self, 
        ocr_text: str, 
        current_date: Optional[str] = None, 
        mock: bool = False
    ) -> ReceiptOutput:
        """
        Takes raw receipt OCR text and returns structured receipt JSON.
        """
        return self.receipt_agent.parse_ocr_text(
            ocr_text=ocr_text, 
            current_date=current_date, 
            mock=mock
        )

    def analyze_inflation(
        self,
        base_basket: List[Dict[str, Any]],
        current_basket: List[Dict[str, Any]],
        official_tuik_data: Dict[str, float],
        mock: bool = False
    ) -> InflationAnalysis:
        """
        Calculates personal inflation based on the comparison of two shopping baskets
        and generates an AI commentary comparing it with official TÜİK inflation data.
        """
        # Calculate rates
        calc_results = self.inflation_agent.calculate_personal_inflation(
            base_basket=base_basket,
            current_basket=current_basket
        )
        
        # Generate LLM analysis
        return self.inflation_agent.generate_analysis(
            personal_data=calc_results,
            official_tuik_data=official_tuik_data,
            mock=mock
        )

    def get_chat_response(
        self,
        user_memory: Dict[str, Any],
        user_message: str,
        history: List[ChatMessage],
        mock: bool = False
    ) -> str:
        """
        Generates a personalized response to the user's message using memory and message history.
        """
        return self.memory_agent.generate_chat_response(
            user_memory=user_memory,
            user_message=user_message,
            history=history,
            mock=mock
        )
