from functools import wraps

from flask import Flask, jsonify, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-me"

# Basit giriş bilgileri (demo amaçlı)
KULLANICI_ADI = "admin"
SIFRE = "123456"

# Geçici bellek listesi
personeller = []

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Giriş | Personel Maaş Takip</title>
  <style>
    body {
      margin: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(120deg, #e0e7ff, #f8fafc);
      min-height: 100vh;
      display: grid;
      place-items: center;
    }
    .card {
      width: min(420px, 92vw);
      background: #fff;
      border-radius: 14px;
      padding: 24px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
      border: 1px solid #e5e7eb;
    }
    h1 { margin: 0 0 16px; font-size: 1.4rem; }
    label { display: block; margin-bottom: 6px; color: #4b5563; font-size: 0.9rem; }
    input {
      width: 100%;
      padding: 10px;
      border: 1px solid #d1d5db;
      border-radius: 10px;
      margin-bottom: 12px;
      box-sizing: border-box;
    }
    button {
      width: 100%;
      border: none;
      padding: 11px;
      border-radius: 10px;
      background: #2563eb;
      color: #fff;
      font-weight: 600;
      cursor: pointer;
    }
    .error { color: #b91c1c; margin-top: 10px; min-height: 20px; }
    .hint { color: #6b7280; font-size: 0.85rem; margin-top: 12px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Yönetim Paneli Girişi</h1>
    <form method="POST">
      <label for="username">Kullanıcı Adı</label>
      <input id="username" name="username" required />

      <label for="password">Şifre</label>
      <input id="password" name="password" type="password" required />

      <button type="submit">Giriş Yap</button>
      <div class="error">{{ hata or "" }}</div>
      <div class="hint">Demo giriş: <b>admin</b> / <b>123456</b></div>
    </form>
  </div>
</body>
</html>
"""

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Personel Maaş Takip</title>
  <style>
    :root { --bg: #f3f6fb; --card: #fff; --text: #1f2937; --muted: #6b7280; --primary: #2563eb; --primary-dark: #1d4ed8; --border: #e5e7eb; --success: #047857; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(120deg, #eef2ff, var(--bg)); color: var(--text); min-height: 100vh; }
    .container { max-width: 1100px; margin: 36px auto; padding: 0 16px; }
    .topbar { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom: 18px; }
    .title { font-size: 1.8rem; font-weight: 700; margin: 0; }
    .logout { text-decoration:none; background:#111827; color:#fff; padding:8px 12px; border-radius:10px; font-size:0.9rem; }
    .layout { display: grid; grid-template-columns: 340px 1fr; gap: 20px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 14px; box-shadow: 0 10px 30px rgba(17, 24, 39, 0.08); padding: 18px; }
    .card h2 { margin-top: 0; font-size: 1.1rem; }
    .field { margin-bottom: 12px; }
    label { display:block; margin-bottom:6px; font-size:.92rem; color:var(--muted); }
    input { width:100%; padding:10px 12px; border:1px solid #d1d5db; border-radius:10px; font-size:.95rem; outline:none; }
    .btn { border:none; background:var(--primary); color:#fff; width:100%; padding:11px; border-radius:10px; font-weight:600; cursor:pointer; }
    .btn:hover { background: var(--primary-dark); }
    .status { margin-top:10px; font-size:.9rem; color:var(--success); min-height:20px; }
    .table-wrap { overflow-x:auto; }
    table { width:100%; border-collapse:collapse; font-size:.93rem; }
    th, td { border-bottom:1px solid var(--border); text-align:left; padding:10px; white-space:nowrap; }
    th { background:#f8fafc; color:#374151; font-weight:600; }
    .empty { color:var(--muted); text-align:center; padding:24px; }
    @media (max-width:920px){ .layout{grid-template-columns:1fr;} .topbar{flex-direction:column; align-items:flex-start;} }
  </style>
</head>
<body>
  <div class="container">
    <div class="topbar">
      <h1 class="title">Personel Maaş Takip Sistemi</h1>
      <a class="logout" href="/logout">Çıkış Yap</a>
    </div>
    <div class="layout">
      <div class="card">
        <h2>Yeni Personel Ekle</h2>
        <form id="personelForm">
          <div class="field"><label for="ad">Ad</label><input id="ad" name="ad" required /></div>
          <div class="field"><label for="gunluk_ucret">Günlük Ücret (₺)</label><input id="gunluk_ucret" name="gunluk_ucret" type="number" min="0" step="0.01" required /></div>
          <div class="field"><label for="calisilan_gun">Çalışılan Gün</label><input id="calisilan_gun" name="calisilan_gun" type="number" min="0" step="1" value="0" required /></div>
          <div class="field"><label for="avans">Avans (₺)</label><input id="avans" name="avans" type="number" min="0" step="0.01" value="0" required /></div>
          <button class="btn" type="submit">Personel Ekle</button>
          <div id="status" class="status"></div>
        </form>
      </div>
      <div class="card">
        <h2>Personel Listesi</h2>
        <div class="table-wrap"><table><thead><tr><th>Ad</th><th>Günlük Ücret</th><th>Çalışılan Gün</th><th>Toplam Maaş</th><th>Avans</th><th>Kalan Maaş</th></tr></thead><tbody id="personelBody"><tr><td class="empty" colspan="6">Henüz personel yok.</td></tr></tbody></table></div>
      </div>
    </div>
  </div>
  <script>
    const form = document.getElementById("personelForm");
    const body = document.getElementById("personelBody");
    const statusEl = document.getElementById("status");
    const para = (n) => Number(n).toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    function satirOlustur(k){ return `<tr><td>${k.ad}</td><td>₺${para(k.gunluk_ucret)}</td><td>${k.calisilan_gun}</td><td>₺${para(k.toplam_maas)}</td><td>₺${para(k.avans)}</td><td>₺${para(k.kalan_maas)}</td></tr>`; }
    async function listeyiYukle(){ const r = await fetch('/api/personeller'); if(r.status===401){ window.location='/login'; return;} const d = await r.json(); body.innerHTML = d.length ? d.map(satirOlustur).join('') : '<tr><td class="empty" colspan="6">Henüz personel yok.</td></tr>'; }
    form.addEventListener('submit', async (e)=>{ e.preventDefault(); const p={ ad:form.ad.value.trim(), gunluk_ucret:Number(form.gunluk_ucret.value), calisilan_gun:Number(form.calisilan_gun.value), avans:Number(form.avans.value)}; const r = await fetch('/api/personeller',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)}); const j = await r.json(); if(!r.ok){ statusEl.style.color='#b91c1c'; statusEl.textContent=j.hata||'Kayıt sırasında hata oluştu.'; return;} statusEl.style.color='#047857'; statusEl.textContent='Personel başarıyla eklendi.'; form.reset(); form.calisilan_gun.value=0; form.avans.value=0; await listeyiYukle(); });
    listeyiYukle();
  </script>
</body>
</html>
"""


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"hata": "Yetkisiz erişim."}), 401
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == KULLANICI_ADI and password == SIFRE:
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template_string(LOGIN_HTML, hata="Kullanıcı adı veya şifre hatalı.")

    if session.get("logged_in"):
        return redirect(url_for("index"))
    return render_template_string(LOGIN_HTML)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@login_required
def index():
    return render_template_string(HTML)


@app.get("/api/personeller")
@login_required
def get_personeller():
    return jsonify(personeller)


@app.post("/api/personeller")
@login_required
def add_personel():
    data = request.get_json(silent=True) or {}
    ad = str(data.get("ad", "")).strip()
    gunluk_ucret = float(data.get("gunluk_ucret", 0) or 0)
    calisilan_gun = int(data.get("calisilan_gun", 0) or 0)
    avans = float(data.get("avans", 0) or 0)

    if not ad:
        return jsonify({"hata": "Ad alanı zorunludur."}), 400
    if gunluk_ucret < 0 or calisilan_gun < 0 or avans < 0:
        return jsonify({"hata": "Sayısal alanlar negatif olamaz."}), 400

    toplam_maas = gunluk_ucret * calisilan_gun
    kalan_maas = toplam_maas - avans
    kisi = {"ad": ad, "gunluk_ucret": gunluk_ucret, "calisilan_gun": calisilan_gun, "toplam_maas": toplam_maas, "avans": avans, "kalan_maas": kalan_maas}
    personeller.append(kisi)
    return jsonify(kisi), 201


if __name__ == "__main__":
    app.run(debug=True)
