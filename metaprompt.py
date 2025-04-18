import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("OPENAI_PROJECT_ID", None),
    organization=os.getenv("OPENAI_ORG_ID", None)
)

# Read the meta-prompt from file
prompt_file = "topics_prompt.txt"
print(f"📄 Reading prompt from '{prompt_file}'...")
with open(prompt_file, "r", encoding="utf-8") as f:
    prompt = f.read().strip()

if not prompt:
    print("❌ Prompt file is empty. Please add a valid meta-prompt to 'topics_prompt.txt'.")
    exit(1)

print("✅ Meta-prompt loaded successfully.")

# Send prompt to GPT-4o
print("🤖 Sending request to GPT-4o...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant generating high-quality blog topic prompts."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7
)

# Extract response content
result = response.choices[0].message.content.strip()

# Determine output file name
base_filename = "generated_prompts.txt"
if not os.path.exists(base_filename):
    output_file = base_filename
else:
    i = 1
    while True:
        candidate = f"generated_prompts.{i}.txt"
        if not os.path.exists(candidate):
            output_file = candidate
            break
        i += 1

# Write to output file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(result)

print(f"✅ Blog prompt list saved to: {output_file}")
