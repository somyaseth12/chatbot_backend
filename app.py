import os
import sqlite3
import secrets
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from chatbot_engine import get_response, log_missed_query, get_suggestions, default_suggestions

import pymongo

# Load env
load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = pymongo.MongoClient(MONGO_URI)
mongo_db = mongo_client["chatbot"]
faq_collection = mongo_db["faqs"]

# Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Feedback DB init
FEEDBACK_DB = 'feedback.db'
def init_feedback_db():
    conn = sqlite3.connect(FEEDBACK_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER NOT NULL,
            comment TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_feedback_db()

@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.get_json()
    query = data.get("query", "")
    suggestions = get_suggestions(query)
    return jsonify({"suggestions": suggestions})


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/suggestions", methods=["GET"])
def starter_suggestions():
    suggestions = get_suggestions()
    return jsonify({"suggestions": suggestions})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        msg = request.json.get("message", "").strip()
        result = get_response(msg)
        if isinstance(result, dict) and result.get("source", "").startswith("faq"):
            suggestions = get_suggestions(msg) or default_suggestions()
        else:
            log_missed_query(msg)
            print("🧠 GPT/API fallback for:", msg)
            suggestions = ["Do you offer custom UI/UX design?", "Do you offer content creation services?", "Can you produce marketing videos?"]

        return jsonify({
            "response": result["answer"] if isinstance(result, dict) else result,
            "suggestions": suggestions
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({
            "response": "Sorry, something went wrong.",
            "suggestions": default_suggestions()
        }), 500


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment', '')
    if rating is None:
        return jsonify({'status': 'error', 'message': 'Rating is required'}), 400
    conn = sqlite3.connect(FEEDBACK_DB)
    c = conn.cursor()
    c.execute('INSERT INTO feedback (rating, comment) VALUES (?, ?)', (rating, comment))
    conn.commit(); conn.close()
    return jsonify({'status': 'success', 'message': 'Feedback received'})

@app.route('/clear-history', methods=['POST'])
def clear_history():
    session.pop('history', None)
    return jsonify({"message": "Chat history cleared"})

@app.route('/rating', methods=['POST'])
def rating_route():
    data = request.get_json()
    score = data.get("score")
    if score is None:
        return jsonify({"status": "error", "message": "Score missing"}), 400
    print(f"📊 Received rating: {score}")
    return jsonify({"status": "received"})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/get-response", methods=["POST"])
def chat_response():
    data = request.get_json()
    user_input = data.get("message")
    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    response = get_response(user_input)
    suggestions = get_suggestions(user_input)
    response["suggestions"] = suggestions

    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
