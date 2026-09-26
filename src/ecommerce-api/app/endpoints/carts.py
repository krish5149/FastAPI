from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User, UserRole
from ..database import get_db
from ..core.dependencies import require_role
from ..schemas.CartSchema import *
from ..models.cart import Cart, CartItem
from ..models.product import Product
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from ..core.idgenerator import generate_unique_cart_code
from ..core.ExceptionHandler import AppException
from ..core.error_codes import *
from ..core.dependencies import *

router = APIRouter(prefix="/cart",tags=["cart"])

@router.post("/additems",response_model=CartResponse,status_code=status.HTTP_201_CREATED)
async def add_item(cart_item: CartCreate,current_user: User = Depends(require_role(UserRole.customer,UserRole.admin,UserRole.seller)),db: AsyncSession = Depends(get_db)) -> CartResponse:
    query1 = select(Cart.cart_id).where(Cart.user_id==current_user.user_code)
    check_exists_prod_execute = await db.execute(query1)
    cart_id_db = check_exists_prod_execute.scalar_one_or_none()
    product = await db.execute(select(Product).where(Product.prod_id==cart_item.product_id))
    product = product.scalar_one_or_none()
    if product is None:
        raise AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message=f"{cart_item.product_id} is Invalid",
            severity="warning",
            category=Category.CART,
            status_code=404
        )

    quantity = 1
    if cart_item.quantity:
        quantity = cart_item.quantity
    if cart_id_db is not None:
        user_items = await db.execute(select(CartItem).where(CartItem.prod_id==cart_item.product_id,CartItem.cart_id==cart_id_db))
        existing_item = user_items.scalar_one_or_none()
        if existing_item is not None:
            update_query = update(CartItem).where(
                CartItem.prod_id==cart_item.product_id,
                CartItem.cart_id==cart_id_db
            ).values(quantity=existing_item.quantity+quantity)
            await db.execute(update_query)
            await db.commit()
            await db.refresh(existing_item)
            return existing_item
        else:
            add_items = CartItem(cart_id=cart_id_db,prod_id=cart_item.product_id,quantity=quantity,name=product.name)
            db.add(add_items)
            await db.commit()
            await db.refresh(add_items)
            return add_items
        
    else:
        # creating id and add into cart table
        cart_code = await generate_unique_cart_code(db)
        cart = Cart(cart_id=cart_code,user_id=current_user.user_code)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

        # adding into cartitem table
        add_item = CartItem(cart_id=cart_code,prod_id=cart_item.product_id,quantity=quantity,name=product.name)
        db.add(add_item)
        await db.commit()
        await db.refresh(add_item)
        return add_item

@router.get("/getcart/{cart_id}",status_code=200,response_model=list[CartResponse])
async def get_cart_by_id(cart_id: str,db: AsyncSession = Depends(get_db),current_user: User = Depends(require_role(UserRole.admin))) -> list[CartResponse]:
    get_cart_query = select(CartItem).where(CartItem.cart_id==cart_id)
    cart_items = await db.execute(get_cart_query)
    items = cart_items.scalars().all()
    if not items:
        AppException(
            error_id=ErrorCode.CART_NOT_FOUND,
            message="Particular cart is not available",
            severity="warning",
            category=Category.CART
        )
    
    return items

@router.get("/getcart/user/{user_id}",response_model=GetCartResponse,status_code=200)
async def get_cart_by_user(user_id: str,current_user: User = Depends(require_role(UserRole.admin)),db: AsyncSession = Depends(get_db)):
    get_carts_query = select(Cart).where(Cart.user_id==user_id).options(selectinload(Cart.items))
    cart_items_list_by_userid = await db.execute(get_carts_query)
    final_result = cart_items_list_by_userid.scalar_one_or_none()
    if final_result is None:
        raise AppException(
            error_id=ErrorCode.CART_NOT_FOUND,
            message="User doesn't have cart yet",
            severity="warning",
            category=Category.CART,
            status_code=409
        )
    
    return GetCartResponse(
        cart_id=final_result.cart_id,
        user_id=final_result.user_id,
        total_items=len(final_result.items),
        items=final_result.items
    )

@router.delete("/removecartproduct/{product_id}",status_code=200)
async def remove_product_cart(product_id: str,current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    user_cart_id_query = select(Cart).where(Cart.user_id==current_user.user_code)
    user_cart_id = await db.execute(user_cart_id_query)
    user_cart_id_value = user_cart_id.scalar_one_or_none()

    if user_cart_id_value is None:
        raise AppException(
            error_id=ErrorCode.CART_NOT_FOUND,
            message="User doesn't have cart yet",
            severity="warning",
            category=Category.CART,
            status_code=409
        )

    
    query_get_product = delete(CartItem).where(CartItem.cart_id==user_cart_id_value.cart_id,CartItem.prod_id==product_id)
    delete_result  = await db.execute(query_get_product)
    if delete_result.rowcount==0:
        raise AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message="Product doesn't exists",
            severity="warning",
            category=Category.CART,
            status_code=409
         ) 
    await db.commit()
    return {"message": "Product deleted successfully from your cart"}

@router.get("/getmycart",response_model=GetCartResponse,status_code=200)
async def get_my_cart(current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    get_carts_query = select(Cart).where(Cart.user_id==current_user.user_code).options(selectinload(Cart.items))
    cart_items_list_by_userid = await db.execute(get_carts_query)
    final_result = cart_items_list_by_userid.scalar_one_or_none()
    if final_result is None:
        raise AppException(
            error_id=ErrorCode.CART_NOT_FOUND,
            message="User doesn't have cart yet add a product to create one",
            severity="warning",
            category=Category.CART,
            status_code=409
        )
    
    return GetCartResponse(
        cart_id=final_result.cart_id,
        user_id=final_result.user_id,
        total_items=len(final_result.items),
        items=final_result.items,
    )

@router.patch("/items/",response_model=CartResponse,status_code=200)
async def update_quantity(product_id: str,quantity: int,current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)) -> CartResponse:
    get_carts_query = select(Cart).where(Cart.user_id==current_user.user_code).options(selectinload(Cart.items))
    cart_items_list_by_userid = await db.execute(get_carts_query)
    final_result = cart_items_list_by_userid.scalar_one_or_none()
    if final_result is None:
        raise AppException(
        error_id=ErrorCode.CART_NOT_FOUND,
        message="User doesn't have cart yet add a product to create one",
        severity="warning",
        category=Category.CART,
        status_code=409
    )

    check_prod_in_cart = await db.execute(select(CartItem.prod_id).where(CartItem.cart_id==final_result.cart_id,CartItem.prod_id==product_id))
    check_prod_in_cart = check_prod_in_cart.scalar_one_or_none()
    if check_prod_in_cart is None:
        raise AppException(
            error_id=ErrorCode.PRODUCT_NOT_FOUND,
            message="User don't have this product in cart",
            severity="warning",
            category=Category.CART,
            status_code=409
        )           

    if final_result.user_id != current_user.user_code:
        raise AppException(
            error_id=ErrorCode.PERMISSION_DENIED,
            message="User don't wont this cart",
            severity="warning",
            category=Category.CART,
            status_code=409
        )

    if quantity <= 0:
        raise AppException(
            error_id=ErrorCode.INVALID_QUANTITY,
            message="Quantity must be greater than 0",
            severity="warning",
            category=Category.CART,
            status_code=400,
        )
            
    query_to_update_quantity = update(CartItem).where(CartItem.cart_id==final_result.cart_id,CartItem.prod_id==product_id).values(quantity=quantity)
    await db.execute(query_to_update_quantity)
    await db.commit()

    final_item_query = select(CartItem).where(CartItem.cart_id == final_result.cart_id, CartItem.prod_id == product_id)
    final_result = await db.execute(final_item_query)
    return final_result.scalar_one_or_none()

@router.delete("/removecart",status_code=200)
async def remove_product_cart(current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    user_cart_id_query = select(Cart).where(Cart.user_id==current_user.user_code)
    user_cart_id = await db.execute(user_cart_id_query)
    user_cart_id_value = user_cart_id.scalar_one_or_none()

    if user_cart_id_value is None:
        raise AppException(
            error_id=ErrorCode.CART_NOT_FOUND,
            message="User doesn't have cart yet",
            severity="warning",
            category=Category.CART,
            status_code=409
        )
    
    await db.execute(delete(CartItem).where(CartItem.cart_id==user_cart_id_value.cart_id))
    await db.execute(delete(Cart).where(Cart.cart_id==user_cart_id_value.cart_id))
    await db.commit()
    return {"message": "Cart deleted successfully"}