# build_perfect_prototype.py
import re
import json
import os
import sys

# Add the project dir to path so we can import translations
sys.path.append(r'C:\Users\Rohit\.gemini\antigravity\scratch\sahayak')
from translations import TRANSLATIONS

def build():
    proj_dir = r'C:\Users\Rohit\.gemini\antigravity\scratch\sahayak'
    
    # 1. Read base.html and extract container wrapper
    with open(os.path.join(proj_dir, 'templates/base.html'), 'r', encoding='utf-8') as f:
        base_html = f.read()

    # 2. Read index.html content
    with open(os.path.join(proj_dir, 'templates/index.html'), 'r', encoding='utf-8') as f:
        index_html = f.read()

    # 3. Read style.css content
    with open(os.path.join(proj_dir, 'static/css/style.css'), 'r', encoding='utf-8') as f:
        style_css = f.read()

    # Merge index.html content into base.html at {% block content %}{% endblock %}
    content_match = re.search(r'{% block content %}(.*?){% endblock %}', index_html, re.DOTALL)
    if content_match:
        content_body = content_match.group(1)
    else:
        content_body = index_html

    full_html = base_html.replace('{% block content %}{% endblock %}', content_body)
    full_html = re.sub(r'{% block title %}.*?{% endblock %}', '<title>Sahayak Wage Agreement Prototype</title>', full_html)
    full_html = re.sub(r'<link rel="stylesheet" href=".*?">', f'<style>\n{style_css}\n</style>', full_html)

    # 4. Inject Translation JS helper
    translations_json = json.dumps(TRANSLATIONS, ensure_ascii=False)

    translation_script = f"""
    <script>
    const translations = {translations_json};
    let currentLang = 'en';

    function setLanguage(lang) {{
        currentLang = lang;
        document.documentElement.lang = lang;
        
        // Translate all elements with data-t attribute
        document.querySelectorAll('[data-t]').forEach(el => {{
            const key = el.getAttribute('data-t');
            if (translations[lang] && translations[lang][key]) {{
                el.innerHTML = translations[lang][key];
            }}
        }});
        
        // Translate inputs with data-t-ph (placeholder) attribute
        document.querySelectorAll('[data-t-ph]').forEach(el => {{
            const key = el.getAttribute('data-t-ph');
            if (translations[lang] && translations[lang][key]) {{
                el.placeholder = translations[lang][key];
            }}
        }});

        // Set active button style in language switcher
        document.querySelectorAll('.lang-btn').forEach(btn => {{
            if (btn.getAttribute('data-lang') === lang) {{
                btn.classList.add('active');
            }} else {{
                btn.classList.remove('active');
            }}
        }});

        // Trigger updates in lists or internal arrays if needed
        if (typeof VOICE_QUESTIONS !== 'undefined') {{
             currentQuestions = VOICE_QUESTIONS[lang] || VOICE_QUESTIONS.en;
        }}
    }}
    </script>
    """

    # Replace normal text tags
    def replace_tag(match):
        key = match.group(1)
        fallback = TRANSLATIONS['en'].get(key, key)
        return f'<span data-t="{key}">{fallback}</span>'

    full_html = re.sub(r'\{\{\s*t\.([a-zA-Z0-9_]+)\s*\}\}', replace_tag, full_html)

    # Handle tags inside placeholders e.g. placeholder="{{ t.xxxx }}"
    full_html = re.sub(r'placeholder="\{\{\s*t\.([a-zA-Z0-9_]+)\s*\}\}"', r'placeholder="" data-t-ph="\1"', full_html)

    # Clean up all residual Jinja layout directives
    full_html = re.sub(r'\{%.*?%\}', '', full_html)
    full_html = re.sub(r'\{\{\s*form_error\s*\}\}', '', full_html)
    full_html = re.sub(r'\{\{\s*current_lang\s*\}\}', 'en', full_html)
    full_html = re.sub(r'action="\{\{\s*url_for.*?\}\}"', 'action="#"', full_html)



    # Replace the Language switcher Jinja loop with static HTML buttons
    lang_switcher_html = """
    <div class="lang-switcher">
      <span class="lang-icon">🌐</span>
      <button type="button" class="lang-btn active" data-lang="en" onclick="setLanguage('en')">English</button>
      <button type="button" class="lang-btn" data-lang="hi" onclick="setLanguage('hi')">हिन्दी</button>
      <button type="button" class="lang-btn" data-lang="te" onclick="setLanguage('te')">తెలుగు</button>
    </div>
    """
    full_html = re.sub(r'<div class="lang-switcher">.*?</div>', lang_switcher_html, full_html, flags=re.DOTALL)

    # Remove headers/nav logic that references url_for
    full_html = re.sub(r'<div class="header-links">.*?</div>', '', full_html, flags=re.DOTALL)

    # Inject the translation helper script into <head>
    full_html = full_html.replace('</head>', f'{translation_script}\n</head>')

    # 5. Replace backend fetch in index.html voice JS block with direct Gemini API call
    gemini_fetch_js = """
      // Client-side direct Gemini call for standalone prototype
      const apiKey = document.getElementById('gemini-api-key').value;
      if (!apiKey) {
        const errorMsg = currentLang === 'hi' ? 'कृपया ऊपर अपना जेमिनी एपीआई की (API Key) दर्ज करें।' : (currentLang === 'te' ? 'దయచేసి పైన మీ జెమిని API కీని నమోదు చేయండి.' : 'Please enter your Gemini API Key in the setup box at the top of the page.');
        qText.textContent = errorMsg;
        setOrbState('speaking');
        speakText(errorMsg, () => { startConversationalListening(); });
        return;
      }

      // Build missing fields checklist
      const allFormFields = [
        "owner_name", "owner_phone", "worker_name", "worker_phone",
        "work_description", "work_location", "start_date", "duration",
        "wage_amount", "wage_unit", "payment_schedule", "late_penalty"
      ];
      const missingFields = allFormFields.filter(f => !aiCurrentState[f] || String(aiCurrentState[f]).trim() === "");

      const geminiPrompt = `
You are Sahayak (सहायक / सहायक), a warm, empathetic voice assistant.
Help the user fill out a wage agreement form. Speak like a friendly community elder.
User transcript: "${userTranscript}"
Current fields collected: ${JSON.stringify(aiCurrentState)}
Missing fields list: ${JSON.stringify(missingFields)}
Target Language: ${currentLang}

IMPORTANT INSTRUCTIONS:
- Extract all fields provided by the user in this turn.
- Actively check for numbers and values. If user said wage amount (e.g. 950 or 1500) and duration, extract it.
- Reply ONLY in ${currentLang} (Hindi in Devanagari, Telugu in Telugu script, Hinglish if user mixes Hindi/English).
- Keep the reply conversational and human-like (1-3 sentences). Do NOT read out field names.
- Ask for the next missing details one by one naturally.
- When critical fields (owner_name, worker_name, work_description, wage_amount) are present and complete, set "is_complete": true.

Return ONLY a valid JSON object matching this schema:
{
  "reply": "your warm conversational response in target language",
  "extracted_fields": {
     "owner_name": "value if found",
     ...
  },
  "is_complete": false
}`;

      fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: geminiPrompt }] }],
          generationConfig: { responseMimeType: "application/json", temperature: 0.7 }
        })
      })
      .then(r => r.json())
      .then(res => {
        const text = res.candidates[0].content.parts[0].text;
        const data = JSON.parse(text.trim());
        
        // Merge extracted fields
        if (data.extracted_fields) {
          Object.assign(aiCurrentState, data.extracted_fields);
          populateFormFromAI(aiCurrentState);
          updateProgressUI(aiCurrentState);
        }

        const reply = data.reply || 'Got it. Please continue.';
        aiConvHistory.push({ role: 'assistant', content: reply });

        qText.textContent = reply;
        transcriptPreview.textContent = '';
        setOrbState('speaking');

        if (data.is_complete || (allFormFields.filter(f => !aiCurrentState[f] || String(aiCurrentState[f]).trim() === "").length === 0)) {
          speakText(reply, () => {
            setTimeout(() => {
              exitVoiceMode();
              showReviewScreen();
            }, 800);
          });
        } else {
          speakText(reply, () => {
            startConversationalListening();
          });
        }
      })
      .catch(err => {
        console.error("Gemini API error:", err);
        const errMsg = currentLang === 'hi' ? 'ओह, जेमिनी एपीआई एरर। कृपया फिर से प्रयास करें।' : 'Gemini API Error. Please verify your API Key and try again.';
        qText.textContent = errMsg;
        setOrbState('speaking');
        speakText(errMsg, () => { startConversationalListening(); });
      });
    """

    # Locate the fetch block inside index.html and replace it
    fetch_block_regex = r"fetch\('/api/voice-assistant/converse'.*?\}\);\s*\}"
    modified_html, count = re.subn(fetch_block_regex, gemini_fetch_js + "\n    }", full_html, flags=re.DOTALL)
    print(f"Replaced fetch block: {count} matches")

    # Let's ensure the onload event sets default English translation
    modified_html = modified_html.replace('</body>', '<script>\nsetLanguage("en");\n</script>\n</body>')

    # Insert the setup box for Gemini key at the very top of main container
    setup_box_html = """
    <div class="api-key-container" style="background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
      <h3 style="margin-top: 0; margin-bottom: 8px; font-size: 18px; color: #1e293b;">🔑 Standalone Prototype Setup</h3>
      <p style="margin-top: 0; margin-bottom: 12px; font-size: 14px; color: #64748b;">To enable the conversational Gemini assistant on this laptop, paste your Gemini API Key below. This key stays locally in your browser.</p>
      <input type="password" id="gemini-api-key" placeholder="Paste your Gemini API Key here (AIzaSy...)" style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; box-sizing: border-box;">
    </div>
    """
    modified_html = modified_html.replace('<div class="main-card">', '<div class="main-card">\n' + setup_box_html)

    dest_path = r'C:\Users\Rohit\.gemini\antigravity\brain\3d00a79a-8174-4a9e-89ef-0ec63ff87fa2\sahayak_prototype.html'
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(modified_html)
    print(f"Perfect standalone prototype generated at: {dest_path}")

if __name__ == '__main__':
    build()
