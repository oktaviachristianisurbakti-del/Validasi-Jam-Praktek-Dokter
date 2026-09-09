import streamlit as st
import pandas as pd
import datetime

# Konfigurasi Halaman Web
st.set_page_config(page_title="Dashboard Master Kehadiran Dokter", page_icon="🏥", layout="wide")

# Inisialisasi Database Sementara di Sesi Web
if 'database_kehadiran' not in st.session_state:
    st.session_state.database_kehadiran = []

# Judul Aplikasi
st.title("🏥 Dashboard Master & Monitoring Kehadiran Seluruh Dokter")
st.markdown("Pusat data terintegrasi untuk mencatat, merekam, dan memantau jam praktek seluruh tenaga medis di berbagai fasilitas kesehatan.")

# --- SIDEBAR: INPUT DATA KEHADIRAN DOKTER ---
st.sidebar.header("➕ Tambah Catatan Kehadiran")
input_nama = st.sidebar.text_input("Nama Lengkap Dokter:", placeholder="Contoh: dr. Dimas, Sp.A")

pilihan_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
input_hari = st.sidebar.selectbox("Pilih Hari:", pilihan_hari)

input_faskes = st.sidebar.text_input("Nama Faskes / Klinik / RS:", placeholder="Contoh: Klinik Bebita")

st.sidebar.markdown("---")
st.sidebar.subheader("🕒 Jam Operasional & Istirahat")

col_m1, col_m2 = st.sidebar.columns(2)
with col_m1:
    input_mulai = st.time_input("Jam Mulai Masuk", value=datetime.time(9, 0))
with col_m2:
    input_selesai = st.time_input("Jam Selesai Pulang", value=datetime.time(19, 0))

ada_istirahat = st.sidebar.checkbox("Ada Jam Istirahat di Tengah Waktu?", value=True)

input_istirahat_mulai = None
input_istirahat_selesai = None
durasi_istirahat_jam = 0.0

if ada_istirahat:
    col_i1, col_i2 = st.sidebar.columns(2)
    with col_i1:
        input_istirahat_mulai = st.time_input("Mulai Istirahat", value=datetime.time(12, 0))
    with col_i2:
        input_istirahat_selesai = st.time_input("Selesai Istirahat", value=datetime.time(15, 0))

if st.sidebar.button("💾 Simpan ke Database"):
    if input_nama.strip() == "" or input_faskes.strip() == "":
        st.sidebar.error("Nama Dokter dan Faskes tidak boleh kosong!")
    else:
        t_mulai_menit = input_mulai.hour * 60 + input_mulai.minute
        t_selesai_menit = input_selesai.hour * input_selesai.minute if False else (input_selesai.hour * 60 + input_selesai.minute)
        
        if t_selesai_menit < t_mulai_menit:
            t_selesai_menit += 24 * 60
            
        total_kotor_menit = t_selesai_menit - t_mulai_menit
        
        durasi_istirahat_menit = 0
        i_mulai_menit = None
        i_selesai_menit = None
        
        if ada_istirahat and input_istirahat_mulai and input_istirahat_selesai:
            i_mulai_menit = input_istirahat_mulai.hour * 60 + input_istirahat_mulai.minute
            i_selesai_menit = input_istirahat_selesai.hour * 60 + input_istirahat_selesai.minute
            if i_selesai_menit < i_mulai_menit:
                i_selesai_menit += 24 * 60
            
            durasi_istirahat_menit = max(0, i_selesai_menit - i_mulai_menit)
            durasi_istirahat_jam = round(durasi_istirahat_menit / 60, 2)
            info_istirahat_str = f"{input_istirahat_mulai.strftime('%H:%M')} - {input_istirahat_selesai.strftime('%H:%M')} ({durasi_istirahat_jam} Jam)"
        else:
            info_istirahat_str = "Tidak ada"
            
        durasi_bersih_menit = max(0, total_kotor_menit - durasi_istirahat_menit)
        durasi_bersih_jam = round(durasi_bersih_menit / 60, 2)
        
        status_beban = "Padat 🔴" if durasi_bersih_jam > 5 else "Normal 🟢"

        st.session_state.database_kehadiran.append({
            "Hari": input_hari,
            "Nama Dokter": input_nama,
            "Faskes": input_faskes,
            "Jam Masuk": input_mulai.strftime("%H:%M"),
            "Jam Pulang": input_selesai.strftime("%H:%M"),
            "Waktu Istirahat": info_istirahat_str,
            "Total Jam Praktek": durasi_bersih_jam,
            "Status": status_beban,
            "Obj_Mulai": t_mulai_menit,
            "Obj_Selesai": t_selesai_menit,
            "Obj_Istirahat_Mulai": i_mulai_menit,
            "Obj_Istirahat_Selesai": i_selesai_menit
        })
        st.sidebar.success(f"Berhasil merekam jadwal {input_nama}!")

# --- FITUR HAPUS DATA DI SIDEBAR ---
if len(st.session_state.database_kehadiran) > 0:
    st.sidebar.markdown("---")
    st.sidebar.header("🗑️ Hapus Data Salah Rekam")
    
    # Membuat daftar pilihan berdasarkan indeks dan ringkasan data
    list_pilihan_hapus = [
        f"ID {idx}: {item['Nama Dokter']} ({item['Hari']} - {item['Faskes']})"
        for idx, item in enumerate(st.session_state.database_kehadiran)
    ]
    
    data_terpilih_hapus = st.sidebar.selectbox("Pilih Data yang Akan Dihapus:", list_pilihan_hapus)
    
    if st.sidebar.button("❌ Hapus Data Terpilih"):
        # Ambil indeks dari string pilihan (misal "ID 0: ...")
        id_to_remove = int(data_terpilih_hapus.split(":")[0].replace("ID", "").strip())
        st.session_state.database_kehadiran.pop(id_to_remove)
        st.sidebar.success("Data berhasil dihapus!")
        st.rerun()

    if st.sidebar.button("⚠️ Hapus Seluruh Database"):
        st.session_state.database_kehadiran = []
        st.sidebar.warning("Semua data telah dibersihkan.")
        st.rerun()

# --- TAMPILAN UTAMA DASHBOARD MASTER ---
st.markdown("---")

if len(st.session_state.database_kehadiran) > 0:
    df_master = pd.DataFrame(st.session_state.database_kehadiran)
    
    total_catatan = len(df_master)
    total_dokter_unik = df_master["Nama Dokter"].nunique()
    total_akumulasi_jam = df_master["Total Jam Praktek"].sum()
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.metric(label="Total Rekaman Jadwal", value=f"{total_catatan} Entri")
    with col_c2:
        st.metric(label="Jumlah Dokter Terdaftar", value=f"{total_dokter_unik} Dokter")
    with col_c3:
        st.metric(label="Akumulasi Seluruh Jam Praktek", value=f"{total_akumulasi_jam:.1f} Jam")
        
    st.markdown("### 🔍 Panel Filter & Pencarian Lanjutan")
    
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        filter_hari = st.selectbox("Filter Hari:", ["Semua Hari"] + pilihan_hari)
        
    with f_col2:
        list_dokter_unik = ["Semua Dokter"] + sorted(df_master["Nama Dokter"].unique().tolist())
        filter_dokter = st.selectbox("Filter Nama Dokter:", list_dokter_unik)
        
    with f_col3:
        filter_jam_aktif = st.checkbox("Cek Dokter yang Praktek pada Jam Tertentu?")
        
    target_jam = None
    if filter_jam_aktif:
        target_jam = st.time_input("Pilih Target Jam (Cek siapa yang bertugas):", value=datetime.time(14, 0))

    # --- PROSES FILTER DATA ---
    df_tampil = df_master.copy()
    
    if filter_hari != "Semua Hari":
        df_tampil = df_tampil[df_tampil["Hari"] == filter_hari]
        
    if filter_dokter != "Semua Dokter":
        df_tampil = df_tampil[df_tampil["Nama Dokter"] == filter_dokter]
        
    if filter_jam_aktif and target_jam is not None:
        target_menit = target_jam.hour * 60 + target_jam.minute
        
        def cek_sedang_praktek(row):
            m = row["Obj_Mulai"]
            s = row["Obj_Selesai"]
            i_m = row["Obj_Istirahat_Mulai"]
            i_s = row["Obj_Istirahat_Selesai"]
            
            dalam_rentang = (m <= target_menit <= s)
            
            if dalam_rentang and i_m is not None and i_s is not None:
                sedang_istirahat = (i_m <= target_menit <= i_s)
                if sedang_istirahat:
                    return False
            return dalam_rentang
                
        df_tampil = df_tampil[df_tampil.apply(cek_sedang_praktek, axis=1)]

    # Kolom yang akan ditampilkan (ditambahkan nomor ID baris agar jelas)
    df_tampil_clean = df_tampil[["Hari", "Nama Dokter", "Faskes", "Jam Masuk", "Jam Pulang", "Waktu Istirahat", "Total Jam Praktek", "Status"]].copy()
    df_tampil_clean.insert(0, "ID", df_tampil.index)

    st.markdown(f"### 📋 Hasil Data Kehadiran ({len(df_tampil_clean)} Data Ditemukan)")
    st.dataframe(df_tampil_clean, use_container_width=True)
    
    # Grafik Akumulasi Jam per Dokter
    st.markdown("### 📊 Grafik Akumulasi Beban Jam Praktek per Dokter")
    if not df_tampil_clean.empty:
        df_grafik = df_tampil_clean.groupby("Nama Dokter")["Total Jam Praktek"].sum()
        st.bar_chart(df_grafik)
    else:
        st.info("Tidak ada dokter yang aktif praktek pada filter jam tersebut (kemungkinan sedang jam istirahat atau libur).")
    
    # Export Data
    st.markdown("---")
    st.subheader("📥 Export Laporan Sesuai Filter")
    csv_master = df_tampil_clean.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data ke CSV (Excel)",
        data=csv_master,
        file_name='Laporan_Kehadiran_Dokter_Detail.csv',
        mime='text/csv',
    )
else:
    st.info("ℹ️ Belum ada data kehadiran yang dimasukkan. Silakan input nama dokter dan jadwalnya melalui panel di sebelah kiri.")
