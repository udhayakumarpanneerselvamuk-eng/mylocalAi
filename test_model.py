import ollama

print("Checking Ollama...")

models = ollama.list()

for model in models.models:
    print("Available model:", model.model)

response = ollama.chat(
    model="qwen2.5:0.5b",
    messages=[
        {
            "role": "user",
            "content": "Hello! Are you working?"
        }
    ]
)

print("\nAI Response:")
print(response.message.content)