from pydantic import BaseModel, Field
from typing import List, Optional

class ReceiptItem(BaseModel):
    name: str = Field(description="Normalized name of the product. Standardized brand casing (e.g. 'Pınar Süt' instead of 'PINAR SUT'), general description.")
    category: str = Field(description="Product category. Must be one of: Gıda, Temizlik, Kozmetik, Sağlık, İçecek, Ev, Bebek, Diğer.")
    price: float = Field(description="Price of a single unit of the product. If unit price is not explicit, calculate it from total price and quantity.")
    quantity: int = Field(description="Quantity purchased. Defaults to 1 if not specified.")
    confidence: float = Field(description="Confidence score for this item extraction between 0.0 and 1.0.")

class ReceiptOutput(BaseModel):
    store: str = Field(description="Detected market/store name. (e.g. Migros, Bim, A101, Carrefour)")
    date: str = Field(description="Detected date of the receipt in YYYY-MM-DD format. Fall back to current date if not found.")
    total: float = Field(description="Total amount of the receipt.")
    items: List[ReceiptItem] = Field(description="List of extracted products from the receipt.")

class InflationAnalysis(BaseModel):
    personal_inflation: float = Field(description="Calculated personal inflation rate as a percentage.")
    official_inflation: float = Field(description="TÜİK official inflation rate as a percentage.")
    difference: float = Field(description="Difference between personal and official inflation (personal - official).")
    analysis: str = Field(description="Natural language explanation in Turkish explaining why there is a difference, what drove the inflation, and suggestions for saving money.")

class ChatMessage(BaseModel):
    role: str = Field(description="Role of the speaker: 'user' or 'assistant'.")
    content: str = Field(description="The textual content of the message.")
