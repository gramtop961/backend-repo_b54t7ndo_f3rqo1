"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Any, Dict

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas here:
# --------------------------------------------------

class Quote(BaseModel):
    """
    Insurance quote submissions and results
    Collection name: "quote"
    """
    quote_type: Literal["auto", "home"] = Field(..., description="Type of insurance quote")
    zip_code: str = Field(..., description="US ZIP code")
    age: Optional[int] = Field(None, ge=16, le=120, description="Customer age")

    # Auto-specific
    vehicle_year: Optional[int] = Field(None, ge=1980, le=2100)
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    accidents_last_5_years: Optional[int] = Field(None, ge=0, le=10)

    # Home-specific
    home_value: Optional[float] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, ge=100)
    security_system: Optional[bool] = None

    # Results returned from pricing engine
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Carrier quotes returned to user")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
