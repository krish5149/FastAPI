from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CreateProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    description: str
    price: int

class ProductResonse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    prod_id: str
    name: str
    description: str
    price: int
    added_at: datetime
