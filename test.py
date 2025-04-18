import os
import requests
from openai import OpenAI

# You can use os.getenv if you're confident in your .env setup
client = OpenAI(api_key="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")

prompt = "A small business owner analyzing data charts on a laptop, in a cozy office, realistic stock photo style"

try:
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",  # 1792x1024 is also fine
        quality="standard",
        response_format="url",
        n=1
    )

    image_url = response.data[0].url
    print("✅ Image URL:", image_url)

    # Save image
    image_data = requests.get(image_url).content
    with open("test_output.jpg", "wb") as f:
        f.write(image_data)
    print("✅ Image saved as test_output.jpg")

except Exception as e:
    print("❌ Error:", e)