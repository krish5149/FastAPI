# Ecommerce API

An ecommerce project with a **FastAPI** backend, **SQLite** database, and a separate **Streamlit** web interface. The UI calls the API over HTTP; authentication and role checks belong to the API.

## Features

| Role | Available in the Streamlit UI |
| --- | --- |
| Visitor | Browse products, create a customer account, sign in |
| Customer | Manage a cart, check out, view orders, request cancellation, add/update/delete reviews |
| Seller | Customer features, add/bulk-add/delete products, view orders containing their products |
| Admin | Seller features, change order status, manage user roles and active status, inspect carts, moderate reviews |

New accounts have the **customer** role. The UI shows the signed-in role, email, and user code in its sidebar. A user's UUID and numeric `user_code` are different identifiers; the admin user and cart routes use `user_code`.

## Requirements

- Python 3.10 or newer
- A terminal with access to `python` (the examples below use PowerShell)

From the `ecommerce-api` directory, create and activate an environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the API's Python dependencies and the UI dependencies:

```powershell
python -m pip install fastapi uvicorn sqlalchemy aiosqlite pydantic-settings "pydantic[email]" "python-jose[cryptography]" "passlib[bcrypt]" python-multipart
python -m pip install -r requirements-streamlit.txt
```

There is currently no dedicated API requirements file; the first command installs the packages imported by the backend. `requirements-streamlit.txt` covers Streamlit and Requests.

## Run locally

Run both services from the **project root** (`ecommerce-api`) in separate terminals using the same environment:

```powershell
# Terminal 1: API
python -m uvicorn app.main:app --reload
```

```powershell
# Terminal 2: web UI
python -m streamlit run app/streamlit_app.py
```

- API: <http://127.0.0.1:8000>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Streamlit UI: <http://localhost:8501>

The UI defaults to `http://127.0.0.1:8000`. Change **FastAPI URL** in the sidebar if the API is running elsewhere. Changing that URL signs out the current UI session.

By default, the SQLite database URL is `sqlite+aiosqlite:///./e-commerce_db.db`, relative to the directory where the API starts. The API creates tables on startup; start it from the project root so it uses the expected database file.

## API routes

| Area | Routes |
| --- | --- |
| Authentication | `POST /auth/signup`, `POST /auth/login`, `GET /auth/me` |
| Products | `GET /products/getproducts`, `GET /products/getproduct/{prod_id}`, `POST /products/addproduct`, `POST /products/bulkaddproducts`, `DELETE /products/deleteproduct/{prod_id}` |
| Cart | `POST /cart/additems`, `GET /cart/getmycart`, `PATCH /cart/items/`, `DELETE /cart/removecartproduct/{product_id}`, `DELETE /cart/removecart`; admins can also look up carts by ID or user code |
| Orders | `POST /oders/checkout`, `GET /oders/getmyorders`, `GET /oders/{order_id}`, `POST /oders/{order_id}/cancel`, `GET /oders/seller/products`, `PATCH /oders/{order_id}/status` |
| Reviews | `POST /review/addreview`, `GET /review/getreview`, `PATCH /review/updatereview`, `DELETE /review/removereview/user`, `DELETE /review/removereview/admin` |
| Users (admin) | `GET /user/users`, `GET /user/users/{user_id}`, `PATCH /user/users/{user_id}/role`, `PATCH /user/users/{user_id}/status` |

**Note:** `/oders` is the current spelling of the order route prefix; the Streamlit UI uses it as implemented. Login takes form fields `username` (the email address) and `password`, and returns a bearer token. Use `/docs` for request schemas and response details.

## Configuration and current limitations

`app/config.py` loads configuration from environment variables or a `.env` file: `DATABASE_URL`, `SECRET_KEY`, and `ALGORITHM`. Set a unique `SECRET_KEY` before deployment; do not publish credentials or real customer data with a database file.

Streamlit hides actions by role, but **the API must enforce access control**. Currently, `DELETE /products/deleteproduct/{prod_id}` has no server-side role check, so its visibility in the UI is not authorization. Some existing order-cancellation rules may reject a cancellation based on status; the UI displays the API's response. See [STREAMLIT.md](STREAMLIT.md) for more UI details.

## Project layout

```text
ecommerce-api/
├── app/
│   ├── main.py              # FastAPI application and routers
│   ├── streamlit_app.py     # Separate Streamlit HTTP client
│   ├── config.py            # Settings
│   ├── database.py          # Async SQLAlchemy session
│   ├── core/                # Auth, dependencies, errors, ID generation
│   ├── endpoints/           # API routes
│   ├── models/              # Database models
│   └── schemas/             # Request/response models
├── requirements-streamlit.txt
└── STREAMLIT.md
```
