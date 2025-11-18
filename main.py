import os
from typing import List, Optional, Literal, Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import create_document, get_documents, db
from schemas import Quote

app = FastAPI(title="Insurance Comparison API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuoteRequest(BaseModel):
    quote_type: Literal["auto", "home"]
    zip_code: str
    age: Optional[int] = Field(None, ge=16, le=120)

    # Auto
    vehicle_year: Optional[int] = Field(None, ge=1980, le=2100)
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    accidents_last_5_years: Optional[int] = Field(None, ge=0, le=10)

    # Home
    home_value: Optional[float] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, ge=100)
    security_system: Optional[bool] = None


class QuoteResponse(BaseModel):
    id: str
    quote_type: str
    zip_code: str
    results: List[Dict[str, Any]]


@app.get("/")
def read_root():
    return {"message": "Insurance Comparison API Running"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


@app.post("/api/quotes", response_model=QuoteResponse)
def create_quote(payload: QuoteRequest):
    """Create a quote request and return simulated comparison results.
    The request is persisted, and the returned results are embedded for later retrieval.
    """
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    base_price = 600.0 if payload.quote_type == "auto" else 1200.0

    modifiers = 0.0
    if payload.age and payload.age < 25:
        modifiers += 0.25
    if payload.quote_type == "auto":
        if payload.vehicle_year and payload.vehicle_year < 2005:
            modifiers += 0.15
        if (payload.accidents_last_5_years or 0) > 0:
            modifiers += min(0.4, 0.1 * (payload.accidents_last_5_years or 0))
    if payload.quote_type == "home":
        if payload.home_value and payload.home_value > 750000:
            modifiers += 0.2
        if payload.security_system:
            modifiers -= 0.05

    carriers = [
        {
            "name": "BlueShield Mutual",
            "monthly": round(base_price * (1 + modifiers) / 12 * 0.95, 2),
            "rating": 4.7,
            "features": ["24/7 support", "Bundle discount", "Fast claims"],
            "cta": "Get Started"
        },
        {
            "name": "NorthStar Insurance",
            "monthly": round(base_price * (1 + modifiers) / 12 * 1.02, 2),
            "rating": 4.5,
            "features": ["Accident forgiveness", "Roadside (auto)", "Smart home (home)"],
            "cta": "Select"
        },
        {
            "name": "Aurora Coverage Co.",
            "monthly": round(base_price * (1 + modifiers) / 12 * 0.88, 2),
            "rating": 4.3,
            "features": ["Low deductible options", "Local agents", "Online portal"],
            "cta": "View Details"
        }
    ]

    # Persist to DB
    doc = payload.model_dump()
    doc["results"] = carriers
    from bson import ObjectId
    collection_name = "quote"
    try:
        inserted_id = create_document(collection_name, doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")

    return QuoteResponse(
        id=inserted_id,
        quote_type=payload.quote_type,
        zip_code=payload.zip_code,
        results=carriers
    )


@app.get("/api/quotes")
def list_quotes(limit: int = 20):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        docs = get_documents("quote", limit=limit)
        for d in docs:
            d["_id"] = str(d["_id"])  # make JSON serializable
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
