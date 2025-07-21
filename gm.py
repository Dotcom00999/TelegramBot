from openai import OpenAI

client = OpenAI(api_key="")

resp = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "сколько стоит создание сайта?"}]
)

print(response.choices[0].message.content)