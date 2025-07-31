import os
import numpy as np
import faiss
import openai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from responses import faq_data
from datetime import datetime
import sqlite3
import requests
from bs4 import BeautifulSoup

load_dotenv()

# --- Load OpenAI Key ---
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Load embedding model ---
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    print("⚠️ Model loading failed:", e)
    model = None

# --- Encode FAQ questions ---
faq_questions = [item["question_lower"] for item in faq_data]
faq_embeddings = model.encode(faq_questions, convert_to_numpy=True)

# --- Build FAISS index ---
dimension = faq_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(faq_embeddings)

# --- Log missed queries to SQLite ---
def log_missed_query(query):
    try:
        conn = sqlite3.connect("missed_queries.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS missed (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                     )''')
        c.execute('INSERT INTO missed (query) VALUES (?)', (query,))
        conn.commit()
        conn.close()
    except Exception as e:
        print("❌ Failed to log missed query:", e)

# --- Scrape fallback from website ---
def get_scraped_data(query):
    try:
        url = "https://www.hirebie.com/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print("⚠️ Failed to fetch webpage.")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Clean page text
        page_text = soup.get_text(separator=' ', strip=True)
        page_text_lower = page_text.lower()

        # Normalize query for matching
        query_words = [word for word in query.lower().split() if len(word) > 3]

        # Check if any word in query exists in page
        for word in query_words:
            if word in page_text_lower:
                start = page_text_lower.find(word)
                snippet = page_text[max(0, start - 100): start + 300]
                return f"(From hirebie.com): ...{snippet.strip()}..."

        return None  # No keyword match found

    except Exception as e:
        print("❌ Error scraping hirebie.com:", e)
        return None


# --- Main chatbot response logic ---
def get_response(user_query):
    if not model:
        return {
            "answer": "Sorry, the AI model isn't currently available.",
            "question": user_query,
            "source": "error"
        }

    user_query_clean = user_query.strip().lower()

    # 1. Exact match from FAQ
    for item in faq_data:
        if user_query_clean == item["question_lower"]:
            return {
                "answer": item["answer"],
                "question": item["question"],
                "source": "faq"
            }

    # 2. Semantic match
    user_vec = model.encode([user_query_clean])
    D, I = index.search(user_vec, k=1)
    best_match_idx = I[0][0]
    score = D[0][0]

    if best_match_idx < len(faq_data) and score < 0.8:
        best_faq = faq_data[best_match_idx]
        return {
            "answer": best_faq["answer"],
            "question": best_faq["question"],
            "source": "semantic"
        }

    # 3. Try web scraping
    scraped_answer = get_scraped_data(user_query)
    if scraped_answer:
        print("✅ Found scraped content.")
        return {
            "answer": scraped_answer,
            "question": user_query,
            "source": "scraped"
        }

    # 4. Fallback to GPT
    try:
        gpt_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Hirebie.com"},
                {"role": "user", "content": user_query}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return {
            "answer": gpt_response['choices'][0]['message']['content'].strip(),
            "question": user_query,
            "source": "gpt"
        }

    except Exception as e:
        print("⚠️ GPT Fallback failed:", e)
        log_missed_query(user_query)
        return {
            "answer": "Sorry, I couldn't fetch a proper answer right now.",
            "question": user_query,
            "source": "error"
        }

# --- Suggestions from similar questions ---
def get_suggestions(user_query=None, top_k=3):
    suggestions = []

    if user_query and model:
        try:
            query_vec = model.encode([user_query])
            D, I = index.search(np.array(query_vec).astype('float32'), top_k + 1)

            for idx in I[0]:
                if idx < len(faq_data):
                    question = faq_data[idx]["question"]
                    if question.lower() != user_query.lower():
                        suggestions.append(question)
                if len(suggestions) >= top_k:
                    break
        except:
            pass
    else:
        suggestions = [item['question'] for item in faq_data[:top_k]]

    return suggestions

# --- Default suggestions for initial load ---
def default_suggestions():
    return [item['question'] for item in faq_data[:3]]
