from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

# ── Temporary storage (will move to Supabase later) ──
soil_records = []

class SoilRecord(BaseModel):
    field_name: str
    ph: float
    nitrogen: float
    moisture: float
    notes: Optional[str] = ""

@router.get("/")
def get_all_records():
    return {"records": soil_records, "total": len(soil_records)}

@router.post("/add")
def add_record(record: SoilRecord):
    new_record = record.dict()
    new_record["id"] = len(soil_records) + 1
    new_record["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_record["advice"] = get_advice(record.ph, record.nitrogen, record.moisture)
    soil_records.append(new_record)
    return {"message": "Soil record added!", "record": new_record}

@router.delete("/delete/{record_id}")
def delete_record(record_id: int):
    global soil_records
    soil_records = [r for r in soil_records if r["id"] != record_id]
    return {"message": "Record deleted!"}

@router.get("/advice")
def get_soil_advice(ph: float, nitrogen: float, moisture: float):
    return {"advice": get_advice(ph, nitrogen, moisture)}

def get_advice(ph, nitrogen, moisture):
    advice = []
    if ph < 6.0:
        advice.append("Soil is acidic — add lime to raise pH")
    elif ph > 7.5:
        advice.append("Soil is alkaline — add sulfur to lower pH")
    else:
        advice.append("pH level is ideal for most crops ✅")
    if nitrogen < 30:
        advice.append("Low nitrogen — apply urea or compost")
    elif nitrogen > 80:
        advice.append("High nitrogen — reduce fertilizer usage")
    else:
        advice.append("Nitrogen level is good ✅")
    if moisture < 40:
        advice.append("Low moisture — increase irrigation")
    elif moisture > 80:
        advice.append("High moisture — improve drainage")
    else:
        advice.append("Moisture level is ideal ✅")
    return advice