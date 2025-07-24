import os
import json

# Klasör yapısını oluştur
folders = [
    "templates",
    "static",
    "static/logos",
    "static/arka_planlar",
    "veri",
    "mail_config"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Boş HTML dosyaları
html_files = [
    "templates/index.html",
    "templates/disney.html",
    "templates/netflix.html",
    "templates/steam.html",
    "templates/admin_login.html",
    "templates/admin_panel.html",
    "templates/admin_keys.html",
    "templates/admin_logs.html"
]

for file in html_files:
    open(file, "w", encoding="utf-8").close()

# Diğer dosyalar
data_files = [
    "veri/DISNEY_keys.txt",
    "veri/NETFLIX_keys.txt",
    "veri/STEAM_keys.txt",
    "veri/logs.txt"
]

for file in data_files:
    open(file, "w", encoding="utf-8").close()

# Steam kullanıcı eşlemesi (örnek veri)
steam_users = {
    "gamer12": "steamkod1@gmail.com",
    "playerTR": "steamkod2@gmail.com"
}
with open("veri/steam_users.json", "w", encoding="utf-8") as f:
    json.dump(steam_users, f, indent=4)

# Mail konfigürasyonları (örnek boş json listesi)
mail_configs = ["disney.json", "netflix.json", "steam.json"]
for conf in mail_configs:
    with open(f"mail_config/{conf}", "w", encoding="utf-8") as f:
        json.dump([], f)

# style.css
with open("static/style.css", "w", encoding="utf-8") as f:
    f.write("/* Buraya CSS yazılacak */")

# main.py
open("main.py", "w", encoding="utf-8").close()

# requirements.txt
with open("requirements.txt", "w", encoding="utf-8") as f:
    f.write("flask\nbeautifulsoup4\nimaplib2\n")

print("✅ Replit proje yapısı başarıyla oluşturuldu.")