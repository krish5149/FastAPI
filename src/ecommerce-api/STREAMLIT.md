# Streamlit interface

The Streamlit interface is an independent client for the existing FastAPI service.
It does not import or modify the FastAPI application code.

## Run it

From the `e-commerce-api` project root:

```powershell
python -m pip install -r requirements-streamlit.txt
uvicorn app.main:app --reload
streamlit run app/streamlit_app.py
```

The UI opens at `http://localhost:8501` and connects to
`http://127.0.0.1:8000` by default. The API URL can be changed in the Streamlit
sidebar.

Visitors can browse products and sign up for a **customer** account. Signup
shows the generated user code when returned by the API. Sign in to use the
remaining pages. The role, email, and user code returned by `/auth/me` appear
under the FastAPI URL in the sidebar. Sign out removes the current login;
changing the API URL does too.

The sidebar uses **Browse / Account** tabs before login and **Shop / Manage**
tabs after login (customers see Shop only). Each tab has page buttons; the
active page is highlighted and stays selected when the app reruns.

The available tabs are role-based:

- **Customer:** products, cart (add/update/remove items or empty cart),
  checkout, order history/details/cancellation, and reviews (add/update/delete).
- **Seller:** customer features plus adding/deleting products, bulk product
  creation, and orders containing their products.
- **Admin:** seller features plus order status updates, user lookup/role/status
  updates, cart lookup, and review moderation.

All operations call the existing API routes; the API remains the authority for
permissions. The existing `/products/deleteproduct/{prod_id}` route has **no
server-side role check**, so showing it only to seller/admin accounts in this
UI is not access control. The admin user endpoints take a numeric `user_code`,
which is included in the `/user/users` list. Select users by email and code
when looking them up, updating role/status, or inspecting their cart; the
UUID is a separate identifier. If the running API is an older copy without
`user_code` in its response, the UI accepts a manually entered code instead
and warns that the API needs its updated schema. The existing order-cancellation route may
reject cancellation based on the order's status; the UI shows that response.
The review-delete handlers and the cancellation response schema were repaired
without changing their intended routes or permissions.
