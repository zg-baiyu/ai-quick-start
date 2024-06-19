from openai import OpenAI

import dotenv

dotenv.load_dotenv()

# 构建一个消息列表
messages = [
    {"role": "system", "content": "你是一个帮助用户的助手。"},
    {"role": "user", "content": "用户请求讲一个笑话"},
    {"role": "assistant", "content": "助手讲了一个笑话作为回复。"},
    {"role": "user", "content": "用户要求再讲一个笑话"}
]

client = OpenAI(api_key="sk-pNUGu5XaAjINm3FwB68c821f6b514d488bB33c5009D43bE1", base_url="https://free.gpt.ge/v1/")
response = client.chat.completions.create(model="gpt-3.5-turbo-16k",
                                          messages=messages)
print(response)
