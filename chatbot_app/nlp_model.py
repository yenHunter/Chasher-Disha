import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import os

# Load training data from CSV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'intents.csv')

data = pd.read_csv(DATA_PATH)

# Prepare data
X_train = data['text']
y_train = data['intent']

# Train model
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(X_train)
model = MultinomialNB()
model.fit(X, y_train)

# Responses (you can expand this)
RESPONSES = {
    "greet": "হ্যালো! কেমন আছেন?",
    "thanks": "আপনাকেও ধন্যবাদ 😊",
    "ask_name": "আমার নাম বাংলা বট 🤖",
    "bye": "বিদায়! আবার দেখা হবে 👋",
    "ask_activity": "আমি এখন তোমার সঙ্গে কথা বলছি 🙂",
}

def get_response(text):
    if not text.strip():
        return "কিছু লিখুন দয়া করে 🙂"

    X_test = vectorizer.transform([text])
    intent = model.predict(X_test)[0]
    return RESPONSES.get(intent, "দুঃখিত, আমি সেটা বুঝতে পারিনি 😅")
