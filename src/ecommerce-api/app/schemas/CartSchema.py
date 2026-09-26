from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class CartCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: str
    quantity: int | None = None

class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cart_id: str
    name: str
    process_id: uuid.UUID
    prod_id: str
    quantity: int
    added_at: datetime

class GetCartItemsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    prod_id: str
    name: str
    quantity: int
    added_at: datetime
    process_id: uuid.UUID

class GetCartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cart_id: str
    user_id: int
    total_items: int
    items: list[GetCartItemsResponse]
    


