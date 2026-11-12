from dotenv import load_dotenv
import anthropic

load_dotenv()  # reads the keys from .env

client = anthropic.Anthropic()  # finds ANTHROPIC_API_KEY automatically
response = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=50,
    messages=[{"role": "user", "content": "Reply with exactly: key works"}],
)
print(response.content[0].text)