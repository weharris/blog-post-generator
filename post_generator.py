import os
import re
import time
import datetime
import requests
from openai import OpenAI
from dotenv import load_dotenv
from perplexity_reference import fetch_reference_from_perplexity as fetch_reference

# Load environment variables
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("OPENAI_PROJECT_ID", None),
    organization=os.getenv("OPENAI_ORG_ID", None)
)

category_keywords = {
    "llm": "LLMs",
    "language model": "LLMs",
    "chatgpt": "LLMs",
    
    "data": "Data",
    "data science": "Data Science",
    "analytics": "Analytics",
    
    "ethics": "Ethics",
    
    "compliance": "Compliance",
    "governance": "Compliance",
    
    "training": "Training",
    "education": "Education",
    
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    
    "business": "Business Strategy",
    "strategy": "Business Strategy",
    
    "agriculture": "Agriculture",
    "farming": "Agriculture",
    "agtech": "Agriculture",
    
    "biopharma": "Biopharma",
    "pharmaceutical": "Biopharma",
    "biotech": "Biopharma",
    
    "healthcare": "Healthcare"
}

def infer_categories_from_topic(topic, max_categories=3):
    topic_lower = topic.lower()
    matched = set()
    for keyword, category in category_keywords.items():
        if keyword in topic_lower:
            matched.add(category)
    return list(matched)[:max_categories] if matched else ["Artificial Intelligence", "Technology"]

def create_image(prompt, filename):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            response_format="url",
            n=1
        )
        img_url = response.data[0].url
        img_data = requests.get(img_url).content
        os.makedirs("images", exist_ok=True)
        with open(f"images/{filename}", 'wb') as handler:
            handler.write(img_data)
    except Exception as e:
        print(f"[Image generation failed] {e}")

def clean_references(text):
    # Remove leading bullets or symbols
    text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.MULTILINE)
    # Remove [Accessed ...] citations
    text = re.sub(r"\[Accessed.*?\]", "", text)
    # Remove extra newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def create_markdown(topic, reference_title, reference_url, ref_body):
    today = datetime.date.today().isoformat()
    safe_title = re.sub(r'[^a-zA-Z0-9-]', '', topic.lower().replace(' ', '-'))
    dated_title = f"{today}-{safe_title}"
    image_file = f"{dated_title}.jpg"

    create_image(f"A realistic, landscape-format stock photo representing: {topic}", image_file)

    prompt = f"""Write a structured blog post about "{topic}" using this format:

## Background
~250 words, critically introduce the topic and evaluate this source: "{reference_title}" ({reference_url})

## Challenges and Developments
Key challenges, context, developments. Use examples.

## Conclusion
Pick 1–2 relevant services below and explain how they help:
- AI Implementation
- Data Governance
- Regulatory Compliance
- Data Analytics Projects
- Capacity Building & Training
- Predictive Modelling & Forecasting

Use max 3 citations. Use Harvard-style referencing. Do not use bullet points. No accessed date. Do not include [Accessed ...] in references. Return only markdown content.
"""

    messages = [
        {"role": "system", "content": "You are a professional blog writer creating structured, insightful blog posts with consistent Harvard-style citations."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    body = response.choices[0].message.content.strip()

    # Generate excerpt
    excerpt_prompt = f"""Write a clever, enticing excerpt (max 25 words) for this blog post:

\"\"\"{body}\"\"\"
"""
    excerpt_resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write compelling blog excerpts."},
            {"role": "user", "content": excerpt_prompt}
        ]
    )
    excerpt = excerpt_resp.choices[0].message.content.strip().replace('"', '')

    categories = infer_categories_from_topic(topic)

    front_matter = f"""---
title: "{topic}"
excerpt: "{excerpt}"
featuredImage: "./images/{image_file}"
publishDate: "{today}"
publish: true
categories: {categories}

seo:
  title: "{topic} - Policy and Innovation"
  description: "Explore {topic} through a critical lens, with action-oriented recommendations."
---"""

    # Smarter reference detection using regex
    reference_exists = re.search(r"(?i)(#+\s*references|\*\*references\*\*)", body)

    if not reference_exists:
        year_match = re.search(r'\b(20\d{2})\b', ref_body or "")
        pub_year = year_match.group(1) if year_match else today[:4]
        domain = re.findall(r"https?://(?:www\.)?([^/]+)", reference_url or "")
        author = domain[0].split('.')[0].capitalize() if domain else "Source"
        formatted_ref = f"""

---

## References

{author}, {pub_year}. {reference_title}. *Source*. Available at: <{reference_url}>.
"""
        body += formatted_ref

    # Clean reference block formatting
    body = clean_references(body)

    return dated_title, front_matter + "\n\n" + body

def save_post(filename, content):
    os.makedirs("posts", exist_ok=True)
    with open(f"posts/{filename}.md", "w", encoding="utf-8") as f:
        f.write(content)
