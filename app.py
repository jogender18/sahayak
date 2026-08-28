import os
import io
import base64
import qrcode
from flask import Flask, render_template, request, redirect, url_for, send_file, abort, jsonify, make_response
from database import init_db, create_agreement, get_agreement, list_recent_agreements
from pdf_generator import generate_agreement_pdf
from translations import TRANSLATIONS, get_text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sahayak-wage-secret-key-2026'

# Ensure database is initialized
init_db()

def get_base_url():
    """
    Returns the public base URL for QR codes and verification links.

    Priority order (highest → lowest):
      1. PUBLIC_BASE_URL env var  — set this on Render/Railway/Vercel for a permanent URL.
      2. X-Forwarded-Proto/Host headers — always reflect the *currently active* tunnel
         URL that Cloudflare injects on every request. This means a restarted tunnel
         with a new URL is used immediately, with no stale-file risk.
      3. public_url.txt — fallback for PDF downloads triggered without a tunnel header
         (e.g. the /pdf/<id> route called directly from localhost).
      4. host_url — last resort (localhost).
    """
    # 1. Explicit env override (Render / Railway / permanent deploy)
    env_url = os.environ.get('PUBLIC_BASE_URL')
    if env_url:
        return env_url.rstrip('/')

    # 2. Live tunnel headers — Cloudflare injects these on every proxied request.
    #    These are always current, even after a tunnel restart with a new subdomain.
    forwarded_proto = request.headers.get('X-Forwarded-Proto')
    forwarded_host  = request.headers.get('X-Forwarded-Host')
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}"

    # 3. public_url.txt — written by tunnel_manager.py on startup.
    #    Used when the PDF download route is hit locally (no Cloudflare header),
    #    but the link/QR should still point at the public tunnel.
    url_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public_url.txt")
    if os.path.exists(url_file):
        try:
            with open(url_file, "r") as f:
                saved_url = f.read().strip()
            if saved_url.startswith("http"):
                return saved_url.rstrip('/')
        except Exception:
            pass

    # 4. Fallback: whatever host Flask sees (localhost in dev)
    return request.host_url.rstrip('/')

def get_current_lang():
    lang = request.args.get('lang')
    if not lang or lang not in TRANSLATIONS:
        lang = request.cookies.get('sahayak_lang', 'en')
    if lang not in TRANSLATIONS:
        lang = 'en'
    return lang

def make_qr_data_uri(url: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_b64}"

@app.context_processor
def inject_translations():
    lang = get_current_lang()
    return {
        "t": get_text(lang),
        "current_lang": lang,
        "all_langs": [
            {"code": "en", "label": "English"},
            {"code": "hi", "label": "हिन्दी (Hindi)"},
            {"code": "te", "label": "తెలుగు (Telugu)"}
        ]
    }

@app.route('/')
def index():
    lang = get_current_lang()
    recent = list_recent_agreements(limit=5)
    resp = make_response(render_template('index.html', recent=recent))
    if request.args.get('lang'):
        resp.set_cookie('sahayak_lang', lang, max_age=30*24*60*60)
    return resp

@app.route('/create', methods=['POST'])
def create():
    data = {
        "owner_name": request.form.get("owner_name", "").strip(),
        "owner_phone": request.form.get("owner_phone", "").strip(),
        "worker_name": request.form.get("worker_name", "").strip(),
        "worker_phone": request.form.get("worker_phone", "").strip(),
        "work_description": request.form.get("work_description", "").strip(),
        "wage_amount": request.form.get("wage_amount", "0").strip(),
        "wage_unit": request.form.get("wage_unit", "per day").strip(),
        "payment_schedule": request.form.get("payment_schedule", "weekly").strip(),
        "late_penalty": request.form.get("late_penalty", "").strip(),
        "start_date": request.form.get("start_date", "").strip(),
        "duration": request.form.get("duration", "").strip(),
        "work_location": request.form.get("work_location", "").strip(),
    }
    
    if not (data["owner_name"] and data["worker_name"] and data["work_description"] and data["wage_amount"]):
        lang = get_current_lang()
        recent = list_recent_agreements(limit=5)
        return render_template(
            'index.html',
            recent=recent,
            form_error="Please fill in all required fields: Owner Name, Worker Name, Description of Work, and Wage Amount.",
            form_data=data
        ), 400

    agreement_id = create_agreement(data)
    lang = get_current_lang()
    return redirect(url_for('view_agreement', agreement_id=agreement_id, lang=lang))

@app.route('/agreement/<agreement_id>')
def view_agreement(agreement_id):
    agreement = get_agreement(agreement_id)
    if not agreement:
        return render_template('404.html'), 404
    
    lang = get_current_lang()
    t = get_text(lang)
    verify_url = f"{get_base_url()}/verify/{agreement_id}?lang={lang}"
    qr_data_uri = make_qr_data_uri(verify_url)
    
    share_text = (
        f"🤝 {t['app_title']}\n"
        f"{t['role_employer']}: {agreement['owner_name']}\n"
        f"{t['role_worker']}: {agreement['worker_name']}\n"
        f"{t['lbl_agreed_wage']}: Rs. {agreement['wage_amount']:,.2f} ({agreement['wage_unit']})\n"
        f"Online Verification: {verify_url}"
    )

    resp = make_response(render_template(
        'agreement.html',
        agreement=agreement,
        verify_url=verify_url,
        qr_data_uri=qr_data_uri,
        share_text=share_text
    ))
    if request.args.get('lang'):
        resp.set_cookie('sahayak_lang', lang, max_age=30*24*60*60)
    return resp

@app.route('/verify/<agreement_id>')
def verify_agreement(agreement_id):
    agreement = get_agreement(agreement_id)
    if not agreement:
        return render_template('404.html'), 404
    
    lang = get_current_lang()
    resp = make_response(render_template('verify.html', agreement=agreement))
    if request.args.get('lang'):
        resp.set_cookie('sahayak_lang', lang, max_age=30*24*60*60)
    return resp

@app.route('/pdf/<agreement_id>')
def download_pdf(agreement_id):
    agreement = get_agreement(agreement_id)
    if not agreement:
        abort(404)
    
    lang = get_current_lang()
    verify_url = f"{get_base_url()}/verify/{agreement_id}?lang={lang}"
    pdf_buffer = generate_agreement_pdf(agreement, verify_url)
    
    filename = f"sahayak_agreement_{agreement_id[:8]}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/agreement/<agreement_id>')
def api_agreement(agreement_id):
    agreement = get_agreement(agreement_id)
    if not agreement:
        return jsonify({"error": "Agreement not found"}), 404
    return jsonify(agreement)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
