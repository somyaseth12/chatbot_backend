import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_uri = os.getenv("MONGO_URI")  # Should be in your .env
client = MongoClient(mongo_uri)
db = client["chatbot"]
collection = db["faqs"]

# Load JSON data
with open("faq.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

# Insert into MongoDB
if faqs:
    result = collection.insert_many(faqs)
    print(f"✅ Inserted {len(result.inserted_ids)} FAQs into MongoDB.")
else:
    print("⚠️ No data found in the JSON file.")
