import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import get_genai_client, DEFAULT_MODEL
from .schemas import ChatMessage

class MemoryAgent:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.genai = get_genai_client()
        
        # Load system persona prompt
        prompt_path = Path(__file__).resolve().parent / "prompts" / "chat_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_instruction_template = f.read()

    def format_memory_context(self, user_memory: Dict[str, Any]) -> str:
        """
        Formats raw user memory variables into a structured text block for prompt injection.
        """
        monthly_budget = user_memory.get("monthly_budget", "Belirtilmedi")
        savings_target = user_memory.get("savings_target", "Belirtilmedi")
        
        favorite_stores = user_memory.get("favorite_stores", [])
        favorite_stores_str = ", ".join(favorite_stores) if favorite_stores else "Belirtilmedi"
        
        favorite_products = user_memory.get("favorite_products", [])
        favorite_products_str = ", ".join(favorite_products) if favorite_products else "Belirtilmedi"
        
        goals = user_memory.get("goals_summary", "Belirtilmedi")
        history_summary = user_memory.get("past_conversations_summary", "Geçmiş konuşma kaydı bulunmuyor.")

        # Formatting personal inflation metrics if passed
        inflation_pct = user_memory.get("personal_inflation", None)
        inflation_str = f"%{inflation_pct}" if inflation_pct is not None else "Hesaplanmadı"

        memory_block = (
            f"=== KULLANICI BELLEĞİ VE YATIRIM/BÜTÇE PROFİLİ ===\n"
            f"- Aylık Harcama Bütçe Limiti: {monthly_budget} TL\n"
            f"- Aylık Tasarruf Hedefi: {savings_target} TL\n"
            f"- Kişisel Enflasyon Oranı: {inflation_str}\n"
            f"- En Sık Alışveriş Yapılan Marketler: {favorite_stores_str}\n"
            f"- En Çok Satın Alınan Ürünler: {favorite_products_str}\n"
            f"- Kullanıcının Özel Hedefleri: {goals}\n"
            f"- Geçmiş Konuşmaların Özeti: {history_summary}\n"
            f"=================================================\n"
        )
        return memory_block

    def generate_chat_response(
        self,
        user_memory: Dict[str, Any],
        user_message: str,
        history: List[ChatMessage],
        mock: bool = False
    ) -> str:
        """
        Generates a personalized response to the user's message using memory and message history.
        """
        memory_context = self.format_memory_context(user_memory)
        full_system_instruction = f"{self.system_instruction_template}\n\n{memory_context}"

        api_key = os.getenv("GEMINI_API_KEY")
        if mock or not api_key:
            return self._generate_mock_chat_response(user_message, user_memory)

        try:
            model = self.genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=full_system_instruction
            )

            # Build conversation history for Gemini API
            # Gemini chat session takes a list of contents: [{'role': 'user'|'model', 'parts': [str]}]
            contents = []
            for msg in history:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [msg.content]})
            
            # Append latest user message
            contents.append({"role": "user", "parts": [user_message]})

            # Generate
            response = model.generate_content(contents)
            return response.text.strip()

        except Exception as e:
            import warnings
            warnings.warn(f"Gemini API chat failed: {str(e)}. Using mock response.")
            return self._generate_mock_chat_response(user_message, user_memory)

    def _generate_mock_chat_response(self, user_message: str, user_memory: Dict[str, Any]) -> str:
        """
        A rule-based chatbot simulator in Turkish that incorporates user goals and memory.
        """
        msg_l = user_message.lower()
        budget = user_memory.get("monthly_budget", 5000)
        target = user_memory.get("savings_target", 1000)
        stores = user_memory.get("favorite_stores", ["Migros", "Bim"])
        inflation = user_memory.get("personal_inflation", 44)

        if "bütçe" in msg_l or "butce" in msg_l or "nasıl gidiyorum" in msg_l or "nasil gidiyorum" in msg_l:
            return (
                f"Bütçe durumunuzu inceledim. Bu ay için belirlediğiniz aylık bütçe limitiniz {budget} TL. "
                f"Şu ana kadarki harcama alışkanlıklarınıza bakılırsa hedefinizi tutturma yolundasınız. "
                f"Enflasyon oranınız da %{inflation} civarında seyrediyor. "
                f"Tasarruflarınızı artırmak için sık alışveriş yaptığınız {', '.join(stores)} gibi marketlerin kampanyalarını takip edebiliriz."
            )
        elif "tasarruf" in msg_l or "hedef" in msg_l or "birikim" in msg_l:
            return (
                f"Belirlediğiniz aylık tasarruf hedefiniz {target} TL. "
                f"Bu birikim hedefine ulaşmak için özellikle yüksek enflasyon gösteren ürünlerden kaçınmak mantıklı olacaktır. "
                f"Her alışverişte en ucuz ürüne yönelmek, market markalarını (private label) tercih etmek aylık bazda ortalama %15-20 tasarruf sağlayabilir."
            )
        elif "enflasyon" in msg_l:
            return (
                f"Kişisel enflasyonunuz şu anda %{inflation} seviyesinde. "
                f"Bu oran, resmi oranlarla kıyaslandığında sepetinizdeki ürünlerin ne kadar hızlı zamlandığını gösteriyor. "
                f"Gıda ve temizlik harcamalarını optimize ederek kişisel enflasyonunuzu düşürebiliriz."
            )
        else:
            return (
                f"Merhaba! Harcamalarınızı ve finansal hedeflerinizi inceleyerek size destek olmak için buradayım. "
                f"Aylık bütçeniz ({budget} TL) veya tasarruf hedefiniz ({target} TL) hakkında daha detaylı konuşmak ister misiniz?"
            )
