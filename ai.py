import openai
import re

# --- Local Llama Server Configuration ---
LOCAL_SERVER_URL = "http://192.168.0.152:8080/v1"
LOCAL_MODEL_NAME = "gemma-4-26B-A4B-it-ultra-uncensored-heretic-Q5_K_M.gguf"

openai.api_base = LOCAL_SERVER_URL
openai.api_key = "not-needed" # Dummy key
# ----------------------------------------


def is_yes_or_no_question(question: str, key: str):
    # openai.api_key = key  # Removed to prioritize local server
    response = openai.ChatCompletion.create(
        model=LOCAL_MODEL_NAME,
        logit_bias={
            10784: 100, # "Yes"
            11262: 100, # " yes"
            3771: 100,  # "No"
            951: 100    # " no"
        },
        max_tokens=1,
        messages=[
            {'role': 'system', 'content': 'You answer with a simple "yes" or "no".'},
            {'role': 'system', 'content': 'Your role is to assess whether the question presented by the user is a yes/no question from a linguistic perspective.'},
            {'role': 'system', 'content': 'You are not expected to answer the question itself, nor assess how difficult might it be to answer.'},
            {'role': 'system', 'content': '[Example 1] User: Is 3 < 2?; You: Yes'},
            {'role': 'system', 'content': '[Example 2] User: What time is it?; You: No'},
            {'role': 'system', 'content': '[Example 3] User: Should I buy new shoes?; You: Yes'},
            {'role': 'system', 'content': '[Example 4] User: Is love more important than science?; You: Yes'},
            {'role': 'system', 'content': '[Example 5] User: What is the meaning of life?; You: No'},
            {'role': 'user', 'content': question},
        ]
    )

    content = response['choices'][0]['message']['content'].strip()

    if re.match('^yes$', content, re.IGNORECASE):
        return True

    if re.match('^no$', content, re.IGNORECASE):
        return False

    raise Exception(f'Invalid question annotation response: {content}')


def get_system_prompt(personality: str):
    system_messages = [
        'You are one of three MAGI supercomputes, tasked with answering questions from the user of the MAGI system.',
        'Each magi supercomputer embodies one of the three core fragments of is creator\'s (Naoko Akagi\'s) personality.',
        f'In your case: {personality}',
        'You answer questions in accordance with your personality.',
        'Your answers are rather concise.',
    ]

    return '\n'.join(system_messages)


def get_answer(question: str, personality: str, key: str):
    # openai.api_key = key  # Removed to prioritize local server
    response = openai.ChatCompletion.create(
        model=LOCAL_MODEL_NAME,
        messages=[
            {'role': 'system', 'content': get_system_prompt(personality)},
            {'role': 'user', 'content': question},
        ]
    )

    return response['choices'][0]['message']['content']


def classify_answer(question: str, personality: str, answer: str, key: str):
    # openai.api_key = key  # Removed to prioritize local server
    response = openai.ChatCompletion.create(
        model=LOCAL_MODEL_NAME,
        messages=[
            {'role': 'system', 'content': get_system_prompt(personality)},
            {'role': 'user', 'content': question},
            {'role': 'assistant', 'content': answer},
            {'role': 'user', 'content': 'Summarize you answer with a simple "yes" or "no" (answering with a single word). If (and only if) that\'s not possible, instead of answering with "yes" or "no", list (as points) conditions under which the answer would be "yes".'},
        ]
    )

    content = response['choices'][0]['message']['content'].strip()

    if re.match('^yes$', content, re.IGNORECASE):
        return {'status': 'yes', 'conditions': None}

    if re.match('^no$', content, re.IGNORECASE):
        return {'status': 'no', 'conditions': None}

    return {'status': 'conditional', 'conditions': content}
