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
    project=os.getenv("OPENAI_PROJECT_ID"),
    organization=os.getenv("OPENAI_ORG_ID")
)

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

def create_markdown(topic, reference_title, reference_url):
    today = datetime.date.today().isoformat()
    safe_title = re.sub(r'[^a-zA-Z0-9-]', '', topic.lower().replace(' ', '-'))
    dated_title = f"{today}-{safe_title}"
    image_file = f"{dated_title}.jpg"

    # Generate image
    image_prompt = f"A photo-realistic landscape-format stock-style image representing: {topic}"
    create_image(image_prompt, image_file)

    # Structured blog writing prompt
    prompt = f"""
Write a structured blog post about "{topic}" using the following format:

## Background
- ~250 words
- Critically introduce the topic
- Reference this source early: "{reference_title}" ({reference_url})

## Challenges
- ~100-150 words
- Discuss key challenges, context, developments
- Use examples if helpful

## Conclusion
- Wrap up with 1 or 2 relevant services (e.g., AI Implementation, Data Governance, Predictive Modelling)
- Be insightful, not generic

Use Harvard-style citation. Only return markdown content, no YAML or extra formatting.
"""

    messages = [
        {"role": "system", "content": "You are a professional business and data science expert focused on structured, insightful long-form posts with Harvard citations. The tone should be that of an expert analyst writing for an informed audience"},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    body = response.choices[0].message.content.strip()

    front_matter = f"""---
title: "{topic}"
excerpt: "Structured article on {topic}, critically engaging with current trends and grounded in academic or policy reference."
featuredImage: "./images/{image_file}"
publishDate: "{today}"
publish: true
categories: ["Artificial Intelligence", "Technology"]

seo:
  title: "{topic} - Policy and Innovation"
  description: "Explore {topic} through a critical lens, with action-oriented recommendations."
---"""

    # Only append our reference if GPT didn't already include a References section
    if "### References" not in body:
        body += f"""

---\n\n### References

{reference_title} ({today[:4]}) *Accessed via DuckDuckGo*. Available at: <a href="{reference_url}" target="_blank" rel="noopener">{reference_url}</a>
"""

    return dated_title, front_matter + "\n\n" + body

def save_post(filename, content):
    os.makedirs("posts", exist_ok=True)
    with open(f"posts/{filename}.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    topic = get_topic_input()
    ref_title, ref_url, ref_body = fetch_reference(topic)
    file_slug, post_md = create_markdown(topic, ref_title, ref_url)
    save_post(file_slug, post_md)
    print(f"✅ Blog post saved as posts/{file_slug}.md")
