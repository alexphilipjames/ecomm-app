from datetime import timedelta

# Security
SECRET_KEY = "your-secret-key-keep-it-secret"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Mock Database
users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": None,  # Will be set in security.py
        "is_admin": True
    }
}

products_db = {
    1: {
        "id": 1,
        "name": "Laptop",
        "price": 999.99,
        "description": "High-performance laptop",
        "stock": 10
    },
    2: {
        "id": 2,
        "name": "Smartphone",
        "price": 499.99,
        "description": "Latest smartphone model",
        "stock": 20
    }
}

carts_db = {}
orders_db = {} 