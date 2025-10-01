import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import os
from datetime import datetime

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
        
        
        

