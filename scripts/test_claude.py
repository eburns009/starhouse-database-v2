import os
from anthropic import Anthropic

api = os.environ.get("ANTHROPIC_API_KEY")
if not api:
    raise SystemExit("Set ANTHROPIC_API_KEY first.")

client = Anthropic(api_key=api)
msg = client.messages.create(
    model="claude-3-5-sonnet-latest",
    max_tokens=200,
    messages=[{"role":"user","content":"Say hello from inside GitHub Codespaces!"}]
)
for b in msg.content:
    if b.type == "text":
        print(b.text)


        
