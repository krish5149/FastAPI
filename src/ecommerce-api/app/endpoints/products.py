from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..core.dependencies import require_role
from ..schemas.ProductSchema import *
from ..models.user import User, UserRole
from sqlalchemy import select
from ..core.idgenerator import generate_unique_product_code
from ..models.product import Product
from ..core.ExceptionHandler import AppException
from ..core.error_codes import *

router = APIRouter(prefix="/products",tags=["products"])

@router.post("/addproduct",response_model=ProductResonse,status_code=status.HTTP_201_CREATED)
async def add_products(product: CreateProduct,current_user: User = Depends(require_role(UserRole.admin,UserRole.seller)),db: AsyncSession = Depends(get_db)) -> ProductResonse:
    id = await generate_unique_product_code(db)
    db_product = Product(
        user_code=current_user.user_code,
        prod_id=id,
        name=product.name,
        description=product.description,
        price=product.price
    )

    db.add(db_product)
    await db.commit()
    return db_product

@router.post("/bulkaddproducts",response_model=list[ProductResonse],status_code=status.HTTP_201_CREATED)
async def bulk_add_products(products: list[CreateProduct],current_user: User = Depends(require_role(UserRole.admin,UserRole.seller)),db: AsyncSession = Depends(get_db)) ->list[ProductResonse]:
    db_products = []
    for product in products:
        id = await generate_unique_product_code(db)
        db_product = Product(
            user_code=current_user.user_code,
            prod_id=id,
            name=product.name,
            description=product.description,
            price=product.price
        )

        db_products.append(db_product)
    
    db.add_all(db_products)
    await db.commit()
    return db_products

@router.get("/getproducts",response_model=list[ProductResonse],status_code=200)
async def get_products(db: AsyncSession = Depends(get_db)) -> list[ProductResonse]:
    query = select(Product)
    products = await db.execute(query)
    products_list = products.scalars().all()
    return products_list

@router.get("/getproduct/{prod_id}",response_model=ProductResonse,status_code=200)
async def get_product(prod_id: str,db: AsyncSession = Depends(get_db)) -> ProductResonse:
    query = select(Product).where(Product.prod_id==prod_id)
    products = await db.execute(query)
    product = products.scalar_one_or_none()
    if product is None:
        raise AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product is not Listed",
            severity="warning",
            category=Category.CART,
            status_code=409
        )
    return product

@router.delete("/deleteproduct/{prod_id}",status_code=200)
async def delete_product(prod_id: str,db: AsyncSession = Depends(get_db)):
    query = select(Product).where(Product.prod_id==prod_id)
    products = await db.execute(query)
    product = products.scalar_one_or_none()
    if product is None:
        AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product is not found in the store",
            severity="warning",
            category=Category.PRODUCT,
            statsu_code=409
        )

    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}