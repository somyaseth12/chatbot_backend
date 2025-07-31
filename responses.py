import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

faq_data = []

# --- MongoDB Settings ---
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "chatbot")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "faq")

def preprocess_faqs(data):
    """Add lowercase version of questions for case-insensitive search."""
    for item in data:
        item["question_lower"] = item["question"].strip().lower()
    return data

# --- Try to Load from MongoDB ---
try:
    if not MONGO_URI:
        raise ValueError("MONGO_URI is missing from .env")

    print("🌐 Connecting to MongoDB...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]

    print(f"📥 Fetching data from {MONGO_DB}.{MONGO_COLLECTION}...")
    raw_data = list(collection.find({}, {"_id": 0, "question": 1, "answer": 1}))
    print(f"🔍 Raw documents from MongoDB: {len(raw_data)}")

    # Filter out entries missing question or answer
    valid_entries = [item for item in raw_data if "question" in item and "answer" in item]
    print(f"✅ Valid FAQ entries found: {len(valid_entries)}")

    if not valid_entries:
        raise ValueError("MongoDB FAQ collection is empty or invalid.")

    faq_data = preprocess_faqs(valid_entries)
    print(f"✅ Loaded {len(faq_data)} FAQ(s) from MongoDB.")

except Exception as e:
    print("❌ MongoDB load failed:", str(e))

    # --- Fallback to Local JSON ---
    try:
        json_path = os.path.join(os.path.dirname(__file__), "faq_data.json")
        print(f"📄 Loading from fallback JSON: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            raw_json_data = json.load(f)
            valid_json = [item for item in raw_json_data if "question" in item and "answer" in item]

        if not valid_json:
            raise ValueError("Local JSON is empty or invalid.")

        faq_data = preprocess_faqs(valid_json)
        print(f"✅ Loaded {len(faq_data)} FAQ(s) from local JSON.")

    except Exception as json_error:
        print("❌ Failed to load faq_data.json:", str(json_error))
        faq_data = []
