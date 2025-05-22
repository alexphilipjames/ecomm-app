from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import get_current_user, create_access_token, get_password_hash, verify_password
from app.core.config import users_db, products_db, carts_db, orders_db
from app.schemas.models import User, UserCreate, Product, ProductCreate, CartItem, Order, Token

router = APIRouter()

# User routes
@router.post("/signup", response_model=dict)
async def signup(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
        "is_admin": False
    }
    return {"message": "User created successfully"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/profile", response_model=User)
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

# Product routes
@router.get("/products", response_model=List[Product])
async def get_products():
    return list(products_db.values())

@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@router.post("/products", response_model=Product)
async def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    product_id = max(products_db.keys()) + 1 if products_db else 1
    product_dict = product.dict()
    product_dict["id"] = product_id
    products_db[product_id] = product_dict
    return product_dict

@router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: int, product: ProductCreate, current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    product_dict = product.dict()
    product_dict["id"] = product_id
    products_db[product_id] = product_dict
    return product_dict

@router.delete("/products/{product_id}")
async def delete_product(product_id: int, current_user: dict = Depends(get_current_user)):
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]
    return {"message": "Product deleted successfully"}

# Cart routes
@router.get("/cart", response_model=List[CartItem])
async def get_cart(current_user: dict = Depends(get_current_user)):
    return carts_db.get(current_user["username"], [])

@router.post("/cart", response_model=dict)
async def add_to_cart(item: CartItem, current_user: dict = Depends(get_current_user)):
    if item.product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    if current_user["username"] not in carts_db:
        carts_db[current_user["username"]] = []
    carts_db[current_user["username"]].append(item.dict())
    return {"message": "Item added to cart"}

@router.put("/cart/{item_id}", response_model=dict)
async def update_cart_item(item_id: int, quantity: int, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    if item_id >= len(carts_db[current_user["username"]]):
        raise HTTPException(status_code=404, detail="Item not found in cart")
    carts_db[current_user["username"]][item_id]["quantity"] = quantity
    return {"message": "Cart updated"}

@router.delete("/cart/{item_id}", response_model=dict)
async def remove_from_cart(item_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["username"] not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    if item_id >= len(carts_db[current_user["username"]]):
        raise HTTPException(status_code=404, detail="Item not found in cart")
    carts_db[current_user["username"]].pop(item_id)
    return {"message": "Item removed from cart"}

# Order routes
@router.post("/checkout", response_model=Order)
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

@router.get("/orders", response_model=List[Order])
async def get_orders(current_user: dict = Depends(get_current_user)):
    user_orders = [order for order in orders_db.values() if order["user_id"] == current_user["username"]]
    return user_orders

@router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: int, current_user: dict = Depends(get_current_user)):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    order = orders_db[order_id]
    if order["user_id"] != current_user["username"] and not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return order

# Payment routes
@router.post("/payment/initiate", response_model=dict)
async def initiate_payment(order_id: int, current_user: dict = Depends(get_current_user)):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    if orders_db[order_id]["user_id"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return {"payment_id": "mock_payment_123", "status": "initiated"}

@router.post("/payment/confirm", response_model=dict)
async def confirm_payment(payment_id: str, current_user: dict = Depends(get_current_user)):
    return {"status": "success", "message": "Payment confirmed"} 