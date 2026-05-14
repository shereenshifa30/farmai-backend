"""
FarmAI Complete Backend — main.py  (FINAL ALL-IN-ONE VERSION)
Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
import logging, time, io, copy, random, os
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from PIL import Image
import requests

# ── Optional TensorFlow ──────────────────────────────────────────────────────
try:
    import tensorflow as tf
    import numpy as np
    TF_OK = True
except ImportError:
    TF_OK = False
    print("⚠️  TensorFlow not installed → demo mode (install with: pip install tensorflow numpy)")

# ── SETTINGS ─────────────────────────────────────────────────────────────────
class Settings(BaseSettings):
    APP_VERSION:     str  = "1.0.0"
    MAX_FILE_SIZE_MB: int = 5
    MODEL_PATH:      str  = "models/crop_disease_model.h5"
    WEATHER_API_KEY: str  = "4aef48db5932ab5272d645ad6417161c"          # paste your WeatherAPI.com key in .env
    model_config = {"protected_namespaces": (), "env_file": ".env", "extra": "ignore"}

settings = Settings()

# ── PYDANTIC MODELS ───────────────────────────────────────────────────────────
class PredictOut(BaseModel):
    disease: str;  confidence: float
    solution_tamil: str;  solution_english: str
    model_config = {"protected_namespaces": ()}

class HealthOut(BaseModel):
    status: str;  version: str;  model_loaded: bool
    model_config = {"protected_namespaces": ()}

# ── ML MODEL ──────────────────────────────────────────────────────────────────
_model = None;  MODEL_LOADED = False
if TF_OK:
    try:
        _model = tf.keras.models.load_model(settings.MODEL_PATH)
        MODEL_LOADED = True
        print(f"✅ Model loaded: {settings.MODEL_PATH}")
    except Exception as e:
        print(f"⚠️  Model load failed: {e}\n   → running in demo mode")
        print(f"   Place your .h5 file at:  {settings.MODEL_PATH}")

CLASS_LABELS = [
    "Tomato_Bacterial_spot", "Tomato_Early_blight", "Tomato_Late_blight",
    "Tomato_Leaf_Mold", "Tomato_Septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite", "Tomato__Target_Spot",
    "Tomato__Tomato_YellowLeaf__Curl_Virus", "Tomato__Tomato_mosaic_virus",
    "Tomato_healthy",
]

DISEASE_DB = {
    "Tomato Bacterial Spot":  {"disease":"Tomato Bacterial Spot","solution_tamil":"பாதிக்கப்பட்ட இலைகளை அகற்றி காப்பர் பூஞ்சைநாசினி தெளிக்கவும்.","solution_english":"Remove infected leaves and apply copper-based fungicide spray."},
    "Tomato Early Blight":    {"disease":"Tomato Early Blight","solution_tamil":"மாங்கோசெப் அல்லது குளோரோத்தலோனில் தெளிக்கவும். பாதிக்கப்பட்ட இலைகளை அகற்றவும்.","solution_english":"Spray Mancozeb or Chlorothalonil. Remove affected leaves immediately."},
    "Tomato Late Blight":     {"disease":"Tomato Late Blight","solution_tamil":"மெட்டலாக்சில் அல்லது மேன்கோசெப் தெளிக்கவும். ஈரப்பதம் குறைக்கவும்.","solution_english":"Use Metalaxyl or Mancozeb fungicide. Reduce field moisture."},
    "Tomato Leaf Mold":       {"disease":"Tomato Leaf Mold","solution_tamil":"காற்றோட்டம் அதிகரித்து பூஞ்சைநாசினி பயன்படுத்தவும்.","solution_english":"Improve airflow and apply fungicide. Avoid overhead watering."},
    "Tomato Septoria Leaf Spot":{"disease":"Tomato Septoria Leaf Spot","solution_tamil":"பாதிக்கப்பட்ட இலைகளை அகற்றி பூஞ்சைநாசினி தெளிக்கவும்.","solution_english":"Remove infected leaves. Spray Mancozeb or copper fungicide."},
    "Tomato Spider Mites Two Spotted Spider Mite":{"disease":"Spider Mite Attack","solution_tamil":"நீம் எண்ணெய் அல்லது அகாரிசைடு தெளிக்கவும். இலைகளை தண்ணீரால் கழுவவும்.","solution_english":"Use neem oil or acaricide spray. Wash leaves with water."},
    "Tomato Target Spot":     {"disease":"Tomato Target Spot","solution_tamil":"பூஞ்சைநாசினி தெளித்து ஈரப்பதம் கட்டுப்படுத்தவும்.","solution_english":"Apply fungicide and control humidity levels in the field."},
    "Tomato Tomato Yellowleaf Curl Virus":{"disease":"Yellow Leaf Curl Virus","solution_tamil":"வெள்ளை ஈக்களை பூச்சுக்கொல்லி மூலம் கட்டுப்படுத்தவும். பாதிக்கப்பட்ட தாவரங்களை அகற்றவும்.","solution_english":"Control whiteflies with insecticides. Remove infected plants."},
    "Tomato Tomato Mosaic Virus":{"disease":"Tomato Mosaic Virus","solution_tamil":"நோயுற்ற தாவரங்களை உடனே அகற்றவும். கருவிகளை கிருமிநாசினியால் சுத்தம் செய்யவும்.","solution_english":"Remove infected plants immediately. Disinfect tools after use."},
    "Tomato Healthy":         {"disease":"Healthy Crop ✅","solution_tamil":"உங்கள் பயிர் ஆரோக்கியமாக உள்ளது! தொடர்ந்து கவனித்து வாருங்கள்.","solution_english":"Your crop is healthy! Continue regular monitoring and care."},
}

MARKET_BASE = [
    {"id":1, "crop":"Rice",      "crop_ta":"அரிசி",          "price":2200,"prev":2100,"unit":"per quintal","market":"Madurai Mandi"},
    {"id":2, "crop":"Wheat",     "crop_ta":"கோதுமை",         "price":2100,"prev":2100,"unit":"per quintal","market":"Chennai APMC"},
    {"id":3, "crop":"Tomato",    "crop_ta":"தக்காளி",        "price":800, "prev":1100,"unit":"per quintal","market":"Madurai Mandi"},
    {"id":4, "crop":"Onion",     "crop_ta":"வெங்காயம்",      "price":1500,"prev":1300,"unit":"per quintal","market":"Coimbatore APMC"},
    {"id":5, "crop":"Banana",    "crop_ta":"வாழை",           "price":1200,"prev":1200,"unit":"per quintal","market":"Madurai Mandi"},
    {"id":6, "crop":"Sugarcane", "crop_ta":"கரும்பு",        "price":350, "prev":320, "unit":"per quintal","market":"Trichy APMC"},
    {"id":7, "crop":"Cotton",    "crop_ta":"பருத்தி",        "price":6500,"prev":6200,"unit":"per quintal","market":"Chennai APMC"},
    {"id":8, "crop":"Groundnut", "crop_ta":"கடலை",           "price":5200,"prev":5200,"unit":"per quintal","market":"Madurai Mandi"},
    {"id":9, "crop":"Turmeric",  "crop_ta":"மஞ்சள்",         "price":7500,"prev":7000,"unit":"per quintal","market":"Erode APMC"},
    {"id":10,"crop":"Chilli",    "crop_ta":"மிளகாய்",        "price":9000,"prev":9500,"unit":"per quintal","market":"Guntur APMC"},
    {"id":11,"crop":"Coconut",   "crop_ta":"தேங்காய்",       "price":120, "prev":115, "unit":"per piece",  "market":"Pollachi APMC"},
    {"id":12,"crop":"Maize",     "crop_ta":"மக்காச்சோளம்",  "price":1800,"prev":1750,"unit":"per quintal","market":"Coimbatore APMC"},
]

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("farmai")

# ── APP ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="FarmAI API", version="1.0.0", docs_url="/docs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.middleware("http")
async def log_req(req: Request, call_next):
    t0 = time.time(); r = await call_next(req)
    logger.info(f"{req.method} {req.url.path} {r.status_code} {round((time.time()-t0)*1000)}ms")
    return r

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status":"ok","message":"FarmAI running 🌿","model_loaded":MODEL_LOADED,"docs":"/docs"}

@app.get("/health", response_model=HealthOut)
def health():
    return HealthOut(status="ok", version=settings.APP_VERSION, model_loaded=MODEL_LOADED)

@app.post("/predict", response_model=PredictOut)
async def predict_disease(file: UploadFile = File(...)):
    ct = file.content_type or ""
    if ct not in ["image/jpeg","image/png","image/webp","image/jpg"]:
        raise HTTPException(400, f"Invalid type '{ct}'. Use JPG, PNG or WEBP.")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file.")
    if len(data) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB.")

    if MODEL_LOADED and _model and TF_OK:
        try:
            img   = Image.open(io.BytesIO(data)).convert("RGB").resize((224, 224))
            arr   = np.expand_dims(np.array(img) / 255.0, 0)
            preds = _model.predict(arr, verbose=0)
            idx   = int(np.argmax(preds[0]))
            conf  = float(preds[0][idx]) * 100
            raw   = CLASS_LABELS[idx]
            name  = raw.replace("__", " ").replace("_", " ").title()
            db    = DISEASE_DB.get(name, {
                "disease": name,
                "solution_tamil": "தகவல் இல்லை — விவசாய நிபுணரை அணுகவும்.",
                "solution_english": "No data found. Please consult an agricultural expert.",
            })
            logger.info(f"Predicted: {name}  conf={conf:.1f}%")
            return PredictOut(disease=db["disease"], confidence=round(conf,1),
                              solution_tamil=db["solution_tamil"], solution_english=db["solution_english"])
        except Exception as e:
            logger.error(f"Predict error: {e}")
            raise HTTPException(500, f"Prediction failed: {str(e)}")
    else:
        # Demo mode: return random sample so UI works without model
        sample = random.choice(list(DISEASE_DB.values()))
        return PredictOut(
            disease=sample["disease"],
            confidence=round(random.uniform(78, 95), 1),
            solution_tamil=sample["solution_tamil"],
            solution_english=sample["solution_english"],
        )

@app.get("/weather/{city}")
def get_weather(city: str):
    key = settings.WEATHER_API_KEY
    if not key or key.startswith("your_") or key == "":
        # ── Demo mode ──
        rain = random.random() > 0.45
        return _demo_weather(city, rain)
    try:
        r = requests.get(
            "https://api.weatherapi.com/v1/forecast.json",
            params={"key": key, "q": city, "days": 5, "aqi": "no", "alerts": "yes"},
            timeout=10,
        )
        d = r.json()
        if "error" in d:
            raise HTTPException(400, d["error"]["message"])
        cur  = d["current"];  loc = d["location"]
        fc   = d["forecast"]["forecastday"]
        hr   = any(f["day"]["daily_chance_of_rain"] > 60 for f in fc[:2])
        adv  = []
        if hr:  adv.append("🌧️ Rain expected — avoid irrigation and protect crops")
        if cur["temp_c"] > 38: adv.append("🌡️ Very hot — water crops early morning or evening")
        if cur["humidity"] > 80: adv.append("💧 High humidity — watch for fungal diseases")
        if not adv: adv.append("✅ Weather looks good for farming today!")
        return {
            "current": {
                "city": loc["name"], "region": loc["region"], "country": loc["country"],
                "temp_c": cur["temp_c"], "feels_like": cur["feelslike_c"],
                "humidity": cur["humidity"], "wind_kph": cur["wind_kph"],
                "condition": cur["condition"]["text"], "uv": cur.get("uv", 0),
            },
            "forecast": [
                {"date": f["date"], "max_temp": f["day"]["maxtemp_c"],
                 "min_temp": f["day"]["mintemp_c"], "condition": f["day"]["condition"]["text"],
                 "humidity": f["day"]["avghumidity"], "rain_chance": f["day"]["daily_chance_of_rain"]}
                for f in fc
            ],
            "advice": adv,
            "has_rain_alert": hr,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

def _demo_weather(city, rain):
    return {
        "current": {
            "city": city, "region": "Tamil Nadu", "country": "India",
            "temp_c": random.randint(32,41), "feels_like": random.randint(35,44),
            "humidity": random.randint(55,85), "wind_kph": random.randint(8,22),
            "condition": "Thunderstorm" if rain else "Partly Cloudy",
            "uv": random.randint(7,11),
        },
        "forecast": [
            {"date":"2026-05-04","max_temp":38,"min_temp":28,"condition":"Thunderstorm" if rain else "Sunny","humidity":82 if rain else 60,"rain_chance":88 if rain else 8},
            {"date":"2026-05-05","max_temp":37,"min_temp":27,"condition":"Rain" if rain else "Partly Cloudy","humidity":85 if rain else 65,"rain_chance":90 if rain else 18},
            {"date":"2026-05-06","max_temp":36,"min_temp":26,"condition":"Cloudy","humidity":68,"rain_chance":35},
            {"date":"2026-05-07","max_temp":39,"min_temp":29,"condition":"Sunny","humidity":55,"rain_chance":5},
            {"date":"2026-05-08","max_temp":40,"min_temp":30,"condition":"Clear","humidity":50,"rain_chance":0},
        ],
        "advice": ["🌧️ Rain expected — avoid irrigation today","⚠️ Protect your crops from heavy rainfall"] if rain
                   else ["☀️ Good farming weather today!","✅ No rain expected this week"],
        "has_rain_alert": rain,
    }

@app.get("/market")
def get_market(search: str = ""):
    result = copy.deepcopy(MARKET_BASE)
    for item in result:
        var = random.randint(-120, 120)
        item["price"] = max(50, item["price"] + var)
        diff = item["price"] - item["prev"]
        item["trend"] = "up" if diff > 30 else ("down" if diff < -30 else "stable")
    if search:
        s = search.lower()
        result = [r for r in result if s in r["crop"].lower() or s in r["crop_ta"]]
    return {
        "prices": result,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(result),
    }
    # ── AUTH ROUTES ───────────────────────────────────────────────────────────────
from pydantic import BaseModel as BM

class AuthUser(BM):
    email: str
    password: str

# Simple in-memory user store (works without Supabase)
_users = {}

@app.post("/auth/signup")
def signup(user: AuthUser):
    if user.email in _users:
        raise HTTPException(400, "Email already registered. Please login.")
    if len(user.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters.")
    _users[user.email] = user.password
    return {
        "message": "Account created successfully!",
        "email": user.email,
        "token": f"farmai-token-{user.email}",
        "demo": True
    }

@app.post("/auth/login")
def login(user: AuthUser):
    if user.email not in _users:
        raise HTTPException(401, "Email not found. Please sign up first.")
    if _users[user.email] != user.password:
        raise HTTPException(401, "Wrong password. Please try again.")
    return {
        "message": "Login successful!",
        "email": user.email,
        "token": f"farmai-token-{user.email}",
        "demo": True
    }

@app.post("/auth/logout")
def logout():
    return {"message": "Logged out successfully"}
    # ── SOIL ROUTES ───────────────────────────────────────────────────────────────
from pydantic import BaseModel as BM2

class SoilIn(BM2):
    field_name: str
    ph: float
    nitrogen: float
    moisture: float
    notes: str = ""

_soil = []
_sid  = 0

def soil_advice(ph, nitrogen, moisture):
    rows = []
    # pH
    if ph < 6.0:
        rows.append({"label":"pH Level","value":ph,"status":"warning","msg":f"pH {ph} is too acidic. Add lime to raise pH.","color":"#b45309"})
    elif ph > 7.5:
        rows.append({"label":"pH Level","value":ph,"status":"warning","msg":f"pH {ph} is too alkaline. Add sulfur to lower pH.","color":"#b45309"})
    else:
        rows.append({"label":"pH Level","value":ph,"status":"good","msg":f"pH {ph} is ideal for most crops ✅","color":"#16a34a"})
    # Nitrogen
    if nitrogen < 30:
        rows.append({"label":"Nitrogen","value":nitrogen,"status":"bad","msg":f"Nitrogen {nitrogen}% is low. Apply urea or compost immediately.","color":"#c0392b"})
    elif nitrogen > 80:
        rows.append({"label":"Nitrogen","value":nitrogen,"status":"warning","msg":f"Nitrogen {nitrogen}% is too high. Reduce fertilizer usage.","color":"#b45309"})
    else:
        rows.append({"label":"Nitrogen","value":nitrogen,"status":"good","msg":f"Nitrogen {nitrogen}% is good ✅","color":"#16a34a"})
    # Moisture
    if moisture < 40:
        rows.append({"label":"Moisture","value":moisture,"status":"warning","msg":f"Moisture {moisture}% is low. Increase irrigation now.","color":"#b45309"})
    elif moisture > 80:
        rows.append({"label":"Moisture","value":moisture,"status":"warning","msg":f"Moisture {moisture}% is too high. Improve field drainage.","color":"#b45309"})
    else:
        rows.append({"label":"Moisture","value":moisture,"status":"good","msg":f"Moisture {moisture}% is ideal ✅","color":"#16a34a"})
    return rows

@app.get("/soil/")
def get_soil():
    return {"records": _soil, "total": len(_soil)}

@app.post("/soil/add")
def add_soil(r: SoilIn):
    global _sid
    _sid += 1
    rec = {
        **r.dict(),
        "id":   _sid,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "advice": soil_advice(r.ph, r.nitrogen, r.moisture),
        "overall": "good" if all(x["status"]=="good" for x in soil_advice(r.ph,r.nitrogen,r.moisture)) else "needs attention"
    }
    _soil.append(rec)
    return {"message": "Record added!", "record": rec}

@app.get("/soil/delete/{rid}")
def del_soil(rid: int):
    global _soil
    _soil = [s for s in _soil if s["id"] != rid]
    return {"message": "Deleted"}