import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import random
import datetime

# Load Bangla-BERT
MODEL_NAME = "sagorsarker/bangla-bert-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)

# Load intents.csv using an absolute path anchored to Django's BASE_DIR
# (M0: BUG-4) — bare "intents.csv" breaks when CWD ≠ project root
from django.conf import settings as _django_settings
_CSV_PATH = _django_settings.BASE_DIR / 'intents.csv'
data = pd.read_csv(_CSV_PATH)

intents = []
examples = []
responses = {}

# Parse CSV and collect examples
for _, row in data.iterrows():
    intent = row["intent"]
    # Handle missing values
    exs_raw = row.get("examples")
    res_raw = row.get("responses")
    if pd.isna(exs_raw) or pd.isna(res_raw):
        continue

    exs = [e.strip() for e in str(exs_raw).split(";")]
    resps = [r.strip() for r in str(res_raw).split(";")]

    intents.append(intent)
    examples.extend([(intent, e) for e in exs])
    responses[intent] = resps

# Function to get embedding
def get_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1)  # mean pooling
    return embeddings[0].numpy()

# Precompute embeddings for all examples
example_embeddings = [(intent, ex, get_embedding(ex)) for intent, ex in examples]

# Get response function
def get_response(user_input):
    user_emb = get_embedding(user_input)

    # Compute cosine similarity with all example embeddings
    sims = [(intent, cosine_similarity([user_emb], [emb])[0][0]) for intent, _, emb in example_embeddings]

    # Pick the best matching intent
    best_intent, best_score = max(sims, key=lambda x: x[1])
    
    print(f"Best intent: {best_intent} with score {best_score}")
    
    if best_intent == 'weather_query':
        return '__ASK_WEATHER__'

    # Threshold to handle unknown inputs
    if best_score < 0.60:
        return "দুঃখিত, আমি বুঝতে পারিনি 😔"

    response = random.choice(responses[best_intent])

    # Substitute template variables  (M0: CODE-5 — removed dead '# return response')
    now = datetime.datetime.now()
    response = response.replace("{current_time}", now.strftime("%I:%M %p"))
    response = response.replace("{current_date}", now.strftime("%d %B, %Y"))

    return response
