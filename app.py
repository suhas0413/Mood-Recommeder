from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
from dotenv import load_dotenv
import json
import re
from functools import lru_cache
from datetime import datetime

# ----------------------------
# INIT
# ----------------------------
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("WARNING: GROQ_API_KEY not found in environment.")

app = Flask(__name__)

client = Groq(api_key=api_key) if api_key else None

# Simple in-memory cache (upgradeable to Redis later)
CACHE = {}

# ----------------------------
# UTILITY FUNCTIONS
# ----------------------------

def validate_input(mood, topic):
    """Validate user input"""
    if not mood or not isinstance(mood, str):
        return False, "Mood is required and must be a string"
    if len(mood) > 50:
        return False, "Mood too long"
    if topic and not isinstance(topic, str):
        return False, "Topic must be a string"
    if topic and len(topic) > 100:
        return False, "Topic too long"
    return True, None


def build_prompt(mood, topic):
    """Structured prompt engineering (improved)"""
    return f"""
You are an advanced AI recommendation engine.

User Context:
- Mood: {mood}
- Topic: {topic if topic else "general"}

Task:
Recommend personalized content strictly based on mood + topic.

Return ONLY valid JSON (no explanation, no markdown):

{{
  "moodSummary": "One sentence summary of the mood and recommendations",
  "movies": [
    {{"title": "", "description": "", "why": ""}}
  ],
  "songs": [
    {{"title": "", "artist": "", "description": "", "why": ""}}
  ],
  "books": [
    {{"title": "", "author": "", "description": "", "why": ""}}
  ],
  "blogs": [
    {{"title": "", "description": "", "why": ""}}
  ]
}}

Rules:
- Exactly 3 items per category
- Keep responses short and meaningful
- Ensure emotional alignment with mood
"""


def parse_ai_response(text):
    """Robust JSON extraction"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
    return None


def get_cache_key(mood, topic):
    return f"{mood.lower()}_{topic.lower() if topic else 'none'}"


# ----------------------------
# ROUTES
# ----------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    if not client:
         return jsonify({'error': 'Server configuration error: GROQ_API_KEY missing'}), 500
         
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid or missing JSON payload'}), 400

        mood = data.get('mood', '')
        if isinstance(mood, str):
            mood = mood.strip()
            
        topic = data.get('topic', '')
        if isinstance(topic, str):
            topic = topic.strip()

        # Validate input
        valid, error = validate_input(mood, topic)
        if not valid:
            return jsonify({'error': error}), 400

        cache_key = get_cache_key(mood, topic)

        # ----------------------------
        # CACHE CHECK
        # ----------------------------
        if cache_key in CACHE:
            return jsonify({
                "cached": True,
                "mood": mood,
                "topic": topic,
                "recommendations": CACHE[cache_key]
            })

        # ----------------------------
        # AI CALL
        # ----------------------------
        prompt = build_prompt(mood, topic)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a world-class personalized recommendation AI. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        ai_text = response.choices[0].message.content.strip()
        print("RAW AI RESPONSE:\n", ai_text)

        recommendations = parse_ai_response(ai_text)

        if not recommendations:
            return jsonify({
                "error": "Failed to parse AI response",
                "raw_response": ai_text
            }), 500

        # ----------------------------
        # STORE CACHE
        # ----------------------------
        CACHE[cache_key] = recommendations

        return jsonify({
            "cached": False,
            "timestamp": datetime.now().isoformat(),
            "mood": mood,
            "topic": topic,
            "recommendations": recommendations
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({'error': 'Internal server error'}), 500


# ----------------------------
# HEALTH CHECK (NEW)
# ----------------------------
@app.route('/health')
def health():
    return jsonify({
        "status": "active",
        "service": "Mood Recommender API"
    })


# ----------------------------
# RUN APP
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True)