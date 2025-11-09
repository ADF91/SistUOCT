import re
import json
from datetime import datetime

def clean_ansi(text):
    ansi_escape = re.compile(r'''
        \x1B[@-_][0-?]*[ -/]*[@-~]
        | \x1B\[[0-?]*[ -/]*[@-~]
        | [\x7F-\x9F]
    ''', re.VERBOSE)
    return ansi_escape.sub('', text)

def log_api_message(data):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = clean_ansi(value)
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    print(f"[{current_time}] Enviando mensaje JSON a la API:\n{json_data}\n")
