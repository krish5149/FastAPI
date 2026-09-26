from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class OrderItemsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    prod_id: str
    name: str
    quantity: int
    price: int

class SkippedItems(BaseModel):
    prod_id: str
    name: str
    requested_quantity: int
    reason: str
    removed_from_cart: bool

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    order_id: str
    status: str
    total_item: int
    total_price: float
    items: list[OrderItemsResponse]

class Order_Response(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    order_id: str
    status: str
    process_id: uuid.UUID
    created_at: datetime
    items: list[OrderItemsResponse]

class OrderOutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    order_id: str
    name: str
    price: float

class CheckOutResponse(BaseModel):
    order: OrderResponse | None = None
    skipped_items: list[SkippedItems]

class UpdateStatus(BaseModel):
    status: str

class SellerOrderItemResponse(BaseModel):
    prod_id: str
    name: str
    quantity: int
    price: int


class SellerOrderResponse(BaseModel):
    order_id: str
    status: str
    created_at: datetime
    items: list[SellerOrderItemResponse]