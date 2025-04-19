
from post_generator import fetch_reference, create_markdown, save_post
import os

input_file = "generated_prompts.txt"
if not os.path.exists(input_file):
    print(f"❌ Prompt file '{input_file}' not found.")
    exit(1)

with open(input_file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f.readlines()]

prompts = []
for line in lines:
    if line:
        split_idx = line.find(". ")
        if split_idx != -1:
            prompts.append(line[split_idx + 2:].strip())
        else:
            prompts.append(line)

print(f"📝 Found {len(prompts)} prompts...\n")

for i, topic in enumerate(prompts, 1):
    print(f"➡️  [{i}] Generating post for: {topic}")
    ref_title, ref_url, ref_body = fetch_reference(topic)
    file_slug, post_md = create_markdown(topic, ref_title, ref_url, ref_body)
    save_post(file_slug, post_md)
    print(f"✅ Saved as: posts/{file_slug}.md\n")

print("🎉 All blog posts generated!")
