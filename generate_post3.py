import os
import re
import datetime
from openai import OpenAI
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def create_markdown(topic, reference_title, reference_url):
    today = datetime.date.today().isoformat()
    safe_title = re.sub(r'[^a-zA-Z0-9-]', '', topic.lower().replace(' ', '-'))
    dated_title = f"{today}-{safe_title}"

    messages = [
        {
            "role": "system",
            "content": "You are a professional blog writer. Write a 1000-word blog post using Harvard-style citations and structured headings. Start with the reference provided."
        },
        {
            "role": "user",
            "content": f"Write a blog post about '{topic}'. Begin with insights from: '{reference_title}'. Cite it in Harvard style. Include section headings and end with a References section."
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    content = response.choices[0].message.content

    front_matter = f"""---
title: "{topic}"
excerpt: "Auto-generated article on {topic} using GPT-4o"
publishDate: "{today}"
publish: true
categories: ["Artificial Intelligence", "Technology"]
seo:
  title: "{topic} - Auto Generated AI Post"
  description: "A deep dive into {topic} with up-to-date sources and citations."
---"""

    full_content = front_matter + "\n\n" + content + "\n\n---\n\n### References\n"
    if reference_title and reference_url:
        full_content += f"{reference_title} ({today[:4]}) *Accessed via DuckDuckGo*. Available at: <a href=\"{reference_url}\" target=\"_blank\" rel=\"noopener\">{reference_url}</a>\n"
    return dated_title, full_content

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
