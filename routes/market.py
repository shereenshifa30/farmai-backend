from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

# ── Tamil Nadu Market Data ──
MARKET_DATA = [
    {"id":1,  "crop":"Rice",       "price":2200, "prev_price":2100, "unit":"per quintal", "market":"Madurai Mandi",    "state":"Tamil Nadu", "trend":"up"},
    {"id":2,  "crop":"Wheat",      "price":2100, "prev_price":2100, "unit":"per quintal", "market":"Chennai APMC",     "state":"Tamil Nadu", "trend":"stable"},
    {"id":3,  "crop":"Tomato",     "price":800,  "prev_price":1100, "unit":"per quintal", "market":"Madurai Mandi",    "state":"Tamil Nadu", "trend":"down"},
    {"id":4,  "crop":"Onion",      "price":1500, "prev_price":1300, "unit":"per quintal", "market":"Coimbatore APMC",  "state":"Tamil Nadu", "trend":"up"},
    {"id":5,  "crop":"Banana",     "price":1200, "prev_price":1200, "unit":"per quintal", "market":"Madurai Mandi",    "state":"Tamil Nadu", "trend":"stable"},
    {"id":6,  "crop":"Sugarcane",  "price":350,  "prev_price":320,  "unit":"per quintal", "market":"Trichy APMC",      "state":"Tamil Nadu", "trend":"up"},
    {"id":7,  "crop":"Cotton",     "price":6500, "prev_price":6200, "unit":"per quintal", "market":"Chennai APMC",     "state":"Tamil Nadu", "trend":"up"},
    {"id":8,  "crop":"Groundnut",  "price":5200, "prev_price":5200, "unit":"per quintal", "market":"Madurai Mandi",    "state":"Tamil Nadu", "trend":"stable"},
    {"id":9,  "crop":"Turmeric",   "price":7500, "prev_price":7000, "unit":"per quintal", "market":"Erode APMC",       "state":"Tamil Nadu", "trend":"up"},
    {"id":10, "crop":"Chilli",     "price":9000, "prev_price":9500, "unit":"per quintal", "market":"Guntur APMC",      "state":"Tamil Nadu", "trend":"down"},
    {"id":11, "crop":"Coconut",    "price":120,  "prev_price":115,  "unit":"per piece",   "market":"Pollachi APMC",    "state":"Tamil Nadu", "trend":"up"},
    {"id":12, "crop":"Maize",      "price":1800, "prev_price":1750, "unit":"per quintal", "market":"Coimbatore APMC",  "state":"Tamil Nadu", "trend":"up"},
]

@router.get("/")
def get_all_prices():
    return {
        "prices": MARKET_DATA,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(MARKET_DATA)
    }

@router.get("/search/{crop_name}")
def search_crop(crop_name: str):
    results = [
        item for item in MARKET_DATA
        if crop_name.lower() in item["crop"].lower()
    ]
    if not results:
        return {"error": f"No data found for '{crop_name}'", "prices": []}
    return {"prices": results, "total": len(results)}

@router.get("/trending")
def get_trending():
    up     = [i for i in MARKET_DATA if i["trend"] == "up"]
    down   = [i for i in MARKET_DATA if i["trend"] == "down"]
    stable = [i for i in MARKET_DATA if i["trend"] == "stable"]
    return {"up": up, "down": down, "stable": stable}

@router.get("/{market_name}")
def get_by_market(market_name: str):
    results = [
        i for i in MARKET_DATA
        if market_name.lower() in i["market"].lower()
    ]
    return {"prices": results, "market": market_name}