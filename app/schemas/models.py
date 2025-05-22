from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    is_admin: bool = False

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    price: float
    description: str
    stock: int

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True

class CartItemBase(BaseModel):
    product_id: int
    quantity: int

class CartItem(CartItemBase):
    pass

class OrderBase(BaseModel):
    user_id: str
    items: List[CartItem]
    total: float
    status: str
    created_at: datetime

class Order(OrderBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None 