import os
import requests
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

def fetch_reference_from_perplexity(topic):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    query = f"Find a high-quality, cited source on the topic: {topic}. Return one recent, reputable source with title, link, and short summary."

    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are a researcher who returns one high-quality source (title, url, snippet) for a given topic, based on reputable academic, government, or industry websites."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        lines = content.strip().splitlines()
        title = lines[0].strip()
        url = ""
        snippet = ""

        for line in lines[1:]:
            if "http" in line:
                url = line.strip()
            elif not snippet and line.strip():
                snippet = line.strip()

        if not url:
            url = "https://www.perplexity.ai"

        if not title:
            title = f"Reference for {topic}"

        if not snippet:
            snippet = "No snippet available from Perplexity."

        return title, url, snippet

    except Exception as e:
        print(f"❌ Perplexity API failed: {e}")
        return f"Placeholder Source for '{topic}'", "https://example.com", "No reference found."
