# MiniCart - Simple E-Commerce API Demo

A FastAPI-based e-commerce API demo with simulated data. This project demonstrates a basic e-commerce system with user management, product catalog, shopping cart, and order processing.

## Features

- User authentication (JWT-based)
- Product management
- Shopping cart functionality
- Order processing
- Mock payment system
- Admin capabilities

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc`

## Default Admin Account

- Username: `admin`
- Password: `admin123`

## API Endpoints

### User Management
- `POST /signup` - Register new user
- `POST /login` - Login and get JWT token
- `GET /profile` - Get user profile (requires auth)

### Products
- `GET /products` - List all products
- `GET /products/{id}` - Get product details
- `POST /products` - Add new product (admin only)
- `PUT /products/{id}` - Update product (admin only)
- `DELETE /products/{id}` - Delete product (admin only)

### Cart
- `GET /cart` - View cart
- `POST /cart` - Add item to cart
- `PUT /cart/{item_id}` - Update cart item quantity
- `DELETE /cart/{item_id}` - Remove item from cart

### Orders
- `POST /checkout` - Place order
- `GET /orders` - List user's orders
- `GET /orders/{order_id}` - Get order details

### Payments
- `POST /payment/initiate` - Start payment process
- `POST /payment/confirm` - Confirm payment

## Note

This is a demo application with simulated data. In a production environment, you would need to:
- Use a proper database
- Implement proper security measures
- Add input validation
- Add error handling
- Implement real payment processing
- Add logging and monitoring 