import os
import re
import datetime
import requests
from openai import OpenAI
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("OPENAI_PROJECT_ID", None),
    organization=os.getenv("OPENAI_ORG_ID", None)
)

# Keywords for category inference
category_keywords = {
    "llm": "LLMs",
    "language model": "LLMs",
    "chatgpt": "LLMs",
    "data": "Data",
    "analytics": "Data Science",
    "ethics": "Ethics",
    "compliance": "Compliance",
    "training": "Training",
    "education": "Training",
    "governance": "Compliance",
    "ai": "Artificial Intelligence",
    "artificial intelligence": "Artificial Intelligence",
    "business": "Business Strategy",
    "strategy": "Business Strategy",
}

def infer_categories_from_topic(topic, max_categories=3):
    topic_lower = topic.lower()
    matched = set()
    for keyword, category in category_keywords.items():
        if keyword in topic_lower:
            matched.add(category)
    return list(matched)[:max_categories] if matched else ["Artificial Intelligence", "Technology"]

def get_topic_input():
    return input("Enter blog topic: ")

def fetch_reference(topic):
    academic_sites = [
        "mckinsey.com", "forbes.com", "pwc.com", "wired.com",
        "harvard.edu", "mit.edu", "stanford.edu", "berkeley.edu", "ox.ac.uk", "cam.ac.uk",
        "whitehouse.gov", "brookings.edu", "nih.gov", "nsf.gov", "ed.gov", "usda.gov", "hbr.org",
        "ec.europa.eu", "ema.europa.eu", "efsa.europa.eu", "euractiv.com", "oecd.org", "nature.com", "sciencebusiness.net"
    ]
    search_string = topic + " " + " OR ".join([f"site:{s}" for s in academic_sites])
    with DDGS() as ddgs:
        results = list(ddgs.text(search_string, max_results=1))
        if results:
            return results[0]["title"], results[0]["href"], results[0]["body"]
    return None, None, None

def create_image(prompt, filename):
    try:
        print(f"[INFO] Generating image with DALL·E 3...")
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
        print(f"✅ Image saved to images/{filename}")
    except Exception as e:
        print(f"❌ Image generation failed: {e}")

def create_markdown(topic, reference_title, reference_url, ref_body):
    today = datetime.date.today().isoformat()
    safe_title = re.sub(r'[^a-zA-Z0-9-]', '', topic.lower().replace(' ', '-'))
    dated_title = f"{today}-{safe_title}"
    image_file = f"{dated_title}.jpg"

    # Generate image
    image_prompt = f"A realistic, landscape-format stock photo representing: {topic}"
    create_image(image_prompt, image_file)

    # Blog content prompt
    prompt = f"""
Write a structured blog post about "{topic}" using the following format:

## Background
- ~250 words
- Critically introduce the topic and evaluate this source: "{reference_title}" ({reference_url})

## Topic
- Discuss challenges, key developments, and sector-specific insights

## Conclusion
- Select 1 or 2 of the following services that are most relevant to the topic:
  - AI Implementation
  - Data Governance
  - Regulatory Compliance
  - Data Analytics Projects
  - Capacity Building & Training
  - Predictive Modelling & Forecasting
- Explain how they help address the issue, with critical insight

Only include a maximum of 3 citations in the entire article.
Use Harvard-style references. Return only markdown content.
"""

    messages = [
        {"role": "system", "content": "You are a professional blog writer creating structured, insightful, and critical blog posts with Harvard-style citations."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    body = response.choices[0].message.content.strip()

    # ✨ Generate excerpt from body content
    excerpt_prompt = f"""
Write a clever, enticing, and concise excerpt (max 25 words) for a blog post based on the following content:

\"\"\"{body}\"\"\"
"""

    excerpt_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional blog writer. Your task is to generate short, smart excerpts for busy professionals."},
            {"role": "user", "content": excerpt_prompt}
        ],
        temperature=0.7
    )

    excerpt = excerpt_response.choices[0].message.content.strip().replace('"', '').replace('\n', ' ')

    # Generate categories
    categories = infer_categories_from_topic(topic)

    # Final front matter
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

    # Append a fallback Harvard-style citation if GPT doesn't include one
    if "### References" not in body and "## References" not in body:
        access_date = datetime.date.today().strftime("%d %B %Y")
        year_match = re.search(r'\b(20\d{2})\b', ref_body or "")
        pub_year = year_match.group(1) if year_match else today[:4]
        domain = re.findall(r"https?://(?:www\.)?([^/]+)", reference_url or "")
        author = domain[0].split('.')[0].capitalize() if domain else "Source"
        formatted_ref = f"""

---\n\n### References

{author}, {pub_year}. {reference_title}. [online] Available at: {reference_url}. [Accessed {access_date}]
"""
        body += formatted_ref

    return dated_title, front_matter + "\n\n" + body

def save_post(filename, content):
    os.makedirs("posts", exist_ok=True)
    with open(f"posts/{filename}.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    topic = get_topic_input()
    ref_title, ref_url, ref_body = fetch_reference(topic)
    file_slug, post_md = create_markdown(topic, ref_title, ref_url, ref_body)
    save_post(file_slug, post_md)
    print(f"✅ Blog post saved as posts/{file_slug}.md")
