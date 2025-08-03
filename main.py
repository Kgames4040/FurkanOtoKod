from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import imaplib
import email
import re
import json
import os
from bs4 import BeautifulSoup
from datetime import datetime
from email.header import decode_header

app = Flask(__name__)
app.secret_key = "gizli_admin_sifresi"

# ------------------ PLATFORM AYARLARI ------------------

PLATFORMS = {
    "disney": {
        "subjects": ["Disney+ için tek seferlik kodunuz", "ChatGPT kodun"],
        "allowed_senders": ["noreply@tm.openai.com"],
        "code_regex": r"\b\d{6}\b",
        "key_file": "veri/DISNEY_keys.txt",
        "log_file": "veri/disney_log.txt"
    },
    "netflix": {
        "subjects": ["Netflix: Oturum açma kodunuz"],
        "allowed_senders": ["info@account.netflix.com"],
        "code_regex": r"\b\d{4}\b",
        "key_file": "veri/NETFLIX_keys.txt",
        "log_file": "veri/netflix_log.txt"
    },
    "steam": {
        "subjects": ["Steam hesabınız: Yeni bilgisayardan erişim", "Steam hesabınız: Yeni tarayıcıdan veya mobil cihazdan erişim"],
        "allowed_senders": ["noreply@steampowered.com"],
        "code_regex": r"\b[A-Z0-9]{5}\b",
        "key_file": "veri/STEAM_keys.txt",
        "log_file": "veri/steam_log.txt"
    }
}

ACCOUNT_FILE = "mail_config/accounts.json"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

# ------------------ YARDIMCI FONKSİYONLAR ------------------

def decode_subject(subject_raw):
    decoded = decode_header(subject_raw)
    return "".join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in decoded
    )

def load_keys(path):
    if not os.path.exists(path): return {}
    with open(path, "r") as f:
        return {line.strip().split("|")[0]: int(line.strip().split("|")[1]) for line in f if "|" in line}

def save_keys(path, key_dict):
    with open(path, "w") as f:
        for key, count in key_dict.items():
            f.write(f"{key}|{count}\n")

def is_valid_key(platform, key):
    keys = load_keys(PLATFORMS[platform]["key_file"])
    return key in keys and keys[key] > 0

def reduce_key_usage(platform, key):
    keys = load_keys(PLATFORMS[platform]["key_file"])
    if key in keys and keys[key] > 0:
        keys[key] -= 1
        save_keys(PLATFORMS[platform]["key_file"], keys)

def get_used_codes(path):
    if not os.path.exists(path): return set()
    with open(path, "r") as f:
        return set(line.strip().split(" - ")[-1] for line in f)

def save_code(path, platform, identifier, code):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a") as f:
        f.write(f"[{now}] {platform.upper()} - {identifier} - {code}\n")

def load_accounts():
    if not os.path.exists(ACCOUNT_FILE): return []
    with open(ACCOUNT_FILE, "r") as f:
        return json.load(f)

def save_accounts(accounts):
    with open(ACCOUNT_FILE, "w") as f:
        json.dump(accounts, f, indent=4)

# ------------------ KOD AL ------------------

def get_verification_code(platform, identifier):
    used = get_used_codes(PLATFORMS[platform]["log_file"])
    accounts = load_accounts()

    for acc in accounts:
        if acc.get("platform") != platform:
            continue
        if platform == "steam" and identifier.lower() != acc.get("username", "").lower():
            continue
        if platform != "steam" and identifier.lower() != acc.get("email", "").lower():
            continue

        email_address = acc["email"]
        password = acc["password"]

        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(email_address, password)
            mail.select("inbox")
            _, data = mail.search(None, "UNSEEN")
            for num in reversed(data[0].split()):
                _, msg_data = mail.fetch(num, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                sender = email.utils.parseaddr(msg["From"])[1]
                subject = decode_subject(msg["Subject"])

                if sender not in PLATFORMS[platform]["allowed_senders"]: continue
                if subject not in PLATFORMS[platform]["subjects"]: continue

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() in ["text/plain", "text/html"]:
                            body += part.get_payload(decode=True).decode(errors="ignore")
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                soup = BeautifulSoup(body, "html.parser")
                text = soup.get_text()
                codes = re.findall(PLATFORMS[platform]["code_regex"], text)

                for code in codes:
                    code = code.upper()
                    if code not in used:
                        return code, acc.get("username") if platform == "steam" else acc.get("email")
        except:
            continue

    return None, None

# ------------------ FLASK ROTALAR ------------------

@app.route("/")
def index(): return render_template("index.html")

@app.route("/disney")
def disney(): return render_template("disney.html")

@app.route("/netflix")
def netflix(): return render_template("netflix.html")

@app.route("/steam")
def steam(): return render_template("steam.html")

@app.route("/get-code", methods=["POST"])
def get_code():
    data = request.get_json()
    platform = data.get("platform", "").lower()
    key = data.get("key", "").strip()
    identifier = data.get("username") if platform == "steam" else data.get("email")

    if platform not in PLATFORMS: return jsonify({"error": "Geçersiz platform"})
    if not is_valid_key(platform, key): return jsonify({"error": "Geçersiz ürün anahtarı"})

    code, user = get_verification_code(platform, identifier)
    if code:
        reduce_key_usage(platform, key)
        save_code(PLATFORMS[platform]["log_file"], platform, user, code)
        return jsonify({"code": code})

    return jsonify({"error": "Kod bulunamadı, tekrar deneyin."})

# ------------------ ADMIN PANEL ------------------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        return render_template("admin/admin_login.html", error="Hatalı giriş.")
    return render_template("admin/admin_login.html")

@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"): return redirect(url_for("admin_login"))
    return render_template("admin/admin_panel.html")

@app.route("/admin/add-keys", methods=["GET", "POST"])
def admin_add_keys():
    if not session.get("admin"): return redirect(url_for("admin_login"))

    existing_keys = {}
    for plat, settings in PLATFORMS.items():
        existing_keys[plat] = load_keys(settings["key_file"])

    if request.method == "POST":
        platform = request.form.get("platform")
        new_key = request.form.get("new_key").strip()
        usage = int(request.form.get("usage", "1"))

        if platform in PLATFORMS:
            keys = load_keys(PLATFORMS[platform]["key_file"])
            keys[new_key] = usage
            save_keys(PLATFORMS[platform]["key_file"], keys)
            return redirect(url_for("admin_add_keys"))

    return render_template("admin/admin_add_keys.html", keys=existing_keys)

@app.route("/admin/add-accounts", methods=["GET", "POST"])
def admin_add_accounts():
    if not session.get("admin"): return redirect(url_for("admin_login"))

    accounts = load_accounts()

    if request.method == "POST":
        platform = request.form.get("platform")
        email_ = request.form.get("email")
        password = request.form.get("password")
        username = request.form.get("username") if platform == "steam" else None

        new_acc = {"platform": platform, "email": email_, "password": password}
        if username: new_acc["username"] = username
        accounts.append(new_acc)
        save_accounts(accounts)

        return redirect(url_for("admin_add_accounts"))

    return render_template("admin/admin_add_accounts.html", accounts=accounts)

@app.route("/admin/delete-account", methods=["POST"])
def admin_delete_account():
    if not session.get("admin"): return jsonify({"success": False})

    email = request.form.get("email")
    platform = request.form.get("platform")
    username = request.form.get("username")

    accounts = load_accounts()
    new_accounts = []
    for acc in accounts:
        if acc["platform"] == platform and acc["email"] == email:
            if platform == "steam":
                if acc.get("username") == username:
                    continue
            else:
                continue
        new_accounts.append(acc)

    save_accounts(new_accounts)
    return jsonify({"success": True})

@app.route("/admin/logs")
def admin_logs():
    if not session.get("admin"): return redirect(url_for("admin_login"))
    logs = []
    for plat in PLATFORMS:
        path = PLATFORMS[plat]["log_file"]
        if os.path.exists(path):
            with open(path) as f:
                logs.extend(f.readlines())
    logs = sorted(logs, reverse=True)
    return render_template("admin/admin_logs.html", logs=logs)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

    
@app.route("/admin/update-key", methods=["POST"])
def admin_update_key():
    if not session.get("admin"): return jsonify({"success": False})

    platform = request.form.get("platform")
    key = request.form.get("key")
    new_usage = request.form.get("usage")

    if platform not in PLATFORMS or not key or not new_usage:
        return jsonify({"success": False})

    try:
        new_usage = int(new_usage)
        if new_usage < 1:
            return jsonify({"success": False})
    except:
        return jsonify({"success": False})

    keys = load_keys(PLATFORMS[platform]["key_file"])
    if key not in keys:
        return jsonify({"success": False})

    keys[key] = new_usage
    save_keys(PLATFORMS[platform]["key_file"], keys)
    return jsonify({"success": True})

    
@app.route("/admin/delete-key", methods=["POST"])
def admin_delete_key():
    if not session.get("admin"): return jsonify({"success": False})

    platform = request.form.get("platform")
    key = request.form.get("key")

    if platform in PLATFORMS:
        keys = load_keys(PLATFORMS[platform]["key_file"])
        if key in keys:
            keys.pop(key)
            save_keys(PLATFORMS[platform]["key_file"], keys)
            return jsonify({"success": True})

    return jsonify({"success": False})





# ------------------ UYGULAMA BAŞLAT ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)