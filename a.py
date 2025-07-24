import os

# Ana klasör ve alt klasör yolları
base_folder = "templates/admin"
static_folder = "static"

# Oluşturulacak admin HTML dosyaları
html_files = [
    "admin_login.html",
    "admin_panel.html",
    "admin_add_accounts.html",
    "admin_add_keys.html",
    "admin_logs.html"
]

# Admin CSS dosyası
css_file = os.path.join(static_folder, "admin.css")

# 1. Admin panel klasörünü oluştur
os.makedirs(base_folder, exist_ok=True)

# 2. HTML dosyalarını oluştur (boş şablonla)
for file in html_files:
    path = os.path.join(base_folder, file)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"<!-- {file} içeriği buraya eklenecek -->\n")

# 3. admin.css dosyasını oluştur (temel stil şablonu ile)
os.makedirs(static_folder, exist_ok=True)

if not os.path.exists(css_file):
    with open(css_file, "w", encoding="utf-8") as f:
        f.write("""
/* Fjalla One font */
@import url('https://fonts.googleapis.com/css2?family=Fjalla+One&display=swap');

body {
    font-family: 'Fjalla One', sans-serif;
    background-color: #f0f8ff;
    margin: 0;
    padding: 0;
    color: #333;
}

button, input, .box {
    border-radius: 50px;
}

.sidebar {
    background-color: #007bff;
    color: white;
}
        """.strip())

print("✅ Admin panel klasörü ve dosyaları başarıyla oluşturuldu.")