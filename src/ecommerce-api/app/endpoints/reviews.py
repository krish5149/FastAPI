from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.dependencies import require_role
from sqlalchemy import select, update, delete
from ..core.ExceptionHandler import AppException
from ..models.user import User, UserRole
from ..core.error_codes import *
from ..core.dependencies import *
from ..core.idgenerator import generate_unique_review_code
from ..models.order import Order, OrderItems
from ..schemas.ReviewSchema import *
from ..models.product import Product
from sqlalchemy.orm import selectinload
from ..models.review import Review
from ..core.error_codes import Category,ErrorCode

router = APIRouter(prefix="/review",tags=["review"])

@router.post("/addreview", status_code=201)
async def add_review(product_id: str,reviews: AddReview,current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    # Check product exists
    product_query = await db.execute(select(Product).where(Product.prod_id == product_id))
    product = product_query.scalar_one_or_none()
    if product is None:
        raise AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product is not available from store",
            severity="warning",
            category=Category.PRODUCT,
            status_code=404
        )

    # Check user purchased and received the product
    order_query = await db.execute(
        select(Order)
        .join(OrderItems, OrderItems.order_id == Order.order_id)
        .where(
            OrderItems.prod_id == product_id,
            Order.user_id == current_user.user_code,
            Order.status == "DELIVERED"
        )
    )
    order = order_query.first()
    if order is None:
        raise AppException(
            error_id=ErrorCode.ORDER_CANNOT_BE_REVIEWED,
            message="You can review only delivered products that you purchased",
            severity="warning",
            category=Category.CART,
            status_code=404
        )

    # Check review already exists
    existing_review_query = await db.execute(select(Review).where(Review.prod_id == product_id,Review.user_id == current_user.user_code))
    existing_review = existing_review_query.scalar_one_or_none()
    if existing_review:
        raise AppException(
            error_id=ErrorCode.REVIEW_ALREADY_EXISTS,
            message="You have already reviewed this product",
            severity="warning",
            category=Category.PRODUCT,
            status_code=409
        )

    # Add review
    review_id = await generate_unique_review_code(db)
    review = Review(
        review_id=review_id,
        prod_id=product_id,
        user_id=current_user.user_code,
        review_comment=reviews.review_comment,
        rating=reviews.rating
    )

    db.add(review)
    await db.commit()
    await db.refresh(review)

    return {
        "message": "Review added successfully",
        "review_id": review_id,
        "review_comment": review.review_comment
    }

@router.get("/getreview",response_model=list[GetReviewSchema],status_code=200)
async def get_reviews(product_id: str,current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)) -> list[GetReviewSchema]:
    product_query = await db.execute(select(Product).where(Product.prod_id == product_id))
    product = product_query.scalar_one_or_none()
    if product is None:
        raise AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product is not available from store",
            severity="warning",
            category=Category.PRODUCT,
            status_code=404
        )
    
    product_review_query = await db.execute(select(Review).where(Review.prod_id==product_id))
    product_review = product_review_query.scalars().all()

    if not product_review:
        raise AppException(
            error_id=ErrorCode.REVIEW_NOT_FOUND,
            message="Review is not found for this product",
            severity="warning",
            category=Category.REVIEW,
            status_code=409
        )

    return product_review
    
@router.patch("/updatereview",response_model=GetReviewSchema,status_code=201)
async def update_review(product_id: str,update_review: UpdateReview,current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)) -> GetReviewSchema:
    product_query = await db.execute(select(Product).where(Product.prod_id == product_id))
    product = product_query.scalar_one_or_none()
    if product is None:
        raise AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product is not available from store",
            severity="warning",
            category=Category.PRODUCT,
            status_code=404
        )
    
    product_review_query = await db.execute(select(Review).where(Review.prod_id==product_id,Review.user_id==current_user.user_code))
    product_review = product_review_query.scalar_one_or_none()

    if product_review is None:
        raise AppException(
            error_id=ErrorCode.REVIEW_NOT_FOUND,
            message="Review is not found for this product",
            severity="warning",
            category=Category.REVIEW,
            status_code=409
        )

    update_query = await db.execute(
        update(Review)
        .where(
            Review.prod_id==product_id,
            Review.user_id==current_user.user_code
        ).values(
            review_comment=update_review.review_comment,
            rating=update_review.rating
        )
    )
    await db.commit()

    final_product_review_query = await db.execute(select(Review).where(Review.prod_id==product_id,Review.user_id==current_user.user_code).execution_options(populate_existing=True))
    final_product_review = final_product_review_query.scalar_one_or_none()

    return final_product_review

@router.delete("/removereview/user",status_code=200)
async def delete_review_user(product_id: str,current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    product_query = await db.execute(select(Product).where(Product.prod_id == product_id))
    product = product_query.scalar_one_or_none()
    if product is None:
        raise AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product is not available from store",
            severity="warning",
            category=Category.PRODUCT,
            status_code=404
        )

    product_review_query = await db.execute(select(Review).where(Review.prod_id==product_id,Review.user_id==current_user.user_code))
    product_review = product_review_query.scalar_one_or_none()

    if product_review is None:
        raise AppException(
            error_id=ErrorCode.REVIEW_NOT_FOUND,
            message="User doesn't have review for this product",
            severity="warning",
            category=Category.REVIEW,
            status_code=409
        )

    await db.execute(delete(select(Review).where(Review.prod_id==product_id,Review.user_id==current_user.user_code)))
    return {
        "message": "Review deleted successfully"
    }

@router.delete("/removereview/admin",status_code=200)
async def delete_review_user(review_id: str,current_user: User = Depends(require_role(UserRole.admin)),db: AsyncSession = Depends(get_db)):
    product_review_query = await db.execute(select(Review).where(Review.review_id==review_id))
    product_review = product_review_query.scalar_one_or_none()

    if product_review is None:
        raise AppException(
            error_id=ErrorCode.REVIEW_NOT_FOUND,
            message="Invalid Review ID",
            severity="warning",
            category=Category.REVIEW,
            status_code=409
        )

    await db.execute(delete(Review).where(Review.review_id==review_id))
    return {
        "message": "Review deleted successfully"
    }

    

    