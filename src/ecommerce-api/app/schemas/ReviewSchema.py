from pydantic import BaseModel
from datetime import datetime

class AddReview(BaseModel):
    review_comment: str
    rating: int

class GetReviewSchema(BaseModel):
    prod_id: str
    review_id: str
    user_id: str
    review_comment: str
    rating: int
    reviewed_at: datetime

class UpdateReview(BaseModel):
    review_comment: str
    rating: int
