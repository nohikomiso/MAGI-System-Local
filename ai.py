import os
import sys
import typing

# Python 3.14 workaround for pydantic < 2.14
if sys.version_info >= (3, 14):
    if hasattr(typing, "_eval_type"):
        original_eval_type = typing._eval_type
        def patched_eval_type(*args, **kwargs):
            kwargs.pop("prefer_fwd_module", None)
            return original_eval_type(*args, **kwargs)
        typing._eval_type = patched_eval_type

from openai import OpenAI

LOCAL_SERVER_URL = "http://192.168.0.152:8080/v1"
client = OpenAI(api_key="no-key-required", base_url=LOCAL_SERVER_URL)

def is_yes_or_no_question(query):
    response = client.chat.completions.create(
        model="gemma-2-9b-it",
        messages=[
            {"role": "system", "content": "You are a logical processor. Determine if the given input is a yes/no question or a query requiring a verdict. Respond with ONLY 'true' or 'false'."},
            {"role": "user", "content": query}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content.strip().lower() == 'true'

def get_answer(query, personality):
    response = client.chat.completions.create(
        model="gemma-2-9b-it",
        messages=[
            {"role": "system", "content": f"{personality}\nRespond in Japanese. Be concise but maintain your personality."},
            {"role": "user", "content": query}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def classify_answer(query, personality, answer):
    response = client.chat.completions.create(
        model="gemma-2-9b-it",
        messages=[
            {"role": "system", "content": f"{personality}\nClassify your own answer to the query. Respond with 'yes', 'no', or 'conditional' followed by a short reason in Japanese, in the format: STATUS: [yes/no/conditional] REASON: [reason]"},
            {"role": "user", "content": f"Query: {query}\nYour Answer: {answer}"}
        ],
        temperature=0.0
    )
    content = response.choices[0].message.content.strip()
    status = 'info'
    if 'STATUS: yes' in content: status = 'yes'
    elif 'STATUS: no' in content: status = 'no'
    elif 'STATUS: conditional' in content: status = 'conditional'
    
    reason = content.split('REASON:')[-1].strip() if 'REASON:' in content else None
    return {'status': status, 'conditions': reason}

def summarize_consensus(query, answers):
    answers_text = "\n".join([f"{name}: {text}" for name, text in answers.items()])
    response = client.chat.completions.create(
        model="gemma-2-9b-it",
        messages=[
            {"role": "system", "content": "あなたはMAGIシステムの最終審判を司るAIです。3人の賢者（メルキオール、バルタザール、カスパー）の回答を統合し、権威ある日本語の要約を作成してください。結論を明確にし、箇条書きを活用して簡潔にまとめてください。"},
            {"role": "user", "content": f"質問: {query}\n\n各賢者の回答:\n{answers_text}"}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()
