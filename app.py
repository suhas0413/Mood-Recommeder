from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        mood = data.get('mood')
        topic = data.get('topic', '')

        if not mood:
            return jsonify({'error': 'Mood is required!'}), 400

        # Prompt for AI
        prompt = f"""
        You are a mood-based content recommender.
        Based on the mood "{mood}" and topic "{topic}", recommend:

        - 3 Movies (title, short description, why it fits)
        - 3 Songs (title, artist, description, why it fits)
        - 3 Books (title, author, description, why it fits)
        - 3 Blog topics or articles (title, description, why it fits)

        Return your answer strictly in JSON format with this structure:
        {{
          "movies": [{{"title": "", "description": "", "why": ""}}],
          "songs": [{{"title": "", "artist": "", "description": "", "why": ""}}],
          "books": [{{"title": "", "author": "", "description": "", "why": ""}}],
          "blogs": [{{"title": "", "description": "", "why": ""}}]
        }}
        """

        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert AI recommender system."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )

        ai_text = response.choices[0].message.content.strip()
        print("Raw AI Response:", ai_text)  # Debug: see what Groq returned

        # Robust JSON parsing
        try:
            recommendations = json.loads(ai_text)
        except json.JSONDecodeError:
            # Try to extract JSON using regex
            match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if match:
                recommendations = json.loads(match.group())
            else:
                return jsonify({
                    'error': 'Failed to parse JSON from Groq response',
                    'raw_response': ai_text
                }), 500

        return jsonify({
            'mood': mood,
            'topic': topic,
            'recommendations': recommendations
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
