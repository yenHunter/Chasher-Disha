# Chasher-Disha (চাষের দিশা): Bangla NLP Chatbot 🤖

[![Python](https://img.shields.io/badge/python-3.14-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2.7-green)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

A Bengali language chatbot built with **Django** and **Bangla-BERT embeddings**, capable of understanding natural Bangla input and responding intelligently. Users can interact through a web-based frontend.

## Features

- Semantic understanding using **Bangla-BERT** (`sagorsarker/bangla-bert-base`)
- Handles multiple Bangla variations for the same intent
- Live chat interface with AJAX frontend
- Easy to extend by updating `intents.csv`
- Fallback response for unknown queries
- CPU-friendly for VPS or local development

## Demo

![Chatbot Demo](https://via.placeholder.com/600x400.png?text=Chatbot+Demo+Placeholder)

- Type a message in Bangla in the chat box.
- Bot responds using semantic understanding.
- Example inputs:
  - "তুমি কে"
  - "হ্যালো"
  - "আজকের আবহাওয়া কেমন"


## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yenHunter/Chasher-Disha.git
cd Chasher-Disha
````

2. **Create a virtual environment**

```bash
python -m venv env
source env/bin/activate       # Linux/Mac
env\Scripts\activate          # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run the server**

```bash
python manage.py runserver
```

5. **Open in browser**

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) to chat with the bot.

## Usage

* Type Bangla messages in the chat box.
* Bot will reply based on semantic similarity.
* Add more phrases or responses in `intents.csv` to expand capabilities.

## Customization

* Each intent in `intents.csv` has:

  * `intent`: unique name
  * `examples`: semicolon-separated example phrases
  * `responses`: semicolon-separated responses
* The chatbot automatically computes embeddings for all examples.

## License

MIT License

This version includes:

- Python & Django badges  
- Placeholder for **demo GIF or image**  
- Clear sections for Features, Installation, Usage, and Customization

# About me
I’m a passionate web developer with experience in building scalable and secure applications. I specialize in Laravel, Django, JavaScript and server management with Nginx. I enjoy automating workflows, optimizing performance, and deploying modern web solutions on VPS environments. I believe in clean code, continuous learning, and sharing knowledge through open-source contributions.

## Connect & Support

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/firoz-ebna-jobaier)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_a_Coffee-Support-yellow?style=for-the-badge&logo=buymeacoffee)](buymeacoffee.com/yenHunter)
[![Fork me on GitHub](https://img.shields.io/badge/Fork_on_GitHub-000?style=for-the-badge&logo=github)](https://github.com/yenHunter)