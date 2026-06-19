from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from datetime import datetime, timedelta
import os
import secrets
import requests as http_requests
from dotenv import load_dotenv
from db.database import get_db_connection, save_linkedin_token, get_linkedin_token
from services.style_memory import store_approved_post
import psycopg2.extras

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
LINKEDIN_REDIRECT_URI = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:5000/auth/callback')

# ── Database helpers ──────────────────────────────────────────────────────────

def get_pending_content(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, news_title, news_content, content_type, generated_text,
               quality_score, conviction_score, matched_beliefs_json,
               status, created_at, scheduled_for
        FROM pending_content
        WHERE user_id = %s AND status = 'pending'
        ORDER BY created_at DESC
    """, (user_id,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in results]

def approve_content(content_id, user_id, scheduled_for=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE pending_content
        SET status = 'approved', approved_at = NOW(), scheduled_for = %s
        WHERE id = %s AND user_id = %s
    """, (scheduled_for, content_id, user_id))
    conn.commit()
    cur.close()
    conn.close()

def mark_published(content_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE pending_content SET status = 'published', published_at = NOW()
        WHERE id = %s
    """, (content_id,))
    conn.commit()
    cur.close()
    conn.close()

def reject_content(content_id, user_id, reason=None):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE pending_content
        SET status = 'rejected', rejection_reason = %s
        WHERE id = %s AND user_id = %s
    """, (reason, content_id, user_id))
    conn.commit()
    cur.close()
    conn.close()

def update_content_text(content_id, user_id, new_text):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE pending_content
        SET generated_text = %s, edited = true
        WHERE id = %s AND user_id = %s
    """, (new_text, content_id, user_id))
    conn.commit()
    cur.close()
    conn.close()

def get_content_by_id(content_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM pending_content WHERE id = %s", (content_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return dict(result) if result else None

# ── LinkedIn API ──────────────────────────────────────────────────────────────

def post_to_linkedin(user_id: int, text: str) -> dict:
    """Post text content to LinkedIn on behalf of user"""
    token_data = get_linkedin_token(user_id)
    if not token_data or not token_data.get('linkedin_access_token'):
        return {"success": False, "error": "No LinkedIn token. Connect LinkedIn first."}

    access_token = token_data['linkedin_access_token']

    # Reject tokens that are still in the PENDING OAuth state
    if access_token.startswith("PENDING:"):
        return {"success": False, "error": "LinkedIn OAuth not completed. Please connect LinkedIn."}

    # Check token expiry
    expiry = token_data.get('linkedin_token_expiry')
    if expiry and datetime.utcnow() > expiry:
        return {"success": False, "error": "LinkedIn token expired. Please reconnect LinkedIn."}

    person_urn = token_data['linkedin_person_urn']

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    resp = http_requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload,
        timeout=15
    )

    if resp.status_code in (200, 201):
        return {"success": True, "post_id": resp.headers.get("x-restli-id", "")}
    else:
        return {"success": False, "error": resp.text, "status": resp.status_code}

# ── LinkedIn OAuth routes ─────────────────────────────────────────────────────

@app.route('/auth/linkedin')
def linkedin_auth():
    state = secrets.token_urlsafe(16)
    user_id = int(request.args.get('user_id', 1))

    # Store state in DB so it survives debug reloader restarts
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET linkedin_access_token = %s WHERE id = %s", (f"PENDING:{state}:{user_id}", user_id))
    conn.commit()
    cur.close()
    conn.close()

    params = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={LINKEDIN_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=openid%20profile%20w_member_social"
    )
    return redirect(params)

@app.route('/auth/callback')
def linkedin_callback():
    error = request.args.get('error')
    if error:
        return f"LinkedIn OAuth error: {error}", 400

    state = request.args.get('state')
    code = request.args.get('code')

    # Recover user_id and validate state from DB
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, linkedin_access_token FROM users WHERE linkedin_access_token LIKE 'PENDING:%'")
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return "OAuth session expired. Please try connecting again.", 400

    stored = row[1]  # "PENDING:{state}:{user_id}"
    parts = stored.split(":")
    if len(parts) < 3 or parts[1] != state:
        return "State mismatch. Please try connecting again.", 400

    user_id = int(parts[2])

    # Exchange code for token
    token_resp = http_requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": LINKEDIN_REDIRECT_URI,
            "client_id": LINKEDIN_CLIENT_ID,
            "client_secret": LINKEDIN_CLIENT_SECRET,
        },
        timeout=15
    )

    if token_resp.status_code != 200:
        return f"Token exchange failed: {token_resp.text}", 400

    token_json = token_resp.json()
    access_token = token_json['access_token']
    expires_in = token_json.get('expires_in', 5184000)
    expiry = datetime.utcnow() + timedelta(seconds=expires_in)

    # Get LinkedIn person URN via userinfo endpoint
    userinfo_resp = http_requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15
    )
    if userinfo_resp.status_code != 200:
        return f"Failed to fetch LinkedIn profile: {userinfo_resp.text}", 400
    userinfo = userinfo_resp.json()
    sub = userinfo.get('sub', '')
    if not sub:
        return "LinkedIn profile missing sub claim. Please try connecting again.", 400
    person_urn = f"urn:li:person:{sub}"
    name = userinfo.get('name', 'Unknown')

    save_linkedin_token(user_id, access_token, person_urn, expiry)

    return redirect(f"/?linkedin_connected=1&name={name}")

# ── Dashboard routes ──────────────────────────────────────────────────────────

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/user/<int:user_id>/pending', methods=['GET'])
def get_pending(user_id):
    pending = get_pending_content(user_id)
    return jsonify(pending)

@app.route('/api/user/<int:user_id>/linkedin_status', methods=['GET'])
def linkedin_status(user_id):
    token_data = get_linkedin_token(user_id)
    if token_data and token_data.get('linkedin_access_token'):
        connected = True
        urn = token_data.get('linkedin_person_urn', '')
        expiry = token_data.get('linkedin_token_expiry')
        expired = expiry and datetime.utcnow() > expiry
    else:
        connected = False
        urn = ''
        expired = False
    return jsonify({"connected": connected and not expired, "urn": urn})

@app.route('/api/content/<int:content_id>/approve', methods=['POST'])
def approve(content_id):
    data = request.json
    user_id = data.get('user_id')
    scheduled_for = data.get('scheduled_for')

    approve_content(content_id, user_id, scheduled_for)

    content = get_content_by_id(content_id)
    linkedin_result = None

    if content:
        # Store in ChromaDB style memory for every content type
        store_approved_post(
            user_id,
            content['content_type'],
            content['generated_text'],
            content.get('news_title', ''),
            content.get('conviction_score') or 0.5
        )

        # Auto-post to LinkedIn if this is a linkedin content piece
        if content.get('content_type') == 'linkedin':
            result = post_to_linkedin(user_id, content['generated_text'])
            if result['success']:
                mark_published(content_id)
                linkedin_result = {"posted": True, "post_id": result.get('post_id')}
            else:
                linkedin_result = {"posted": False, "error": result.get('error')}

    return jsonify({"status": "approved", "linkedin": linkedin_result})

@app.route('/api/content/<int:content_id>/reject', methods=['POST'])
def reject(content_id):
    data = request.json
    user_id = data.get('user_id')
    reason = data.get('reason')
    reject_content(content_id, user_id, reason)
    return jsonify({"status": "rejected"})

@app.route('/api/content/<int:content_id>/edit', methods=['POST'])
def edit(content_id):
    data = request.json
    user_id = data.get('user_id')
    new_text = data.get('text')
    update_content_text(content_id, user_id, new_text)
    return jsonify({"status": "updated"})

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, port=int(os.getenv('PORT', 5000)))
