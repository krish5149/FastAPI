from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.dependencies import require_role
from sqlalchemy import select, update, delete, func
from ..core.ExceptionHandler import AppException
from ..models.user import User, UserRole
from ..core.error_codes import *
from ..core.dependencies import *
from ..core.idgenerator import generate_unique_order_code
from ..models.cart import Cart, CartItem
from ..schemas.OrderSchema import *
from ..models.product import Product
from sqlalchemy.orm import selectinload
from ..models.order import Order, OrderItems

router = APIRouter(prefix="/oders",tags=["orders"])

@router.post("/checkout",status_code=201)
async def checkout(current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    user_cart = await db.execute(select(Cart).where(Cart.user_id==current_user.user_code).options(selectinload(Cart.items)))
    exc_user_cart = user_cart.scalar_one_or_none()
    if exc_user_cart is None:
        raise AppException(
            error_id=ErrorCode.CART_NOT_FOUND,
            message="User doesn't have cart yet",
            severity="warning",
            category=Category.CART,
            status_code=409
        )

    skipped_items = []
    total_price = 0
    ordered_items = []
    for cart_item in exc_user_cart.items:
        product = await db.execute(select(Product).where(Product.prod_id==cart_item.prod_id))
        product = product.scalar_one_or_none()
        if product is None:
            skipped_items.append({
                "prod_id": cart_item.prod_id,
                "name": cart_item.name,
                "requested_quantity":cart_item.quantity,
                "message_id": ErrorCode.PRODUCT_NOT_FOUND,
                "reason": "Product doest not available",
                "removed_from_cart": True
            })
            continue

        product_quantity = product.base_quantity
        if cart_item.quantity > product_quantity:
            skipped_items.append({
                "prod_id": cart_item.prod_id,
                "name": cart_item.name,
                "requested_quantity":cart_item.quantity,
                "message_id": ErrorCode.PRODUCT_NOT_FOUND,
                "reason": f"Currently {product_quantity} available",
                "removed_from_cart": False
            })
            continue
        
        ordered_items.append({
            "prod_id":cart_item.prod_id,
            "quantity":cart_item.quantity,
            "name":product.name,
            "price":cart_item.quantity*product.price
        })

        total_price += (cart_item.quantity*product.price)

        # updating product qunatity 
        new_stock = product.base_quantity-cart_item.quantity
        await db.execute(update(Product).where(Product.prod_id==cart_item.prod_id).values(base_quantity = new_stock))

        # delete the product in table
        await db.execute(delete(CartItem).where(CartItem.prod_id==product.prod_id,CartItem.cart_id==cart_item.cart_id))
        await db.commit()

        # delete the product item not available in cartitem
        items_in_cartitem = await db.execute(select(CartItem).where(CartItem.cart_id==cart_item.cart_id))
        if items_in_cartitem.first() is None:
            await db.execute(delete(Cart).where(Cart.cart_id==cart_item.cart_id))
            await db.commit()

    if not ordered_items:
        return {
            "order": None,
            "skipped_items": skipped_items,
        }

    # create a new order and add it to table
    order_id = await generate_unique_order_code(db)
    new_order = Order(order_id=order_id,user_id=current_user.user_code,status="PENDING",total=0)
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    order_items_objs = [OrderItems(order_id=order_id, **item) for item in ordered_items]
    db.add_all(order_items_objs)
    await db.commit()

    return CheckOutResponse(
        order = OrderResponse(
            order_id=order_id,
            status=new_order.status,
            total_item=len(order_items_objs),
            total_price=total_price,
            items=order_items_objs
        ),
        skipped_items = skipped_items
    ) 

@router.get("/getmyorders", response_model=list[Order_Response], status_code=200)
async def get_my_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[Order_Response]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.user_code)
        .options(selectinload(Order.items))
    )
    orders = result.scalars().all()

    if not orders:
        raise AppException(
            error_id=ErrorCode.ORDER_NOT_FOUND,
            message="No orders found for this user",
            severity="warning",
            category=Category.ORDER,
            status_code=404,
        )

    return orders

@router.get("/{order_id}",response_model=list[OrderOutResponse],status_code=200)
async def get_order(order_id: str,current_user: User = Depends(get_current_user),db: AsyncSession = Depends(get_db)) -> list[OrderOutResponse]:
    exc_order_id = await db.execute(select(OrderItems).where(OrderItems.order_id==order_id))
    items = exc_order_id.scalars().all()
    if len(items) <= 0:
        raise AppException(
            error_id=ErrorCode.ORDER_NOT_FOUND,
            message="There is no order for this ID",
            severity="warning",
            category=Category.ORDER,
            status_code=409
        )

    return items

@router.patch("/{order_id}/status",response_model=Order_Response,status_code=200)
async def update_order_status(order_id: str,status_data: UpdateStatus,current_user: User = Depends(require_role(UserRole.admin)),db: AsyncSession = Depends(get_db)) -> Order_Response:

    result = await db.execute(select(Order).where(Order.order_id == order_id).options(selectinload(Order.items)))
    order = result.scalar_one_or_none()

    if order is None:
        raise AppException(
            error_id=ErrorCode.ORDER_NOT_FOUND,
            message="There is no order for this ID",
            severity="warning",
            category=Category.ORDER,
            status_code=404
        )

    await db.execute(update(Order).where(Order.order_id == order_id).values(status=status_data.status))
    await db.commit()

    result = await db.execute(select(Order).where(Order.order_id == order_id).options(selectinload(Order.items)))
    order = result.scalar_one()
    return order

@router.post("/{order_id}/cancel",status_code=200)
async def cancel_order(order_id: str,current_user: User = Depends(require_role(UserRole.admin,UserRole.seller,UserRole.customer)),db: AsyncSession = Depends(get_db)):     
    result = await db.execute(select(Order).where(Order.user_id == current_user.user_code,Order.order_id==order_id))
    orders = result.scalar_one_or_none()
    if orders is None:
        raise AppException(
            error_id=ErrorCode.ORDER_NOT_FOUND,
            message="No orders found for this user",
            severity="warning",
            category=Category.ORDER,
            status_code=404,
        )

    # Customers can cancel only their own order
    if (current_user.role == UserRole.customer and Order.user_id != current_user.user_code):
        raise AppException(
            error_id=ErrorCode.ORDER_NOT_FOUND,
            message="There is no order for this user",
            severity="warning",
            category=Category.ORDER,
            status_code=404,
        )

    if orders.status == "SHIPPING":
        raise AppException(
                error_id=ErrorCode.ORDER_CANNOT_BE_CANCELLED,
                message=f"Cannot cancel an order with status {orders.status}",
                severity="warning",
                category=Category.ORDER,
                status_code=409,
            )

    if orders.status == "CANCELLED":
        raise AppException(
                error_id=ErrorCode.ORDER_CANNOT_BE_CANCELLED,
                message=f"Cannot cancel because this order is already {orders.status}",
                severity="warning",
                category=Category.ORDER,
                status_code=409,
            )
    
    await db.execute(update(Order).where(Order.order_id==order_id).values(status="CANCELLED"))
    await db.commit()

    result = await db.execute(select(Order).where(Order.order_id==order_id).options(selectinload(Order.items)))
    return_result = result.scalar_one_or_none()
    return return_result
    

@router.get("/seller/products",response_model=list[SellerOrderResponse],status_code=200)
async def seller_product(current_user: User = Depends(require_role(UserRole.admin,UserRole.seller)),db: AsyncSession = Depends(get_db)) -> list[SellerOrderResponse]:
    result = await db.execute(
        select(Order,OrderItems)
        .join(OrderItems,OrderItems.order_id==Order.order_id)
        .join(Product,Product.prod_id==OrderItems.prod_id)
        .where(Product.user_code==current_user.user_code)
    )

    row = result.all()
    if not row:
        raise AppException(
            error_id=ErrorCode.ORDER_NOT_FOUND,
            message=f"There is no order for the product",
            severity="warning",
            category=Category.ORDER,
            status_code=409,
        )

    orders_dict = {}
    for orders,order_items in row:
        if orders.order_id not in orders_dict:
            orders_dict[orders.order_id] = {
                "order_id":orders.order_id,
                "status":orders.status,
                "created_at":orders.created_at,
                "items":[]
            }

        orders_dict[orders.order_id]["items"].append({
            "prod_id": order_items.prod_id,
            "name": order_items.name,
            "quantity": order_items.quantity,
            "price": order_items.price
        })

    return list(orders_dict.values())
