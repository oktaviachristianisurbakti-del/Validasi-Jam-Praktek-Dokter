import streamlit as st
import pandas as pd
import datetime

# Konfigurasi Halaman Web
st.set_page_config(page_title="Dashboard Jam Praktek Dokter", page_icon="🩺", layout="wide")

# Judul Aplikasi
st.title("🩺 Dashboard Perhitungan Jam Praktek Dokter & Faskes")
st.markdown("Aplikasi otomatis untuk menghitung durasi, akumulasi beban kerja, dan visualisasi jadwal praktek tenaga medis di berbagai fasilitas kesehatan.")

# --- SIDEBAR: INPUT DATA UTAMA ---
st.sidebar.header("📝 Input Data Dokter")
nama_dokter = st.sidebar.text_input("Nama Lengkap Dokter:", "dr. Andi Wijaya, Sp.PD")
pilihan_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
hari_praktek = st.sidebar.selectbox("Pilih Hari:", pilihan_hari)

st.sidebar.markdown("---")
st.sidebar.header("🏥 Tambah Jadwal Faskes")

# Form input dinamis untuk faskes
jumlah_faskes = st.sidebar.number_input("Berapa Faskes hari ini?", min_value=1, max_value=6, value=2)

data_input = []

for i in range(int(jumlah_faskes)):
    st.sidebar.subheader(f"Faskes ke-{i+1}")
    f_nama = st.sidebar.text_input(f"Nama Faskes {i+1}", value=f"Klinik/RS {i+1}", key=f"f_{i}")
    
    col_s1, col_s2 = st.sidebar.columns(2)
    with col_s1:
        f_mulai = st.time_input(f"Mulai {i+1}", value=datetime.time(8, 0), key=f"m_{i}")
    with col_s2:
        f_selesai = st.time_input(f"Selesai {i+1}", value=datetime.time(12, 0), key=f"s_{i}")
        
    f_istirahat = st.sidebar.number_input(f"Istirahat (Jam) {i+1}", min_value=0.0, max_value=3.0, step=0.25, value=0.0, key=f"i_{i}")
    
    data_input.append({
        "Faskes": f_nama,
        "Jam Mulai": f_mulai,
        "Jam Selesai": f_selesai,
        "Istirahat": f_istirahat
    })

# --- PROSES DATA ---
list_hasil = []
for item in data_input:
    t_mulai = item["Jam Mulai"].hour + item["Jam Mulai"].minute / 60
    t_selesai = item["Jam Selesai"].hour + item["Jam Selesai"].minute / 60
    
    durasi_kotor = t_selesai - t_mulai
    if durasi_kotor < 0:
        durasi_kotor += 24 
        
    durasi_bersih = max(0.0, durasi_kotor - item["Istirahat"])
    
    if durasi_bersih > 5:
        status = "Padat 🔴"
    elif durasi_bersih > 0:
        status = "Normal 🟢"
    else:
        status = "-"

    list_hasil.append({
        "Faskes": item["Faskes"],
        "Jam Mulai": item["Jam Mulai"].strftime("%H:%M"),
        "Jam Selesai": item["Jam Selesai"].strftime("%H:%M"),
        "Istirahat (Jam)": item["Istirahat"],
        "Total Jam": round(durasi_bersih, 2),
        "Status": status
    })

df_hasil = pd.DataFrame(list_hasil)
total_jam_hari_ini = df_hasil["Total Jam"].sum()

# --- TAMPILAN UTAMA DASHBOARD ---
st.markdown(f"### 📋 Ringkasan Jadwal untuk: **{nama_dokter}**")
st.markdown(f"📅 **Jadwal Hari:** {hari_praktek}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Jam Praktek", value=f"{total_jam_hari_ini:.1f} Jam")
with col2:
    st.metric(label="Jumlah Faskes", value=f"{len(df_hasil)} Lokasi")
with col3:
    status_beban = "Sangat Padat ⚠️" if total_jam_hari_ini > 8 else "Proporsional ✅"
    st.metric(label="Evaluasi Beban Harian", value=status_beban)

st.markdown("---")

st.subheader("📊 Rincian Waktu Praktek per Faskes")
st.dataframe(df_hasil, use_container_width=True)

if not df_hasil.empty and total_jam_hari_ini > 0:
    st.subheader("📈 Grafik Distribusi Jam Praktek")
    df_chart = df_hasil.set_index("Faskes")["Total Jam"]
    st.bar_chart(df_chart)

st.markdown("---")
st.subheader("📥 Export Data")
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(df_hasil)
st.download_button(
    label="Download Laporan ke CSV",
    data=csv,
    file_name=f'Jadwal_Praktek_{nama_dokter.replace(" ", "_")}.csv',
    mime='text/csv',
)
