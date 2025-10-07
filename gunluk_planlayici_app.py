import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import os
from datetime import datetime
import json
import hashlib

# ==============================================================
# 🔐 ZORUNLU GİRİŞ / KAYIT SİSTEMİ + E-POSTA DOĞRULAMA + ŞİFRE SIFIRLAMA
# ==============================================================

import random
import smtplib
from email.message import EmailMessage

# --------------------------------------------------------------
# ✉️ E-posta gönderim ayarları
# --------------------------------------------------------------
EMAIL_ADDRESS = "gunlukplanlayici@gmail.com"  # Gmail adresin
EMAIL_PASSWORD = "nklofygdcgnsqkde"           # Google uygulama şifresi (16 haneli)

def send_email(to_email, code):
    """Gmail SMTP ile 6 haneli doğrulama kodu gönderir"""
    subject = "📧 Günlük Planlayıcı Doğrulama Kodunuz"
    body = f"Merhaba,\n\nGünlük Planlayıcı hesabınızı oluşturmak için aşağıdaki 6 haneli kodu girin:\n\n{code}\n\nKod 5 dakika boyunca geçerlidir."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"E-posta gönderilemedi: {e}")

# --------------------------------------------------------------
# 🔹 Kullanıcı sistemi
# --------------------------------------------------------------
USERS_FILE = "users.json"

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# --------------------------------------------------------------
# 🔹 Session durumu
# --------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "awaiting_verification" not in st.session_state:
    st.session_state.awaiting_verification = False
if "awaiting_password_reset" not in st.session_state:
    st.session_state.awaiting_password_reset = False
if "awaiting_password_verification" not in st.session_state:
    st.session_state.awaiting_password_verification = False

# --------------------------------------------------------------
# 🔹 Giriş / Kayıt ekranı
# --------------------------------------------------------------
if not st.session_state.logged_in:

    st.set_page_config(page_title="Günlük Planlayıcı", page_icon="🗓", layout="centered")

    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            max-width: 500px;
            padding-top: 80px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🗓 Günlük Planlayıcı")
    st.markdown("### Lütfen giriş yap veya kayıt ol")

    users = load_users()

    # ---------------- E-posta doğrulama ekranı ----------------
    if st.session_state.awaiting_verification:
        st.info(f"📩 {st.session_state.temp_user['email']} adresine gönderilen 6 haneli kodu gir:")
        user_code = st.text_input("Doğrulama Kodu")
        if st.button("Doğrula"):
            if user_code == st.session_state.verification_code:
                # Kaydı tamamla
                user_info = st.session_state.temp_user
                users[user_info["username"]] = {
                    "password": user_info["password"],
                    "email": user_info["email"],
                    "tasks": []
                }
                save_users(users)
                st.success("✅ E-posta doğrulandı! Kayıt tamamlandı, artık giriş yapabilirsiniz.")
                # Session temizle
                del st.session_state.verification_code
                del st.session_state.temp_user
                st.session_state.awaiting_verification = False
                st.rerun()
            else:
                st.error("❌ Hatalı kod, lütfen tekrar deneyin.")

    # ---------------- Şifremi unuttum ekranı ----------------
    elif st.session_state.awaiting_password_reset:
        st.info("📧 Kayıtlı e-postanı gir ve şifre sıfırlama kodu al.")
        reset_email = st.text_input("E-posta")
        if st.button("Kod Gönder"):
            for user, info in users.items():
                if info.get("email") == reset_email:
                    code = str(random.randint(100000, 999999))
                    st.session_state.reset_code = code
                    st.session_state.reset_user = user
                    send_email(reset_email, code)
                    st.session_state.awaiting_password_reset = False
                    st.session_state.awaiting_password_verification = True
                    st.success("📩 Şifre sıfırlama kodu gönderildi! Kod 5 dakika geçerlidir.")
                    st.rerun()
                    break
            else:
                st.error("❌ Bu e-postaya kayıtlı kullanıcı bulunamadı.")

    # ---------------- Şifre doğrulama ekranı ----------------
    elif st.session_state.awaiting_password_verification:
        st.info("📧 E-postana gönderilen 6 haneli kodu gir ve yeni şifre belirle.")
        user_code = st.text_input("Doğrulama Kodu")
        new_password = st.text_input("Yeni Şifre", type="password")
        confirm_password = st.text_input("Yeni Şifre (Tekrar)", type="password")
        if st.button("Şifreyi Sıfırla"):
            if user_code == st.session_state.reset_code:
                if new_password != confirm_password:
                    st.error("❌ Şifreler eşleşmiyor.")
                elif new_password == "":
                    st.error("❌ Yeni şifre boş olamaz.")
                else:
                    users[st.session_state.reset_user]["password"] = hash_password(new_password)
                    save_users(users)
                    st.success("✅ Şifre başarıyla değiştirildi! Şimdi giriş yapabilirsin.")
                    # Session temizle
                    st.session_state.pop("reset_code")
                    st.session_state.pop("reset_user")
                    st.session_state.awaiting_password_verification = False
                    st.rerun()
            else:
                st.error("❌ Kod hatalı, tekrar deneyin.")

    # ---------------- Giriş / Kayıt seçim ekranı ----------------
    else:
        secim = st.radio("Ne yapmak istiyorsun?", ["Giriş Yap", "Kayıt Ol"], horizontal=True)

        # ---------------- Giriş ----------------
        if secim == "Giriş Yap":
            username = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")

            if st.button("Giriş Yap"):
                if username in users and users[username]["password"] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.success(f"👋 Hoş geldin, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Kullanıcı adı veya şifre hatalı!")

            if st.button("Şifremi Unuttum"):
                st.session_state.awaiting_password_reset = True
                st.rerun()

        # ---------------- Kayıt ----------------
        elif secim == "Kayıt Ol":
            new_username = st.text_input("Yeni Kullanıcı Adı")
            new_email = st.text_input("E-posta")
            new_password = st.text_input("Şifre", type="password")
            confirm_password = st.text_input("Şifre (Tekrar)", type="password")

            if st.button("Kayıt Ol"):
                if new_username in users:
                    st.warning("⚠️ Bu kullanıcı adı zaten alınmış.")
                elif new_password != confirm_password:
                    st.error("❌ Şifreler eşleşmiyor.")
                elif new_username == "" or new_password == "" or new_email == "":
                    st.error("❌ Lütfen tüm alanları doldur.")
                else:
                    code = str(random.randint(100000, 999999))
                    st.session_state.verification_code = code
                    st.session_state.temp_user = {
                        "username": new_username,
                        "password": hash_password(new_password),
                        "email": new_email
                    }
                    send_email(new_email, code)
                    st.session_state.awaiting_verification = True
                    st.success("📩 E-posta doğrulama kodu gönderildi!")
                    st.rerun()

    st.stop()  # Giriş yapılmadıysa uygulama devam etmez

# --------------------------------------------------------------
# 🔹 Giriş sonrası ana ekran
# --------------------------------------------------------------
st.sidebar.success(f"👤 Aktif kullanıcı: {st.session_state.current_user}")

users = load_users()
current_user = st.session_state.current_user

if "tasks" not in users[current_user]:
    users[current_user]["tasks"] = []
    save_users(users)

user_tasks = users[current_user]["tasks"]
df = pd.DataFrame(user_tasks, columns=["Görev", "Açıklama", "Bitiş Tarihi", "Durum"])

def save_user_tasks():
    users = load_users()
    users[current_user]["tasks"] = df.to_dict(orient="records")
    save_users(users)

if st.sidebar.button("🚪 Çıkış Yap"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()


# --------------------------------------------------------------
# ⚙️ BURADAN SONRA GRİD, TAKVİM, EXCEL vb. GELECEK
# --------------------------------------------------------------


# Dosya adı
DOSYA_ADI = "gorevler.csv"

# Sayfa ayarı
st.set_page_config(page_title="Günlük Planlayıcı", layout="wide")
st.title("🗂️ Günlük Planlayıcı")
st.write("Görevlerinizi buradan takip edebilirsiniz.")

# Tema paleti seçimi
tema = st.sidebar.selectbox("Tema Paleti Seçin", ["Soft", "Pastel", "Klasik"])

# Görevleri CSV'den yükle
if os.path.exists(DOSYA_ADI):
    df = pd.read_csv(DOSYA_ADI, dtype={"Bitiş Tarihi": str})
else:
    df = pd.DataFrame(columns=["ID", "Görev", "Öncelik", "Bitiş Tarihi", "Tamamlandı", "Not"])

# ID sütunu yoksa ekle
if "ID" not in df.columns:
    df.insert(0, "ID", range(1, len(df)+1))

# Varsayılan tamamlandı sütunu ekle
if "Tamamlandı" not in df.columns:
    df["Tamamlandı"] = False

# Not sütunu varsa yoksa ekle
if "Not" not in df.columns:
    df["Not"] = ""

# Görev ekleme formu
with st.form("gorev_ekle", clear_on_submit=True):
    gorev = st.text_input("Görev adı")
    oncelik = st.selectbox("Öncelik", ["Düşük", "Orta", "Yüksek"])
    bitis_tarihi = st.date_input("Bitiş tarihi")
    bitis_saati = st.time_input("Bitiş saati")
    ekle = st.form_submit_button("Ekle")

    if ekle and gorev:
        bitis_ts = pd.Timestamp.combine(bitis_tarihi, bitis_saati)
        yeni_id = df["ID"].max() + 1 if not df.empty else 1
        yeni = pd.DataFrame([[yeni_id, gorev, oncelik, bitis_ts.strftime("%Y-%m-%d %H:%M:%S"), False, ""]],
                            columns=df.columns)
        df = pd.concat([df, yeni], ignore_index=True)
        df.to_csv(DOSYA_ADI, index=False)
        st.success("Görev eklendi ✅")
        st.rerun()

# Sidebar filtreleme ve sıralama
st.sidebar.header("Filtreleme ve Sıralama")
oncelik_secim = ["Hepsi", "Düşük", "Orta", "Yüksek"]
filtre_oncelik = st.sidebar.multiselect("Öncelik filtrele", oncelik_secim, default=["Hepsi"])
if "Hepsi" in filtre_oncelik:
    filtre_oncelik = ["Düşük", "Orta", "Yüksek"]

filtre_tamamlanan = st.sidebar.selectbox("Durum filtrele", ["Hepsi", "Tamamlandı", "Tamamlanmadı"])
siralama = st.sidebar.radio("Sırala", ["Bitiş Tarihi", "Öncelik"])

# Filtreleme
df_filtre = df[df["Öncelik"].isin(filtre_oncelik)]
if filtre_tamamlanan == "Tamamlandı":
    df_filtre = df_filtre[df_filtre["Tamamlandı"] == True]
elif filtre_tamamlanan == "Tamamlanmadı":
    df_filtre = df_filtre[df_filtre["Tamamlandı"] == False]

# Sıralama
if siralama == "Bitiş Tarihi":
    df_filtre = df_filtre.assign(_bt_dt=pd.to_datetime(df_filtre["Bitiş Tarihi"], errors='coerce'))
    df_filtre = df_filtre.sort_values("_bt_dt").drop(columns=["_bt_dt"])
else:
    oncelik_sira = {"Yüksek":0, "Orta":1, "Düşük":2}
    df_filtre = df_filtre.sort_values("Öncelik", key=lambda x: x.map(oncelik_sira))

# Tema renk paletleri
tema_paleti = {
    "Soft": {"Yüksek": {"color": "#4d0000", "bg": "#ffcccc"}, "Orta": {"color": "#665500", "bg": "#fff2cc"}, "Düşük": {"color": "#003300", "bg": "#ccffcc"},
             "Deadline": {"gecmis":"#e6e6e6", "turuncu":"#ffe0b3", "sari":"#fff2cc", "yesil":"#e6ffe6"}},
    "Pastel": {"Yüksek": {"color": "#660000", "bg": "#ffdddd"}, "Orta": {"color": "#666633", "bg": "#fff5cc"}, "Düşük": {"color": "#006600", "bg": "#ddffdd"},
               "Deadline": {"gecmis":"#f2f2f2", "turuncu":"#ffe6cc", "sari":"#ffffcc", "yesil":"#e6ffe6"}},
    "Klasik": {"Yüksek": {"color": "white", "bg": "red"}, "Orta": {"color": "black", "bg": "yellow"}, "Düşük": {"color": "white", "bg": "green"},
               "Deadline": {"gecmis":"grey", "turuncu":"orange", "sari":"yellow", "yesil":"green"}}
}
p = tema_paleti[tema]

# Grid için Bitiş Tarihi string formatı
df_grid = df_filtre.copy()
df_grid['Bitiş Tarihi'] = df_grid['Bitiş Tarihi'].astype(str).str.replace('T', ' ')

# JS: deadline hücresinde renk ve yazı
deadline_style = JsCode(f"""
function(params) {{
    if (!params.value) return null;
    let now = new Date();
    let deadline = Date.parse(params.value);
    let bg = '';
    if (!deadline) {{ bg = 'white'; }}
    else {{
        let diff = (deadline - now)/(1000*60*60*24);
        if(diff<0) bg='{p['Deadline']['gecmis']}';
        else if(diff<=3) bg='{p['Deadline']['turuncu']}';
        else if(diff<=7) bg='{p['Deadline']['sari']}';
        else bg='{p['Deadline']['yesil']}';
    }}
    return {{
        'color':'black', 
        'backgroundColor':bg,
        'display':'flex',
        'alignItems':'center',
        'justifyContent':'center',
        'fontWeight':'bold',
        'textAlign':'center'
    }};
}}
""")

priority_style = JsCode(f"""
function(params) {{
    if (params.value == 'Yüksek') return {{'color': '{p['Yüksek']['color']}', 'backgroundColor': '{p['Yüksek']['bg']}'}} ;
    if (params.value == 'Orta') return {{'color': '{p['Orta']['color']}', 'backgroundColor': '{p['Orta']['bg']}'}} ;
    if (params.value == 'Düşük') return {{'color': '{p['Düşük']['color']}', 'backgroundColor': '{p['Düşük']['bg']}'}} ;
    return null;
}};
""")

# Not sütunu için style (uzun metinler alt satıra geçer)
not_style = JsCode("""
function(params) {
    return {
        'white-space': 'normal',
        'overflow-wrap': 'break-word',
        'line-height': '18px',
        'padding': '5px'
    };
}
""")

# GridOptionsBuilder
gb = GridOptionsBuilder.from_dataframe(df_grid)
gb.configure_column("Öncelik", cellStyle=priority_style)
gb.configure_column("Bitiş Tarihi", cellStyle=deadline_style)
gb.configure_column("Tamamlandı", editable=True, cellRenderer="agCheckboxCellRenderer")
gb.configure_column("Not", editable=True, cellStyle=not_style, autoHeight=True)  # Not sütunu için style ve autoHeight
gridOptions = gb.build()

# Grid gösterimi
grid_response = AgGrid(
    df_grid,
    gridOptions=gridOptions,
    update_mode="MODEL_CHANGED",
    allow_unsafe_jscode=True,
    theme="streamlit",
    fit_columns_on_grid_load=True
)





# Grid’de yapılan değişiklikleri orijinal df’ye yansıt
updated_df = pd.DataFrame(grid_response['data'])
for idx, row in updated_df.iterrows():
    mask = df['ID'] == row['ID']
    df.loc[mask, 'Tamamlandı'] = row['Tamamlandı']
    df.loc[mask, 'Not'] = row['Not']

# CSV’ye kaydet
df.to_csv(DOSYA_ADI, index=False)

#----------------------------------------Silme Bölümü----------------------------------------
st.markdown("---")
st.subheader("🗑️ Görev Sil")
with st.form("gorev_sil_form"):
    if not df.empty:
        # ID ve görev adı birlikte gösterilecek
        secim_listesi = [f"{row['ID']} - {row['Görev']}" for _, row in df.iterrows()]
        secim = st.selectbox("Silmek istediğiniz görevi seçin", secim_listesi)
        sil_button = st.form_submit_button("Sil")
        if sil_button:
            secilen_id = int(secim.split(" - ")[0])
            df = df[df["ID"] != secilen_id].reset_index(drop=True)
            df.to_csv(DOSYA_ADI, index=False)
            st.success(f"✅ Görev silindi.")
            st.rerun()
    else:
        st.info("Silinecek görev yok.")
        st.form_submit_button("Sil", disabled=True)

        #----------------------------------------silme Bölümü Sonu----------------------------------------

#----------------------------------------Takvim Görselleştirme----------------------------------------
import calendar
import streamlit as st
from datetime import datetime
import pandas as pd

st.markdown("---")
st.subheader("📅 Görev Takvimi")

# Takvim üstünde ay ve yıl seçici
col1, col2 = st.columns(2)
with col1:
    current_year = datetime.now().year
    secilen_yil = st.selectbox("Yıl", list(range(current_year - 1, current_year + 5)), index=1)
with col2:
    current_month = datetime.now().month
    secilen_ay = st.selectbox("Ay", list(range(1, 13)), index=current_month - 1)

# Ayın takvimini al
cal = calendar.Calendar(firstweekday=0)  # Pazartesi = 0
ay_gunleri = cal.monthdayscalendar(secilen_yil, secilen_ay)

# Görevleri ilgili günlere dağıt
gorevler_ay = {}
for _, row in df.iterrows():
    try:
        tarih = pd.to_datetime(row["Bitiş Tarihi"])
        if tarih.year == secilen_yil and tarih.month == secilen_ay:
            gun = tarih.day
            if gun not in gorevler_ay:
                gorevler_ay[gun] = []
            if pd.notna(row["Görev"]) and row["Görev"] != "":
                gorevler_ay[gun].append(row["Görev"])
    except:
        continue

# Takvim tablo olarak gösterimi
st.markdown("<style>td{vertical-align: top;}</style>", unsafe_allow_html=True)
html = "<table border='1' style='border-collapse: collapse; width: 100%; text-align: left;'>"
html += "<tr>"
for gun_adi in ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]:
    html += f"<th style='padding:5px'>{gun_adi}</th>"
html += "</tr>"

for hafta in ay_gunleri:
    html += "<tr>"
    for gun in hafta:
        if gun == 0:
            html += "<td style='padding:5px; height:80px'></td>"
        else:
            html += f"<td style='padding:5px; height:80px; vertical-align:top; font-size:12px;'>"
            html += f"<b>{gun}</b><br>"
            if gun in gorevler_ay:
                for gorev in gorevler_ay[gun]:
                    html += f"• {gorev}<br>"
            html += "</td>"
    html += "</tr>"
html += "</table>"

st.markdown(html, unsafe_allow_html=True)


#----------------------------------------Takvim Görselleştirme Sonu----------------------------------------

#----------------------------------------Sidebar Görev Detayları----------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📋 Görev Detayları")

# Tarih seçimi için sidebar date_input
secili_tarih_sidebar = st.sidebar.date_input("Gün seçin", key="detay_tarih")

# Seçilen tarihe ait görevleri filtrele
detay_df_sidebar = df[pd.to_datetime(df["Bitiş Tarihi"]).dt.date == secili_tarih_sidebar]

if not detay_df_sidebar.empty:
    for idx, row in detay_df_sidebar.iterrows():
        st.sidebar.markdown(f"**Görev:** {row['Görev']}")
        st.sidebar.markdown(f"**Öncelik:** {row['Öncelik']}")
        st.sidebar.markdown(f"**Bitiş Tarihi:** {row['Bitiş Tarihi']}")
        st.sidebar.markdown(f"**Tamamlandı:** {'✅' if row['Tamamlandı'] else '❌'}")
        st.sidebar.markdown(f"**Not:** {row['Not']}")
        st.sidebar.markdown("---")
else:
    st.sidebar.info("Bu tarihe ait görev bulunmuyor.")

#----------------------------------------Sidebar Görev Detayları Sonu----------------------------------------

#----------------------------------------Görevleri Excel olarak indir----------------------------------------
import io

st.markdown("---")
st.subheader("💾 Görevleri Excel Olarak İndir")

# Excel’e yazdırmak için BytesIO
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Görevler')
    processed_data = output.getvalue()
    return processed_data

excel_data = to_excel(df)

st.download_button(
    label="📥 Excel Olarak İndir",
    data=excel_data,
    file_name="gorevler.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
#----------------------------------------Görevleri Excel olarak indir Sonu----------------------------------------
# ---------------- Hatırlatıcı ----------------
st.sidebar.markdown("### ⏰ Görev Hatırlatıcı")

# Görevleri seçmek için dropdown
if len(df) > 0:
    selected_task_index = st.sidebar.selectbox("Hatırlatma ayarla:", range(len(df)), format_func=lambda i: df.iloc[i]["Görev"])
    reminder_minutes = st.sidebar.number_input(
        "Kaç dakika önce hatırlatma gönderilsin?", min_value=1, value=30, step=1
    )

    if st.sidebar.button("Hatırlatıcıyı Ayarla"):
        task = df.iloc[selected_task_index]
        deadline_str = task["Bitiş Tarihi"]

        # Bitiş tarihi stringini datetime objesine çevir
        try:
            deadline = pd.to_datetime(deadline_str)
            now = pd.Timestamp.now()
            reminder_time = deadline - pd.Timedelta(minutes=reminder_minutes)

            # Eğer reminder zamanı geçmişse uyar
            if reminder_time <= now:
                st.warning("⚠️ Hatırlatma zamanı geçmiş! Farklı bir dakika girin.")
            else:
                # Hatırlatma ayarla
                st.success(f"✅ '{task['Görev']}' için hatırlatma ayarlandı ({reminder_minutes} dakika önce).")

                # Burada mail gönderme işini zaman kontrolüyle yapıyoruz
                import time
                import threading

                def send_reminder_later(email, task_name, send_time):
                    while True:
                        now = pd.Timestamp.now()
                        if now >= send_time:
                            subject = f"Hatırlatma: {task_name}"
                            body = f"Merhaba!\n\n'{task_name}' adlı görevinizin bitişine {reminder_minutes} dakika kaldı. İyi çalışmalar!"
                            msg = EmailMessage()
                            msg["Subject"] = subject
                            msg["From"] = EMAIL_ADDRESS
                            msg["To"] = email
                            msg.set_content(body)
                            try:
                                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                                    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                                    smtp.send_message(msg)
                                st.info(f"📩 '{task_name}' için hatırlatma maili gönderildi.")
                            except Exception as e:
                                st.error(f"Hatırlatma gönderilemedi: {e}")
                            break
                        time.sleep(30)  # 30 saniyede bir kontrol

                # Thread ile arka planda çalıştır
                threading.Thread(target=send_reminder_later, args=(users[current_user]["email"], task["Görev"], reminder_time), daemon=True).start()

        except Exception as e:
            st.error("❌ Bitiş tarihi formatı hatalı. Lütfen 'YYYY-MM-DD HH:MM' formatında girin.")
else:
    st.sidebar.info("📌 Önce görev ekleyin.")

        

