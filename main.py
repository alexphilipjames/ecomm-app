from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext

app = FastAPI(title="MiniCart API", description="A simple e-commerce API demo")

# Security
SECRET_KEY = "your-secret-key-keep-it-secret"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Mock Database
users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
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

# Models
class User(BaseModel):
    username: str
    email: str
    is_admin: bool = False

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Product(BaseModel):
    id: int
    name: str
    price: float
    description: str
    stock: int

class CartItem(BaseModel):
    product_id: int
    quantity: int

class Order(BaseModel):
    id: int
    user_id: str
    items: List[CartItem]
    total: float
    status: str
    created_at: datetime

# Auth functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    user = users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# User routes
@app.post("/signup")
async def signup(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": pwd_context.hash(user.password),
        "is_admin": False
    }
    return {"message": "User created successfully"}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "is_admin": current_user["is_admin"]
    }

# Product routes
@app.get("/products")
async def get_products():
    return list(products_db.values())

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@app.post("/products")
async def create_product(product: Product, current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    products_db[product.id] = product.dict()
    return product

@app.put("/products/{product_id}")
async def update_product(product_id: int, product: Product, current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    products_db[product_id] = product.dict()
    return product

@app.delete("/products/{product_id}")
async def delete_product(product_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]
    return {"message": "Product deleted successfully"}

# Cart routes
@app.get("/cart")
async def get_cart(current_user: dict = Depends(get_current_user)):
    return carts_db.get(current_user["username"], [])

@app.post("/cart")
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    if item.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    if current_user["username"] not in carts_db:
        carts_db[current_user["username"]] = []
    carts_db[current_user["username"]].append(item.dict())
    return {"message": "Item added to cart"}

@app.put("/cart/{item_id}")
async def update_cart_item(item_id: int, quantity: int, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    if item_id >= len(carts_db[current_user["username"]]):
        raise HTTPException(status_code=404, detail="Item not found in cart")
    carts_db[current_user["username"]][item_id]["quantity"] = quantity
    return {"message": "Cart updated"}

@app.delete("/cart/{item_id}")
async def remove_from_cart(item_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    if item_id >= len(carts_db[current_user["username"]]):
        raise HTTPException(status_code=404, detail="Item not found in cart")
    carts_db[current_user["username"]].pop(item_id)
    return {"message": "Item removed from cart"}

# Order routes
@app.post("/checkout")
async def checkout(current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in carts_db or not carts_db[current_user["username"]]:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    order_id = len(orders_db) + 1
    items = carts_db[current_user["username"]]
    total = sum(item["quantity"] * products_db[item["product_id"]]["price"] for item in items)
    
    order = {
        "id": order_id,
        "user_id": current_user["username"],
        "items": items,
        "total": total,
        "status": "pending",
        "created_at": datetime.now()
    }
    
    orders_db[order_id] = order
    carts_db[current_user["username"]] = []
    return order

@app.get("/orders")
async def get_orders(current_user: dict = Depends(get_current_user)):
    user_orders = [order for order in orders_db.values() if order["user_id"] == current_user["username"]]
    return user_orders

@app.get("/orders/{order_id}")
async def get_order(order_id: int, current_user: dict = Depends(get_current_user)):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    order = orders_db[order_id]
    if order["user_id"] != current_user["username"] and not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return order

# Payment routes
@app.post("/payment/initiate")
async def initiate_payment(order_id: int, current_user: dict = Depends(get_current_user)):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    if orders_db[order_id]["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"payment_id": "mock_payment_123", "status": "initiated"}

@app.post("/payment/confirm")
async def confirm_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    return {"status": "success", "message": "Payment confirmed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 