# ai_voice_assistant.py - Conversational AI Voice Engine for Sahayak
# Supports ChatGPT (OpenAI API), Gemini API, and smart heuristic multilingual extraction.
# Handles any trade/work in English, Hindi, Telugu, and Hinglish.

import os
import json
import re

SYSTEM_PROMPT = (
    'You are Sahayak, an empathetic conversational voice assistant that helps informal workers, '
    'daily wage laborers, and contractors in India create wage protection agreements. '
    'You support ANY job or trade without limitation: masonry, carpentry, welding, plumbing, farming, '
    'domestic help, cooking, painting, tiling, driving, electrical, tailoring, security, '
    'loading, catering, roofing, auto repair, and many more. '
    'Extract these 12 fields from the conversation: '
    'owner_name, owner_phone, worker_name, worker_phone, work_description, work_location, '
    'start_date, duration, wage_amount, wage_unit, payment_schedule, late_penalty. '
    'wage_unit must be exactly one of: per day, per job, per month, per hour, per sq. ft. '
    'payment_schedule must be exactly one of: weekly, daily, on completion, installments. '
    'If user gives multiple details at once, extract them ALL at once. '
    'Respond in target language: en for English, hi for Hindi Devanagari, te for Telugu script. '
    'Keep replies short (1-2 sentences) as they will be read aloud over voice. '
    'Set is_complete to true when owner_name, worker_name, work_description, and wage_amount are all known. '
    'Return ONLY valid JSON: {"extracted_fields": {...}, "reply": "...", "is_complete": true/false, "missing_fields": [...]}'
)


def process_conversation_turn(user_message, conversation_history=None, current_state=None, lang='en'):
    if conversation_history is None:
        conversation_history = []
    if current_state is None:
        current_state = {}

    openai_key = os.environ.get('OPENAI_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')

    # Try Groq first since it is free, fast, and open source oriented
    if groq_key:
        try:
            return _call_groq(user_message, conversation_history, current_state, lang, groq_key)
        except Exception as e:
            print(f'[AI] Groq error: {e}, falling back...')

    if openai_key:
        try:
            return _call_openai(user_message, conversation_history, current_state, lang, openai_key)
        except Exception as e:
            print(f'[AI] OpenAI error: {e}, falling back...')

    if gemini_key:
        try:
            return _call_gemini(user_message, conversation_history, current_state, lang, gemini_key)
        except Exception as e:
            print(f'[AI] Gemini error: {e}, falling back...')

    return _fallback_nlp(user_message, conversation_history, current_state, lang)


def _call_groq(user_message, history, state, lang, api_key):
    import openai
    client = openai.OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )
    # Default to llama-3.3-70b-versatile for high quality, or llama3-8b-8192
    model = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'system', 'content': f'Target Language: {lang}. Current extracted fields: {json.dumps(state, ensure_ascii=False)}'}
    ]
    for t in history[-6:]:
        messages.append({'role': t.get('role', 'user'), 'content': t.get('content', '')})
    messages.append({'role': 'user', 'content': user_message})
    
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={'type': 'json_object'},
        temperature=0.3,
        max_tokens=500
    )
    return _merge(json.loads(resp.choices[0].message.content), state)


def _call_openai(user_message, history, state, lang, api_key):
    import openai
    client = openai.OpenAI(api_key=api_key)
    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'system', 'content': f'Target Language: {lang}. Current extracted fields: {json.dumps(state, ensure_ascii=False)}'}
    ]
    for t in history[-6:]:
        messages.append({'role': t.get('role', 'user'), 'content': t.get('content', '')})
    messages.append({'role': 'user', 'content': user_message})
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={'type': 'json_object'},
        temperature=0.3,
        max_tokens=500
    )
    return _merge(json.loads(resp.choices[0].message.content), state)


def _call_gemini(user_message, history, state, lang, api_key):
    import requests
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
    prompt_parts = [
        SYSTEM_PROMPT,
        f'Target Language: {lang}',
        f'Current State: {json.dumps(state, ensure_ascii=False)}'
    ]
    for t in history[-6:]:
        role = 'User' if t.get('role') == 'user' else 'Assistant'
        prompt_parts.append(f"{role}: {t.get('content', '')}")
    prompt_parts.append(f'User: {user_message}')
    prompt_parts.append('Return ONLY valid JSON.')
    payload = {
        'contents': [{'parts': [{'text': chr(10).join(prompt_parts)}]}],
        'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0.3}
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    raw = r.json()['candidates'][0]['content']['parts'][0]['text']
    return _merge(json.loads(raw), state)


def _merge(data, current_state):
    merged = dict(current_state or {})
    for k, v in data.get('extracted_fields', {}).items():
        if v and str(v).strip().lower() not in ['null', 'none', '']:
            merged[k] = str(v).strip()
    req_fields = ['owner_name', 'worker_name', 'work_description', 'wage_amount']
    missing = [f for f in req_fields if not merged.get(f)]
    return {
        'extracted_fields': merged,
        'reply': data.get('reply', 'Details noted.'),
        'is_complete': data.get('is_complete', len(missing) == 0),
        'missing_fields': missing
    }


def _fallback_nlp(user_message, history, current_state, lang):
    msg = user_message.strip()
    low = msg.lower()
    s = dict(current_state or {})

    # Phone numbers
    phones = re.findall(r'(?:\+91[\-\s]?)?[6-9]\d{9}', msg)
    if phones:
        if not s.get('owner_phone'):
            s['owner_phone'] = phones[0]
        elif len(phones) > 1 and not s.get('worker_phone'):
            s['worker_phone'] = phones[1]
        elif not s.get('worker_phone') and phones[0] != s.get('owner_phone'):
            s['worker_phone'] = phones[0]

    # Wage amount
    wm = re.search(r'(\d{3,6})', low)
    if wm and not s.get('wage_amount'):
        s['wage_amount'] = wm.group(1)

    # Wage unit
    if any(w in low for w in ['per day', 'daily', 'pratidin', 'roz', 'rozana']):
        s['wage_unit'] = 'per day'
    elif any(w in low for w in ['per month', 'monthly', 'mahine']):
        s['wage_unit'] = 'per month'
    elif any(w in low for w in ['per job', 'theka', 'fixed', 'lump']):
        s['wage_unit'] = 'per job'
    elif any(w in low for w in ['per hour', 'hourly', 'ghanta']):
        s['wage_unit'] = 'per hour'
    elif any(w in low for w in ['sq ft', 'square feet', 'sqft']):
        s['wage_unit'] = 'per sq. ft.'

    # Payment schedule
    if any(w in low for w in ['weekly', 'week', 'saptah']):
        s['payment_schedule'] = 'weekly'
    elif any(w in low for w in ['completion', 'finish', 'khatam', 'done']):
        s['payment_schedule'] = 'on completion'
    elif any(w in low for w in ['installment', 'kist', 'kist']):
        s['payment_schedule'] = 'installments'

    # Duration
    dm = re.search(r'(\d+\s*(?:days?|months?|weeks?|din|mahine|hafte))', low)
    if dm and not s.get('duration'):
        s['duration'] = dm.group(1)

    # Location
    lm = re.search(r'(?:in|at|near|location|place|jagah)\s+([A-Za-z][A-Za-z\s]{2,25}?)(?:\s+for|\s+from|\.|,|$)', msg, re.IGNORECASE)
    if lm and not s.get('work_location'):
        s['work_location'] = lm.group(1).strip()

    # Trades - universal map
    trades_map = {
        'welding': 'Welding and metal fabrication work',
        'welder': 'Welding and metal fabrication work',
        'carpentry': 'Carpentry, woodwork, and furniture making',
        'carpenter': 'Carpentry and woodwork',
        'masonry': 'Brick masonry, plastering, and construction work',
        'mason': 'Brick masonry and plastering',
        'plumbing': 'Plumbing and pipe fitting work',
        'plumber': 'Plumbing and pipe repair',
        'painting': 'Wall painting and surface finishing',
        'painter': 'Wall painting and surface finishing',
        'electrical': 'Electrical wiring and fitting work',
        'electrician': 'Electrical wiring and appliance setup',
        'farming': 'Agricultural harvesting and farm labor',
        'harvesting': 'Crop harvesting and agricultural fieldwork',
        'domestic': 'Domestic cooking, cleaning, and housekeeping',
        'cooking': 'Cooking, food preparation, and kitchen work',
        'housekeeping': 'Housekeeping and cleaning work',
        'driving': 'Vehicle driving and transport service',
        'driver': 'Vehicle driving service',
        'tailoring': 'Garment stitching and tailoring work',
        'tailor': 'Garment stitching and tailoring',
        'tiling': 'Floor tile and marble laying work',
        'security': 'Security guarding and premises watch',
        'loading': 'Goods loading and unloading labor',
        'catering': 'Event catering and food service',
        'roofing': 'Roofing and waterproofing work',
        'construction': 'General construction labor',
        'repair': 'Repair and maintenance work',
    }
    for key, desc in trades_map.items():
        if key in low and not s.get('work_description'):
            s['work_description'] = desc
            break

    # If still no description, use full message if it looks descriptive
    if not s.get('work_description') and len(msg.split()) >= 3 and any(w in low for w in ['work', 'job', 'kaam', 'pani', 'pari']):
        s['work_description'] = msg

    # ── Name extraction heuristics (independent — all run on every message) ──

    skip_words = {'Hiring', 'Employing', 'Looking', 'Trying', 'Going', 'Working', 'The', 'A', 'An', 'And', 'I', 'Am'}

    # "my name is X" → owner_name (always checked first)
    my_name_m = re.search(r'(?:my name is)\s+([A-Z][a-z]+)', msg, re.IGNORECASE)
    if my_name_m and not s.get('owner_name'):
        candidate = my_name_m.group(1).strip().title()
        if candidate not in skip_words:
            s['owner_name'] = candidate

    # "I am X" (not followed by hiring/employing) → owner_name
    i_am_m = re.search(r'\b(?:i am|i\'m)\s+([A-Z][a-z]+)\b(?!\s*(?:hiring|employing|looking|a\s|an\s))', msg, re.IGNORECASE)
    if i_am_m and not s.get('owner_name'):
        candidate = i_am_m.group(1).strip().title()
        if candidate not in skip_words:
            s['owner_name'] = candidate

    # "I am hiring/employing X" → worker_name
    i_hiring_m = re.search(r'\b(?:i am|i\'m)\s+(?:hiring|employing)\s+\b([A-Z][a-z]+)\b', msg, re.IGNORECASE)
    if i_hiring_m and not s.get('worker_name'):
        s['worker_name'] = i_hiring_m.group(1).title()

    # "Mohan is hiring Ramesh" → owner=Mohan, worker=Ramesh (third-person)
    third_hiring_m = re.search(r'\b([A-Z][a-z]+)\b\s+(?:is\s+)?(?:hiring|employing)\s+\b([A-Z][a-z]+)\b', msg, re.IGNORECASE)
    if third_hiring_m:
        owner_cand = third_hiring_m.group(1).title()
        worker_cand = third_hiring_m.group(2).title()
        if owner_cand not in skip_words and not s.get('owner_name'):
            s['owner_name'] = owner_cand
        if worker_cand not in skip_words and not s.get('worker_name'):
            s['worker_name'] = worker_cand

    # ── worker name is X / kaargar ka naam X → worker_name
    wn_m = re.search(r'(?:worker(?:\'s)? name is|kaargar ka naam|मजदूर का नाम|కార్మికుడి పేరు)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', msg, re.IGNORECASE)
    if wn_m and not s.get('worker_name'):
        s['worker_name'] = wn_m.group(1).strip().title()

    # ── owner name is X / malik ka naam X → owner_name
    on_m = re.search(r'(?:owner(?:\'s)? name is|employer(?:\'s)? name is|malik ka naam|मालिक का नाम|యజమాని పేరు)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', msg, re.IGNORECASE)
    if on_m and not s.get('owner_name'):
        s['owner_name'] = on_m.group(1).strip().title()

    # ── Active Missing Field Direct-Answer Fallback Heuristic ──
    # If the user gives a short response (1-3 words) and we still haven't filled the
    # active missing field, assign the response directly to it.
    req_fields = ['owner_name', 'worker_name', 'work_description', 'wage_amount']
    prev_missing = [f for f in req_fields if not current_state.get(f)]
    
    if prev_missing and len(msg.split()) <= 3:
        active_field = prev_missing[0]
        # Only assign if the active field wasn't successfully extracted by standard rules above
        if not s.get(active_field):
            if active_field in ('owner_name', 'worker_name'):
                # Exclude basic conversational noise
                noise = {'hello', 'hi', 'yes', 'no', 'okay', 'ok', 'haan', 'हां', 'అవును'}
                if low not in noise:
                    s[active_field] = msg.strip().title()
            elif active_field == 'work_description':
                s[active_field] = msg.strip().capitalize()
            elif active_field == 'wage_amount':
                # If they say "thousand" or "eight hundred", we can clean it up
                num_only = re.sub(r'\D', '', low)
                if num_only:
                    s[active_field] = num_only
                else:
                    # Let them write custom text or ignore
                    pass

    missing = [f for f in req_fields if not s.get(f)]


    replies = {
        'owner_name': {
            'en': 'Hello! Please tell me the name of the employer or contractor.',
            'hi': 'नमस्ते! कृपया काम देने वाले मालिक या ठेकेदार का नाम बताएं।',
            'te': 'నమస్కారం! దయచేసి యజమాని లేదా కాంట్రాక్టర్ పేరు చెప్పండి.'
        },
        'worker_name': {
            'en': 'Got it! Now please tell me the name of the worker or artisan.',
            'hi': 'ठीक है! अब काम करने वाले कारीगर या मजदूर का नाम बताएं।',
            'te': 'సరే! ఇప్పుడు కార్మికుడు లేదా పని వాళ్ళ పేరు చెప్పండి.'
        },
        'work_description': {
            'en': 'What type of work is this? For example: welding, carpentry, masonry, farming, cooking, driving, painting, etc.',
            'hi': 'यह किस प्रकार का काम है? जैसे: वेल्डिंग, बढ़ई, चिनाई, खेती, खाना बनाना, ड्राइविंग, पेंटिंग आदि।',
            'te': 'ఇది ఏ రకమైన పని? ఉదాహరణకు: వెల్డింగ్, వడ్రంగి, తాపీ పని, వ్యవసాయం, వంట, డ్రైవింగ్, పెయింటింగ్ మొ.'
        },
        'wage_amount': {
            'en': 'What is the agreed wage in Rupees? And is it per day, per job, or per month?',
            'hi': 'तय मजदूरी कितने रुपये है? और यह प्रतिदिन है, पूरे काम के लिए है, या महीने के लिए?',
            'te': 'వేతనం ఎంత రూపాయలు? మరియు రోజువారీగా, మొత్తం పనికా, లేదా నెలవారీగా?'
        },
        'done': {
            'en': 'All details have been collected! Please review the agreement summary.',
            'hi': 'सभी आवश्यक जानकारी दर्ज कर ली गई है! कृपया अनुबंध की समीक्षा करें।',
            'te': 'అన్ని వివరాలు నమోదయ్యాయి! దయచేసి ఒప్పందాన్ని సమీక్షించండి.'
        }
    }

    if missing:
        key = missing[0]
        reply_map = replies.get(key, replies['done'])
        reply = reply_map.get(lang, reply_map['en'])
    else:
        reply = replies['done'].get(lang, replies['done']['en'])

    return {
        'extracted_fields': s,
        'reply': reply,
        'is_complete': len(missing) == 0,
        'missing_fields': missing
    }
