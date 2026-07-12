import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import get_genai_client, DEFAULT_MODEL
from .schemas import InflationAnalysis

class InflationAgent:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.genai = get_genai_client()
        
        # Load system instruction
        prompt_path = Path(__file__).resolve().parent / "prompts" / "inflation_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.system_instruction = f.read()

    def calculate_personal_inflation(
        self, 
        base_basket: List[Dict[str, Any]], 
        current_basket: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates personal inflation rate based on product price changes between two periods.
        Each basket item is expected to have: 'name', 'category', 'price', 'quantity'.
        """
        # Match products by name (case-insensitive, normalized)
        base_map = {item['name'].lower().strip(): item for item in base_basket}
        current_map = {item['name'].lower().strip(): item for item in current_basket}
        
        matched_changes = []
        matched_base_spend = 0.0
        
        # Product-to-product matching
        for name_key, base_item in base_map.items():
            if name_key in current_map:
                cur_item = current_map[name_key]
                base_price = float(base_item['price'])
                cur_price = float(cur_item['price'])
                qty = float(base_item['quantity'])
                
                if base_price > 0:
                    price_change = (cur_price - base_price) / base_price
                    item_spend = base_price * qty
                    matched_changes.append({
                        "name": base_item['name'],
                        "category": base_item['category'],
                        "price_change": price_change,
                        "base_spend": item_spend
                    })
                    matched_base_spend += item_spend

        # Fallback to category-average price comparison if direct product matches are insufficient
        category_inflation = {}
        category_weights = {}
        
        # Calculate category spending weights in the base month
        total_base_spend = sum(float(item['price']) * float(item['quantity']) for item in base_basket)
        if total_base_spend == 0:
            total_base_spend = 1.0  # Avoid division by zero
            
        cat_base_spends = {}
        for item in base_basket:
            cat = item['category']
            cat_base_spends[cat] = cat_base_spends.get(cat, 0.0) + (float(item['price']) * float(item['quantity']))
            
        for cat, spend in cat_base_spends.items():
            category_weights[cat] = spend / total_base_spend

        # Calculate category changes
        if len(matched_changes) >= 3:
            # We have enough direct product matches
            # Let's aggregate product changes by category
            cat_matched_changes = {}
            cat_matched_spend = {}
            for mc in matched_changes:
                cat = mc['category']
                cat_matched_changes[cat] = cat_matched_changes.get(cat, 0.0) + (mc['price_change'] * mc['base_spend'])
                cat_matched_spend[cat] = cat_matched_spend.get(cat, 0.0) + mc['base_spend']
                
            for cat, total_change_spend in cat_matched_changes.items():
                base_spend = cat_matched_spend[cat]
                category_inflation[cat] = total_change_spend / base_spend if base_spend > 0 else 0.0
                
            personal_rate = sum(mc['price_change'] * (mc['base_spend'] / matched_base_spend) for mc in matched_changes)
        else:
            # Fall back to category-level average unit price comparison
            # Group unit prices by category
            cat_base_prices = {}
            cat_cur_prices = {}
            for item in base_basket:
                cat = item['category']
                if cat not in cat_base_prices:
                    cat_base_prices[cat] = []
                cat_base_prices[cat].append(float(item['price']))
                
            for item in current_basket:
                cat = item['category']
                if cat not in cat_cur_prices:
                    cat_cur_prices[cat] = []
                cat_cur_prices[cat].append(float(item['price']))
                
            # Compute average unit price per category
            for cat, base_w in category_weights.items():
                base_avg = sum(cat_base_prices[cat]) / len(cat_base_prices[cat]) if cat_base_prices.get(cat) else 0
                cur_avg = sum(cat_cur_prices[cat]) / len(cat_cur_prices[cat]) if cat_cur_prices.get(cat) else base_avg
                
                if base_avg > 0:
                    category_inflation[cat] = (cur_avg - base_avg) / base_avg
                else:
                    category_inflation[cat] = 0.0
                    
            personal_rate = sum(category_inflation.get(cat, 0.0) * w for cat, w in category_weights.items())

        # Convert to percentage
        personal_inflation_pct = round(personal_rate * 100, 2)
        
        # Standardize weights and category inflation for output
        category_reports = {}
        for cat in category_weights:
            category_reports[cat] = {
                "weight": round(category_weights[cat] * 100, 2),
                "personal_inflation": round(category_inflation.get(cat, 0.0) * 100, 2)
            }

        return {
            "personal_inflation": personal_inflation_pct,
            "categories": category_reports
        }

    def generate_analysis(
        self,
        personal_data: Dict[str, Any],
        official_tuik_data: Dict[str, float],
        mock: bool = False
    ) -> InflationAnalysis:
        """
        Generates AI commentary comparing personal inflation with official TÜİK inflation.
        """
        personal_inflation = personal_data["personal_inflation"]
        official_inflation = official_tuik_data.get("TÜFE", 35.0)  # Default official TÜFE
        difference = round(personal_inflation - official_inflation, 2)

        api_key = os.getenv("GEMINI_API_KEY")
        if mock or not api_key:
            return self._generate_mock_analysis(personal_inflation, official_inflation, difference, personal_data, official_tuik_data)

        try:
            model = self.genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction
            )
            
            # Format comparison details for prompt
            comparison_details = []
            for cat, data in personal_data["categories"].items():
                tuik_val = official_tuik_data.get(cat, official_inflation)
                comparison_details.append(
                    f"- Kategori: {cat}\n"
                    f"  Sepetinizdeki Ağırlığı: %{data['weight']}\n"
                    f"  Sizin Enflasyonunuz: %{data['personal_inflation']}\n"
                    f"  TÜİK Resmi Enflasyonu: %{tuik_val}"
                )
            
            prompt = (
                f"KİŞİSEL ENFLASYON RAPORU\n"
                f"Hesaplanan Kişisel Enflasyon Oranı: %{personal_inflation}\n"
                f"Resmi TÜİK Genel Enflasyon Oranı (TÜFE): %{official_inflation}\n"
                f"Aradaki Fark: %{difference}\n\n"
                f"KATEGORİ BAZLI KARŞILAŞTIRMALAR:\n" + "\n".join(comparison_details)
            )

            # Call Gemini
            response = model.generate_content(
                contents=prompt,
                generation_config=self.genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=InflationAnalysis,
                    temperature=0.2
                )
            )

            data = json.loads(response.text)
            return InflationAnalysis(**data)

        except Exception as e:
            import warnings
            warnings.warn(f"Gemini API call failed in InflationAgent: {str(e)}. Using fallback analyzer.")
            return self._generate_mock_analysis(personal_inflation, official_inflation, difference, personal_data, official_tuik_data)

    def _generate_mock_analysis(
        self,
        personal_inflation: float,
        official_inflation: float,
        difference: float,
        personal_data: Dict[str, Any],
        official_tuik_data: Dict[str, float]
    ) -> InflationAnalysis:
        """
        Fallback generator that constructs a realistic financial analysis in Turkish.
        """
        # Find the highest inflation category in user's basket
        highest_cat = "Gıda"
        highest_val = -100.0
        for cat, data in personal_data["categories"].items():
            if data["personal_inflation"] > highest_val:
                highest_val = data["personal_inflation"]
                highest_cat = cat

        if difference > 0:
            analysis_text = (
                f"Bu ay kişisel enflasyonunuz %{personal_inflation} olarak hesaplandı ve resmi TÜİK enflasyon oranı olan %{official_inflation}'in %{difference} üzerinde gerçekleşti. "
                f"Bu durumun temel sebebi, bütçenizde önemli yer tutan '{highest_cat}' kategorisindeki harcamalarınızın fiyat artışının (%{highest_val}) resmi ortalamanın çok üstünde olmasıdır. "
                f"Harcamalarınızı düşürmek için özellikle yüksek fiyat artışı yaşayan bu kategoride alternatif markalara yönelmenizi ve market bazlı fiyat karşılaştırmaları yapmanızı tavsiye ederiz."
            )
        elif difference < 0:
            analysis_text = (
                f"Tebrikler! Kişisel enflasyonunuz %{personal_inflation} ile resmi TÜİK enflasyon oranı olan %{official_inflation}'in %{abs(difference)} altında kaldı. "
                f"Bütçenizi akıllıca yöneterek enflasyonun etkilerini azaltmayı başarmışsınız. Fiyat artışlarının görece düşük olduğu ürünleri tercih etmeniz bu sonuca katkı sağladı. "
                f"Tasarruf eğiliminizi devam ettirmek için bütçe hedeflerinizi koruyabilirsiniz."
            )
        else:
            analysis_text = (
                f"Kişisel enflasyon oranınız resmi TÜİK enflasyon oranı olan %{official_inflation} ile tamamen aynı gerçekleşti. "
                f"Tüketim sepetiniz ve harcama alışkanlıklarınız Türkiye genel ortalamasını birebir yansıtmaktadır. "
                f"Gelecek dönemlerde bütçe disiplinini korumak için en çok harcama yaptığınız kategorileri takip etmeye devam edebilirsiniz."
            )

        return InflationAnalysis(
            personal_inflation=personal_inflation,
            official_inflation=official_inflation,
            difference=difference,
            analysis=analysis_text
        )
