import streamlit as st
import pandas as pd
import datetime

# Konfigurasi Halaman Web
st.set_page_config(page_title="Dashboard Master Kehadiran Dokter", page_icon="🏥", layout="wide")

# Inisialisasi Database Sementara di Sesi Web (agar data tidak hilang saat input baru)
if 'database_kehadiran' not in st.session_state:
    st.session_state.database_kehadiran = []

# Judul Aplikasi
st.title("🏥 Dashboard Master & Monitoring Kehadiran Seluruh Dokter")
st.markdown("Pusat data terintegrasi untuk mencatat, merekam, dan memantau jam praktek seluruh tenaga medis di berbagai fasilitas kesehatan.")

# --- SIDEBAR: INPUT DATA KEHADIRAN DOKTER ---
st.sidebar.header("➕ Tambah Catatan Kehadiran")
input_nama = st.sidebar.text_input("Nama Lengkap Dokter:", placeholder="Contoh: dr. Budi, Sp.OG")

pilihan_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
input_hari = st.sidebar.selectbox("Pilih Hari:", pilihan_hari)

input_faskes = st.sidebar.text_input("Nama Faskes / Klinik / RS:", placeholder="Contoh: RS Bhakti Husada")

col_m1, col_m2 = st.sidebar.columns(2)
with col_m1:
    input_mulai = st.time_input("Jam Mulai", value=datetime.time(8, 0))
with col_m2:
    input_selesai = st.time_input("Jam Selesai", value=datetime.time(12, 0))

input_istirahat = st.sidebar.number_input("Waktu Istirahat (Jam):", min_value=0.0, max_value=3.0, step=0.25, value=0.0)

if st.sidebar.button("💾 Simpan ke Database"):
    if input_nama.strip() == "" or input_faskes.strip() == "":
        st.sidebar.error("Nama Dokter dan Faskes tidak boleh kosong!")
    else:
        # Hitung durasi
        t_mulai = input_mulai.hour + input_mulai.minute / 60
        t_selesai = input_selesai.hour + input_selesai.minute / 60
        durasi_kotor = t_selesai - t_mulai
        if durasi_kotor < 0:
            durasi_kotor += 24
        durasi_bersih = max(0.0, durasi_kotor - input_istirahat)
        
        status_beban = "Padat 🔴" if durasi_bersih > 5 else "Normal 🟢"

        # Simpan ke session state
        st.session_state.database_kehadiran.append({
            "Hari": input_hari,
            "Nama Dokter": input_nama,
            "Faskes": input_faskes,
            "Jam Mulai": input_mulai.strftime("%H:%M"),
            "Jam Selesai": input_selesai.strftime("%H:%M"),
            "Istirahat (Jam)": input_istirahat,
            "Total Jam": round(durasi_bersih, 2),
            "Status": status_beban
        })
        st.sidebar.success(f"Berhasil merekam jadwal {input_nama}!")

# Tombol untuk Reset/Hapus Database jika diperlukan
if st.sidebar.button("🗑️ Reset Semua Data"):
    st.session_state.database_kehadiran = []
    st.sidebar.warning("Database telah dibersihkan.")

# --- TAMPILAN UTAMA DASHBOARD MASTER ---
st.markdown("---")

if len(st.session_state.database_kehadiran) > 0:
    df_master = pd.DataFrame(st.session_state.database_kehadiran)
    
    # Metrik Ringkasan Utama
    total_catatan = len(df_master)
    total_dokter_unik = df_master["Nama Dokter"].nunique()
    total_akumulasi_jam = df_master["Total Jam"].sum()
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.metric(label="Total Rekaman Jadwal", value=f"{total_catatan} Entri")
    with col_c2:
        st.metric(label="Jumlah Dokter Terdaftar", value=f"{total_dokter_unik} Dokter")
    with col_c3:
        st.metric(label="Akumulasi Seluruh Jam Praktek", value=f"{total_akumulasi_jam:.1f} Jam")
        
    st.markdown("### 📋 Tabel Master Seluruh Kehadiran Dokter")
    
    # Fitur Filter opsional di atas tabel
    filter_hari = st.selectbox("Filter berdasarkan Hari:", ["Semua Hari"] + pilihan_hari)
    if filter_hari != "Semua Hari":
        df_tampil = df_master[df_master["Hari"] == filter_hari]
    else:
        df_tampil = df_master
        
    st.dataframe(df_tampil, use_container_width=True)
    
    # Grafik Akumulasi Jam per Dokter
    st.markdown("### 📊 Grafik Akumulasi Beban Jam Praktek per Dokter")
    df_grafik = df_master.groupby("Nama Dokter")["Total Jam"].sum()
    st.bar_chart(df_grafik)
    
    # Export Master Data ke CSV
    st.markdown("---")
    st.subheader("📥 Export Seluruh Database Laporan")
    csv_master = df_master.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Seluruh Database ke CSV (Excel)",
        data=csv_master,
        file_name='Master_Database_Kehadiran_Dokter.csv',
        mime='text/csv',
    )
else:
    st.info("ℹ️ Belum ada data kehadiran yang dimasukkan. Silakan input nama dokter dan jadwalnya melalui panel di sebelah kiri.")
