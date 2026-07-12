import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from .config import get_genai_client, DEFAULT_MODEL
from .schemas import ReceiptOutput, ReceiptItem

class ReceiptAgent:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.genai = get_genai_client()
        
        # Load system instruction
        prompt_path = Path(__file__).resolve().parent / "prompts" / "receipt_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_instruction = f.read()

    def parse_ocr_text(self, ocr_text: str, current_date: Optional[str] = None, mock: bool = False) -> ReceiptOutput:
        """
        Parses OCR text of a receipt to extract structured JSON data.
        If mock is True or GEMINI_API_KEY is not set, runs a local rule-based parsing fallback.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if mock or not api_key:
            return self._parse_mock(ocr_text, current_date)

        try:
            model = self.genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction
            )
            
            # Format user prompt
            now_str = current_date or datetime.now().strftime("%Y-%m-%d")
            prompt = f"Bugünün Tarihi (Current Date): {now_str}\n\nAnaliz Edilecek Fiş OCR Çıktısı (Receipt OCR Text):\n{ocr_text}"
            
            # Request structured output from Gemini
            response = model.generate_content(
                contents=prompt,
                generation_config=self.genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=ReceiptOutput,
                    temperature=0.1
                )
            )
            
            # Load and return parsed output
            data = json.loads(response.text)
            return ReceiptOutput(**data)
            
        except Exception as e:
            # If the API call fails, fall back to mock parser so the application doesn't crash
            import warnings
            warnings.warn(f"Gemini API call failed: {str(e)}. Falling back to mock parsing.")
            return self._parse_mock(ocr_text, current_date)

    def _parse_mock(self, ocr_text: str, current_date: Optional[str]) -> ReceiptOutput:
        """
        A rule-based regex fallback parser for local testing and offline development.
        """
        # 1. Store Detection
        store = "Bilinmeyen Market"
        ocr_lower = ocr_text.lower()
        if "migros" in ocr_lower:
            store = "Migros"
        elif "bim" in ocr_lower:
            store = "Bim"
        elif "a101" in ocr_lower or "a-101" in ocr_lower:
            store = "A101"
        elif "sok" in ocr_lower or "şok" in ocr_lower:
            store = "Şok"
        elif "carrefour" in ocr_lower:
            store = "Carrefour"
        elif "file" in ocr_lower:
            store = "File"

        # 2. Date Detection
        date_pattern = r"(\d{2})[./-](\d{2})[./-](\d{4}|\d{2})"
        date_match = re.search(date_pattern, ocr_text)
        if date_match:
            day, month, year = date_match.groups()
            if len(year) == 2:
                year = "20" + year
            date = f"{year}-{month}-{day}"
        else:
            date = current_date or datetime.now().strftime("%Y-%m-%d")

        # 3. Total Detection
        total_pattern = r"(?:toplam|top|tutar|toplamtutar)\s*:?\s*([0-9]+[.,][0-9]{2})"
        total_match = re.search(total_pattern, ocr_text, re.IGNORECASE)
        total = 0.0
        if total_match:
            total_val = total_match.group(1).replace(",", ".")
            try:
                total = float(total_val)
            except ValueError:
                pass

        # 4. Item Extraction (mock parsing lines containing prices)
        items = []
        lines = ocr_text.split("\n")
        
        # Simple extraction logic: check lines that look like "ITEM_NAME ... PRICE"
        item_line_pattern = r"^([A-ZÇĞİÖŞÜa-zçğıöşü\s0-9%*]+?)\s+([0-9]+[.,][0-9]{2})(?:\s+[A-Z])?$"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip totals or headers
            if any(k in line.lower() for k in ["toplam", "kdv", "fiş", "tarih", "saat", "nakit", "kredi"]):
                continue

            match = re.match(item_line_pattern, line)
            if match:
                name_raw = match.group(1).strip()
                price_val = match.group(2).replace(",", ".")
                
                try:
                    price = float(price_val)
                except ValueError:
                    continue
                
                # Exclude lines that are just numbers or too short
                if len(name_raw) < 3 or name_raw.replace(".", "").isdigit():
                    continue

                # Normalize name
                name = name_raw.title()
                
                # Categorization heuristic
                category = "Gıda"
                name_l = name.lower()
                if any(x in name_l for x in ["deterjan", "sivi sabun", "sabun", "domestos", "yuzey", "bulasik"]):
                    category = "Temizlik"
                elif any(x in name_l for x in ["sampuan", "parfum", "deodorant", "krem", "ruj"]):
                    category = "Kozmetik"
                elif any(x in name_l for x in ["ilac", "vitamin", "sargi", "aspirin", "agri"]):
                    category = "Sağlık"
                elif "su" in name_l.split() or any(x in name_l for x in ["kola", "fanta", "gazoz", "cay", "kahve", "bira", "sarap", "viski"]):
                    category = "İçecek"
                elif any(x in name_l for x in ["pecete", "kagit havlu", "ampul", "pil", "tencere", "tabak"]):
                    category = "Ev"
                elif any(x in name_l for x in ["bez", "mama", "biberon", "islak mendil"]):
                    category = "Bebek"

                items.append(ReceiptItem(
                    name=name,
                    category=category,
                    price=price,
                    quantity=1,
                    confidence=0.90
                ))

        # If no items could be parsed, provide a fallback item to avoid returning empty array
        if not items:
            items.append(ReceiptItem(
                name="Tanımlanamayan Ürün",
                category="Diğer",
                price=total if total > 0 else 10.0,
                quantity=1,
                confidence=0.50
            ))

        # Adjust total if it was 0
        if total == 0.0:
            total = sum(item.price * item.quantity for item in items)

        return ReceiptOutput(
            store=store,
            date=date,
            total=round(total, 2),
            items=items
        )
