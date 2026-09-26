"""Streamlit client for the existing ecommerce FastAPI routes."""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:8000"
TIMEOUT = 10
FETCH_ERROR = object()


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        super().__init__(f"{status_code}: {detail}")


class ApiClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        json_data: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            data=data,
            json=json_data,
            params=params,
            timeout=TIMEOUT,
        )
        if not response.ok:
            try:
                body = response.json()
            except ValueError:
                body = response.text
            detail = body
            if isinstance(body, dict):
                detail = body.get("message") or body.get("detail") or body
            raise ApiError(response.status_code, str(detail))
        return response.json() if response.content else None


def resource(value: Any) -> str:
    return quote(str(value), safe="")


def load(
    api: ApiClient, path: str, *, empty_statuses: tuple[int, ...] = (),
    params: dict[str, Any] | None = None,
) -> Any:
    try:
        return api.request("GET", path, params=params)
    except ApiError as exc:
        if exc.status_code in empty_statuses:
            return None
        st.error(str(exc))
    except requests.RequestException as exc:
        st.error(f"Cannot connect to FastAPI: {exc}")
    return FETCH_ERROR


def flash_and_rerun(message: str) -> None:
    st.session_state["notice"] = message
    st.rerun()


def action(
    api: ApiClient, method: str, path: str, message: str, *,
    json_data: Any = None, params: dict[str, Any] | None = None,
) -> None:
    try:
        api.request(method, path, json_data=json_data, params=params)
    except (ApiError, requests.RequestException) as exc:
        st.error(str(exc))
        return
    flash_and_rerun(message)


def product_choice(product: dict[str, Any]) -> str:
    return f"{product.get('name', 'Product')} ({product.get('prod_id', '')})"


def signin(api: ApiClient) -> None:
    st.subheader("Sign in")
    with st.form("signin"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if not submitted:
        return
    if not email or not password:
        st.warning("Enter both your email and password.")
        return
    try:
        response = api.request(
            "POST", "/auth/login",
            data={"username": email, "password": password},
        )
        st.session_state["token"] = response["access_token"]
        flash_and_rerun("Signed in.")
    except (ApiError, requests.RequestException, KeyError) as exc:
        st.error(f"Sign in failed: {exc}")


def signup(api: ApiClient) -> None:
    st.subheader("Create customer account")
    with st.form("signup"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Sign up", type="primary")
    if not submitted:
        return
    if not email or len(password) < 8:
        st.warning("Enter an email and a password of at least 8 characters.")
    elif password != confirm:
        st.warning("Passwords do not match.")
    else:
        try:
            created = api.request(
                "POST", "/auth/signup",
                json_data={"email": email, "password": password},
            )
        except (ApiError, requests.RequestException) as exc:
            st.error(f"Sign up failed: {exc}")
            return
        code = created.get("user_code")
        message = "Account created. Sign in with your new credentials."
        if code is not None:
            message = f"Account created with user code {code}. Sign in with your email."
        flash_and_rerun(message)


def products_page(api: ApiClient) -> None:
    st.subheader("Products")
    products = load(api, "/products/getproducts")
    if products is FETCH_ERROR:
        return
    if products:
        st.dataframe(products, use_container_width=True, hide_index=True)
    else:
        st.info("No products available.")
    with st.form("find_product"):
        product_id = st.text_input("Find product by ID")
        submitted = st.form_submit_button("Find product")
    if submitted:
        if not product_id.strip():
            st.warning("Enter a product ID.")
        else:
            product = load(api, f"/products/getproduct/{resource(product_id.strip())}")
            if product is not FETCH_ERROR and product is not None:
                st.json(product)


def cart_page(api: ApiClient) -> None:
    st.subheader("My cart")
    products = load(api, "/products/getproducts")
    if products is FETCH_ERROR:
        return
    if products:
        with st.form("add_item"):
            product = st.selectbox("Product", products, format_func=product_choice)
            quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
            submitted = st.form_submit_button("Add to cart", type="primary")
        if submitted:
            action(
                api, "POST", "/cart/additems", "Added to cart.",
                json_data={"product_id": product["prod_id"], "quantity": int(quantity)},
            )

    cart = load(api, "/cart/getmycart", empty_statuses=(409,))
    if cart is FETCH_ERROR:
        return
    if not cart or not cart.get("items"):
        st.info("Your cart is empty.")
        return
    st.caption(f"{cart['total_items']} line item(s)")
    for item in cart["items"]:
        product_id = item["prod_id"]
        with st.expander(f"{item['name']} - quantity {item['quantity']}"):
            with st.form(f"item_{product_id}"):
                quantity = st.number_input(
                    "Quantity", min_value=1, value=int(item["quantity"]), step=1,
                    key=f"quantity_{product_id}",
                )
                update = st.form_submit_button("Update quantity")
                remove = st.form_submit_button("Remove item")
            if update:
                action(
                    api, "PATCH", "/cart/items/", "Quantity updated.",
                    params={"product_id": product_id, "quantity": int(quantity)},
                )
            if remove:
                action(
                    api, "DELETE",
                    f"/cart/removecartproduct/{resource(product_id)}",
                    "Item removed from cart.",
                )

    st.divider()
    confirm_clear = st.checkbox("I want to empty my entire cart")
    if st.button("Empty cart", disabled=not confirm_clear):
        action(api, "DELETE", "/cart/removecart", "Cart emptied.")

    if st.button("Place order", type="primary"):
        try:
            result = api.request("POST", "/oders/checkout")
        except (ApiError, requests.RequestException) as exc:
            st.error(f"Checkout failed: {exc}")
            return
        if result.get("order"):
            st.success(f"Order {result['order']['order_id']} placed.")
        else:
            st.warning("No items could be ordered.")
        if result.get("skipped_items"):
            st.warning("Some items were skipped:")
            st.dataframe(result["skipped_items"], use_container_width=True)


def orders_page(api: ApiClient) -> None:
    st.subheader("My order history")
    orders = load(api, "/oders/getmyorders", empty_statuses=(404,))
    if orders is FETCH_ERROR:
        return
    if orders is None:
        st.info("No orders found.")
        return
    for order in orders:
        order_id = order["order_id"]
        with st.expander(f"{order_id} - {order['status']}"):
            st.write(f"Created: {order.get('created_at', 'Unknown')}")
            st.dataframe(order.get("items", []), use_container_width=True, hide_index=True)
            if st.button("View order items", key=f"details_{order_id}"):
                details = load(api, f"/oders/{resource(order_id)}")
                if details is not FETCH_ERROR and details is not None:
                    st.dataframe(details, use_container_width=True, hide_index=True)
            confirm = st.checkbox("Confirm cancellation", key=f"confirm_{order_id}")
            if st.button("Cancel order", key=f"cancel_{order_id}", disabled=not confirm):
                action(
                    api, "POST", f"/oders/{resource(order_id)}/cancel",
                    f"Cancellation requested for {order_id}.",
                )


def reviews_page(api: ApiClient, role: str) -> None:
    st.subheader("Reviews")
    products = load(api, "/products/getproducts")
    if products is FETCH_ERROR:
        return
    if not products:
        return
    product = st.selectbox("Product", products, format_func=product_choice)
    product_id = product["prod_id"]
    reviews = load(
        api, "/review/getreview",
        params={"product_id": product_id}, empty_statuses=(409,),
    )
    if reviews is FETCH_ERROR:
        st.caption("Reviews could not be loaded.")
    elif reviews:
        st.dataframe(reviews, use_container_width=True, hide_index=True)
    elif reviews is None:
        st.info("No reviews for this product yet.")

    with st.form("add_review"):
        rating = st.slider("Rating", 1, 5, 5)
        comment = st.text_area("Review")
        submitted = st.form_submit_button("Add review")
    if submitted:
        action(
            api, "POST", "/review/addreview", "Review added.",
            params={"product_id": product_id},
            json_data={"rating": rating, "review_comment": comment},
        )
    with st.form("update_review"):
        rating = st.slider("Updated rating", 1, 5, 5)
        comment = st.text_area("Updated review")
        submitted = st.form_submit_button("Update my review")
    if submitted:
        action(
            api, "PATCH", "/review/updatereview", "Review updated.",
            params={"product_id": product_id},
            json_data={"rating": rating, "review_comment": comment},
        )

    confirm = st.checkbox("Confirm removal of my review")
    if st.button("Delete my review", disabled=not confirm):
        action(
            api, "DELETE", "/review/removereview/user",
            "Your review was deleted.", params={"product_id": product_id},
        )

    if role == "admin":
        st.divider()
        with st.form("moderate_review"):
            review_id = st.text_input("Review ID to remove")
            submitted = st.form_submit_button("Delete review as admin")
        if submitted:
            if review_id.strip():
                action(
                    api, "DELETE", "/review/removereview/admin",
                    "Review deleted.",
                    params={"review_id": review_id.strip()},
                )
            else:
                st.warning("Enter a review ID.")


def manage_products_page(api: ApiClient) -> None:
    st.subheader("Manage products")
    with st.form("new_product"):
        name = st.text_input("Name")
        description = st.text_area("Description")
        price = st.number_input("Price", min_value=0, step=1)
        submitted = st.form_submit_button("Add product", type="primary")
    if submitted:
        if not name.strip():
            st.warning("Enter a product name.")
        else:
            action(
                api, "POST", "/products/addproduct", "Product added.",
                json_data={
                    "name": name.strip(), "description": description,
                    "price": int(price),
                },
            )
    with st.expander("Bulk add products"):
        with st.form("bulk_products"):
            raw = st.text_area(
                "Products JSON array",
                value='[{"name": "Example", "description": "Description", "price": 10}]',
            )
            submitted = st.form_submit_button("Bulk add")
        if submitted:
            try:
                items = json.loads(raw)
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON: {exc}")
            else:
                if not isinstance(items, list) or not items or any(
                    not isinstance(item, dict) for item in items
                ):
                    st.warning("Provide a non-empty JSON array of products.")
                else:
                    action(
                        api, "POST", "/products/bulkaddproducts",
                        "Products added.", json_data=items,
                    )
    products = load(api, "/products/getproducts")
    if products is FETCH_ERROR or not products:
        return
    with st.form("delete_product"):
        product = st.selectbox(
            "Product to delete", products, format_func=product_choice,
        )
        confirmed = st.checkbox("Confirm product deletion")
        submitted = st.form_submit_button("Delete product")
    if submitted:
        if confirmed:
            action(
                api, "DELETE",
                f"/products/deleteproduct/{resource(product['prod_id'])}",
                "Product deleted.",
            )
        else:
            st.warning("Confirm deletion first.")


def seller_orders_page(api: ApiClient) -> None:
    st.subheader("Orders containing my products")
    orders = load(api, "/oders/seller/products", empty_statuses=(409,))
    if orders is FETCH_ERROR:
        return
    if not orders:
        st.info("No seller orders found.")
        return
    for order in orders:
        with st.expander(f"{order['order_id']} - {order['status']}"):
            st.write(f"Created: {order.get('created_at', 'Unknown')}")
            st.dataframe(order.get("items", []), use_container_width=True, hide_index=True)


def admin_orders_page(api: ApiClient) -> None:
    st.subheader("Manage order status")
    with st.form("order_status"):
        order_id = st.text_input("Order ID")
        status = st.selectbox(
            "Status", ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"]
        )
        submitted = st.form_submit_button("Update status")
    if submitted:
        if order_id.strip():
            action(
                api, "PATCH", f"/oders/{resource(order_id.strip())}/status",
                "Order status updated.", json_data={"status": status},
            )
        else:
            st.warning("Enter an order ID.")


def user_code_input(users: list[dict[str, Any]], label: str) -> int | None:
    if all(isinstance(user.get("user_code"), int) for user in users):
        user = st.selectbox(
            label, users,
            format_func=lambda entry: f"{entry['email']} (code {entry['user_code']})",
        )
        return user["user_code"]
    code = st.text_input(label, help="Enter the user's numeric code, not their UUID.")
    return int(code.strip()) if code.strip().isdecimal() and int(code.strip()) > 0 else None


def admin_users_page(api: ApiClient) -> None:
    st.subheader("Manage users")
    users = load(api, "/user/users")
    if users is FETCH_ERROR:
        return
    if not users:
        st.info("No users found.")
        return
    st.dataframe(users, use_container_width=True, hide_index=True)
    if any("user_code" not in user for user in users):
        st.warning(
            "This API's /user/users response does not include user_code. "
            "Enter a known user code below, or run the API version whose "
            "UserResponse schema includes user_code. A UUID cannot be used here."
        )
    with st.form("user_lookup"):
        code = user_code_input(users, "User code to find")
        lookup = st.form_submit_button("Find user")
    if lookup:
        if code is None:
            st.warning("Enter a valid numeric user code.")
        else:
            found = load(api, f"/user/users/{code}")
            if found is not FETCH_ERROR and found is not None:
                st.json(found)
    with st.form("change_role"):
        code = user_code_input(users, "User code for role")
        role = st.selectbox("New role", ["customer", "seller", "admin"])
        submitted = st.form_submit_button("Update role")
    if submitted:
        if code is None:
            st.warning("Enter a valid numeric user code.")
        else:
            action(
                api, "PATCH", f"/user/users/{code}/role",
                "User role updated.", json_data={"role": role},
            )
    with st.form("change_status"):
        code = user_code_input(users, "User code for status")
        active = st.checkbox("Active", value=True)
        submitted = st.form_submit_button("Update active status")
    if submitted:
        if code is None:
            st.warning("Enter a valid numeric user code.")
        else:
            action(
                api, "PATCH", f"/user/users/{code}/status",
                "User status updated.", json_data={"is_active": active},
            )


def admin_carts_page(api: ApiClient) -> None:
    st.subheader("Inspect carts")
    with st.form("cart_by_id"):
        cart_id = st.text_input("Cart ID")
        submitted = st.form_submit_button("Find cart")
    if submitted:
        if cart_id.strip():
            cart = load(api, f"/cart/getcart/{resource(cart_id.strip())}")
            if cart is not FETCH_ERROR and cart is not None:
                st.dataframe(cart, use_container_width=True, hide_index=True)
        else:
            st.warning("Enter a cart ID.")
    users = load(api, "/user/users")
    if users is FETCH_ERROR:
        return
    if users:
        with st.form("cart_by_user"):
            code = user_code_input(users, "User code for cart")
            submitted = st.form_submit_button("Find user's cart")
        if submitted:
            if code is None:
                st.warning("Enter a valid numeric user code.")
            else:
                cart = load(api, f"/cart/getcart/user/{code}")
                if cart is not FETCH_ERROR and cart is not None:
                    st.json(cart)


def sidebar_page(groups: dict[str, list[str]]) -> str:
    allowed = [page for pages in groups.values() for page in pages]
    if st.session_state.get("sidebar_page") not in allowed:
        st.session_state["sidebar_page"] = allowed[0]
    selected = st.session_state["sidebar_page"]
    active_group = next(group for group, pages in groups.items() if selected in pages)
    tabs = st.sidebar.tabs(list(groups), default=active_group)
    for tab, pages in zip(tabs, groups.values()):
        with tab:
            for page in pages:
                if st.button(
                    page,
                    key=f"nav_{page}",
                    type="primary" if page == selected else "secondary",
                    width="stretch",
                ):
                    st.session_state["sidebar_page"] = page
                    st.rerun()
    return selected


def main() -> None:
    st.set_page_config(page_title="Ecommerce", page_icon="🛒", layout="wide")
    st.title("Ecommerce")
    st.caption("Shopping and management through the existing FastAPI endpoints")
    api_url = st.sidebar.text_input("FastAPI URL", value=DEFAULT_API_URL).rstrip("/")
    if st.session_state.get("last_api_url", api_url) != api_url:
        st.session_state.pop("token", None)
        st.session_state.pop("sidebar_page", None)
    st.session_state["last_api_url"] = api_url
    notice = st.session_state.pop("notice", None)
    if notice:
        st.success(notice)
    token = st.session_state.get("token")
    api = ApiClient(api_url, token)
    if not token:
        st.sidebar.info("Not signed in - sign up as a customer or sign in.")
        page = sidebar_page(
            {"Browse": ["Products"], "Account": ["Sign in", "Sign up"]}
        )
        {"Products": products_page, "Sign in": signin, "Sign up": signup}[page](api)
        return

    profile = load(api, "/auth/me")
    if profile is FETCH_ERROR or profile is None:
        st.sidebar.error("Session could not be verified.")
        if st.sidebar.button("Clear session"):
            st.session_state.pop("token", None)
            st.rerun()
        return
    role = profile.get("role")
    if role not in ("customer", "seller", "admin"):
        st.error(f"Unknown account role: {role!r}")
        return
    st.sidebar.success(f"Signed in as {role.title()}")
    st.sidebar.caption(profile.get("email", ""))
    if profile.get("user_code") is not None:
        st.sidebar.caption(f"User code: {profile['user_code']}")
    if st.sidebar.button("Sign out"):
        st.session_state.pop("token", None)
        st.session_state.pop("sidebar_page", None)
        st.rerun()

    pages = {
        "Products": lambda: products_page(api),
        "My cart": lambda: cart_page(api),
        "My orders": lambda: orders_page(api),
        "Reviews": lambda: reviews_page(api, role),
    }
    if role in ("seller", "admin"):
        pages["Manage products"] = lambda: manage_products_page(api)
        pages["Seller orders"] = lambda: seller_orders_page(api)
    if role == "admin":
        pages["Manage orders"] = lambda: admin_orders_page(api)
        pages["Manage users"] = lambda: admin_users_page(api)
        pages["Inspect carts"] = lambda: admin_carts_page(api)
    groups = {"Shop": ["Products", "My cart", "My orders", "Reviews"]}
    if role in ("seller", "admin"):
        groups["Manage"] = ["Manage products", "Seller orders"]
    if role == "admin":
        groups["Manage"].extend(["Manage orders", "Manage users", "Inspect carts"])
    page = sidebar_page(groups)
    pages[page]()


if __name__ == "__main__":
    main()
