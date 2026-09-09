import streamlit as st
import pandas as pd
import datetime

# Konfigurasi Halaman Web
st.set_page_config(page_title="Dashboard Analisis Beban Kerja & FTE Dokter JKN", page_icon="🏥", layout="wide")

# Inisialisasi Database Sementara di Sesi Web
if 'database_kehadiran' not in st.session_state:
    st.session_state.database_kehadiran = []

# Judul Aplikasi
st.title("🏥 Dashboard Analisis Beban Kerja, Rasio JKN & Kapasitas FTE")
st.markdown("Pusat monitoring kehadiran tenaga medis berbasis konversi tenaga riil (*Full-Time Equivalent / FTE*) terhadap kepesertaan JKN.")

# --- SIDEBAR: PENGATURAN PARAMETER ---
st.sidebar.header("⚙️ Pengaturan Standar & FTE")
jumlah_peserta_faskes = st.sidebar.number_input("Total Peserta JKN di Faskes:", min_value=500, max_value=100000, value=7873, step=500)
standar_rasio = st.sidebar.number_input("Standar Rasio Peserta per Dokter (FTE):", min_value=1000, max_value=10000, value=5000, step=500)

# Standar jam kerja 1 dokter full-time dalam seminggu (biasanya 40 jam)
standar_jam_fulltime_mingguan = st.sidebar.number_input("Standar Jam Kerja 1 Dokter Full-Time / Minggu:", min_value=20, max_value=50, value=40)

sistem_hari_kerja = st.sidebar.selectbox("Sistem Hari Kerja Faskes:", ["5 Hari Kerja (Maks 8 Jam/Hari)", "6 Hari Kerja (Maks 7 Jam/Hari)"])
max_jam_harian = 8 if "5 Hari" in sistem_hari_kerja else 7

st.sidebar.markdown("---")
st.sidebar.header("📁 Metode Input Data")
metode_input = st.sidebar.radio("Pilih cara input:", ["Upload File Excel/CSV", "Input Manual (Form)"])

pilihan_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

if metode_input == "Upload File Excel/CSV":
    st.sidebar.markdown("---")
    st.sidebar.subheader("📤 Upload Jadwal Massal")
    uploaded_file = st.sidebar.file_uploader("Pilih file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
                
            df_upload.columns = df_upload.columns.str.strip()
                
            if st.sidebar.button("📥 Proses & Masukkan ke Database"):
                count_sukses = 0
                for _, row in df_upload.iterrows():
                    nama = str(row.get("Nama Dokter", row.get("Nama", ""))).strip()
                    hari = str(row.get("Hari", "Senin")).strip()
                    faskes = str(row.get("Faskes", row.get("Klinik", ""))).strip()
                    
                    if not nama or nama == "nan" or not faskes or faskes == "nan":
                        continue
                        
                    j_masuk_raw = row.get("Jam Masuk", row.get("Mulai", "08:00"))
                    j_pulang_raw = row.get("Jam Pulang", row.get("Selesai", "16:00"))
                    
                    if isinstance(j_masuk_raw, datetime.time):
                        m_jam, m_menit = j_masuk_raw.hour, j_masuk_raw.minute
                    else:
                        try:
                            m_jam, m_menit = map(int, str(j_masuk_raw).strip().split(':')[:2])
                        except:
                            m_jam, m_menit = 8, 0
                            
                    if isinstance(j_pulang_raw, datetime.time):
                        p_jam, p_menit = j_pulang_raw.hour, j_pulang_raw.minute
                    else:
                        try:
                            p_jam, p_menit = map(int, str(j_pulang_raw).strip().split(':')[:2])
                        except:
                            p_jam, p_menit = 16, 0
                        
                    t_mulai_menit = m_jam * 60 + m_menit
                    t_selesai_menit = p_jam * 60 + p_menit
                    if t_selesai_menit < t_mulai_menit:
                        t_selesai_menit += 24 * 60
                        
                    durasi_menit = max(0, t_selesai_menit - t_mulai_menit)
                    durasi_jam = round(durasi_menit / 60, 2)
                    
                    warning_harian = durasi_jam > max_jam_harian
                    status_beban = "Lebih Batas Harian ⚠️" if warning_harian else ("Padat 🔴" if durasi_jam > 5 else "Normal 🟢")
                    
                    st.session_state.database_kehadiran.append({
                        "Hari": hari,
                        "Nama Dokter": nama,
                        "Faskes": faskes,
                        "Jam Masuk": f"{m_jam:02d}:{m_menit:02d}",
                        "Jam Pulang": f"{p_jam:02d}:{p_menit:02d}",
                        "Total Jam Praktek": durasi_jam,
                        "Status": status_beban,
                        "Obj_Mulai": t_mulai_menit,
                        "Obj_Selesai": t_selesai_menit
                    })
                    count_sukses += 1
                    
                st.sidebar.success(f"Berhasil mengimpor {count_sukses} baris jadwal!")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Gagal membaca file: {e}")

else:
    # --- INPUT MANUAL ---
    st.sidebar.markdown("---")
    st.sidebar.header("➕ Form Input Satuan")
    input_nama = st.sidebar.text_input("Nama Lengkap Dokter:")
    input_hari = st.sidebar.selectbox("Pilih Hari:", pilihan_hari)
    input_faskes = st.sidebar.text_input("Nama Faskes:")

    col_m1, col_m2 = st.sidebar.columns(2)
    with col_m1:
        input_mulai = st.time_input("Jam Masuk", value=datetime.time(9, 0))
    with col_m2:
        input_selesai = st.time_input("Jam Pulang", value=datetime.time(12, 0))

    if st.sidebar.button("💾 Simpan ke Database"):
        if input_nama.strip() == "" or input_faskes.strip() == "":
            st.sidebar.error("Nama dan Faskes wajib diisi!")
        else:
            t_mulai_menit = input_mulai.hour * 60 + input_mulai.minute
            t_selesai_menit = input_selesai.hour * 60 + input_selesai.minute
            if t_selesai_menit < t_mulai_menit:
                t_selesai_menit += 24 * 60
            durasi_menit = max(0, t_selesai_menit - t_mulai_menit)
            durasi_jam = round(durasi_menit / 60, 2)
            
            warning_harian = durasi_jam > max_jam_harian
            status_beban = "Lebih Batas Harian ⚠️" if warning_harian else ("Padat 🔴" if durasi_jam > 5 else "Normal 🟢")

            st.session_state.database_kehadiran.append({
                "Hari": input_hari,
                "Nama Dokter": input_nama,
                "Faskes": input_faskes,
                "Jam Masuk": input_mulai.strftime("%H:%M"),
                "Jam Pulang": input_selesai.strftime("%H:%M"),
                "Total Jam Praktek": durasi_jam,
                "Status": status_beban,
                "Obj_Mulai": t_mulai_menit,
                "Obj_Selesai": t_selesai_menit
            })
            st.sidebar.success(f"Berhasil merekam jadwal {input_nama}!")

# --- KELOLA DATABASE / HAPUS ---
if len(st.session_state.database_kehadiran) > 0:
    st.sidebar.markdown("---")
    st.sidebar.header("🗑️ Kelola Database")
    
    if st.sidebar.button("⚠️ Hapus Seluruh Database (Reset)"):
        st.session_state.database_kehadiran = []
        st.sidebar.warning("Database dibersihkan.")
        st.rerun()

    list_pilihan_hapus = [
        f"ID {idx}: {item['Nama Dokter']} ({item['Hari']} | {item['Jam Masuk']}-{item['Jam Pulang']})"
        for idx, item in enumerate(st.session_state.database_kehadiran)
    ]
    data_terpilih_hapus = st.sidebar.selectbox("Pilih Data untuk Dihapus:", list_pilihan_hapus)
    
    if st.sidebar.button("❌ Hapus Data Terpilih"):
        id_to_remove = int(data_terpilih_hapus.split(":")[0].replace("ID", "").strip())
        st.session_state.database_kehadiran.pop(id_to_remove)
        st.sidebar.success("Data berhasil dihapus!")
        st.rerun()

# --- DASHBOARD UTAMA ---
st.markdown("---")

if len(st.session_state.database_kehadiran) > 0:
    df_master = pd.DataFrame(st.session_state.database_kehadiran)
    
    # --- PANEL FILTER & PENCARIAN DI ATAS ---
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
        target_jam = st.time_input("Pilih Target Jam:", value=datetime.time(10, 0))

    # --- PROSES FILTER DATA ---
    df_tampil = df_master.copy()
    if filter_hari != "Semua Hari":
        df_tampil = df_tampil[df_tampil["Hari"] == filter_hari]
    if filter_dokter != "Semua Dokter":
        df_tampil = df_tampil[df_tampil["Nama Dokter"] == filter_dokter]
        
    if filter_jam_aktif and target_jam is not None:
        target_menit = target_jam.hour * 60 + target_jam.minute
        def cek_sedang_praktek(row):
            return row["Obj_Mulai"] <= target_menit <= row["Obj_Selesai"]
        df_tampil = df_tampil[df_tampil.apply(cek_sedang_praktek, axis=1)]

    # --- KALKULASI FTE (Full-Time Equivalent) ---
    # Hitung total jam seluruh dokter dalam database global
    total_jam_global = df_master["Total Jam Praktek"].sum()
    headcount_dokter = df_master["Nama Dokter"].nunique()
    
    # Menghitung tenaga riil (FTE) berdasarkan total jam dibagi standar jam fulltime (misal 40 jam)
    fte_total = round(total_jam_global / standar_jam_fulltime_mingguan, 2)
    
    # Kebutuhan dokter ideal berdasarkan peserta JKN dan rasio (misal 7873 / 5000 = ~1.58 dokter)
    dokter_ideal_jkn = round(jumlah_peserta_faskes / standar_rasio, 2)

    st.markdown("---")
    st.markdown("### 📊 Analisis Kapasitas Riil: Headcount vs Tenaga FTE (Full-Time Equivalent)")

    with st.expander("ℹ️ Penjelasan Mengapa Tenaga Riil (FTE) Berbeda dari Jumlah Orang (Headcount)", expanded=True):
        st.markdown(f"""
        * **Headcount (Jumlah Orang):** Terdapat **{headcount_dokter} dokter** yang terdaftar di faskes ini.
        * **Total Akumulasi Jam:** Seluruh dokter tersebut jika ditotal jam prakteknya menghasilkan **{total_jam_global:.1f} jam/minggu**.
        * **Konversi Tenaga Riil (FTE):** Berdasarkan standar **{standar_jam_fulltime_mingguan} jam/minggu** untuk 1 dokter penuh, kapasitas riil tenaga medis Anda setara dengan **{fte_total} Dokter Full-Time**. 
        * *Kesimpulan:* Meskipun secara fisik ada {headcount_dokter} orang, kekuatan layanan faskes Anda dihitung secara proporsional berdasarkan jam kerjanya.
        """)

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        st.metric(label="Jumlah Orang (Headcount)", value=f"{headcount_dokter} Orang")
    with col_f2:
        st.metric(label="Tenaga Riil (FTE)", value=f"{fte_total} FTE")
    with col_f3:
        st.metric(label="Kebutuhan Ideal JKN", value=f"{dokter_ideal_jkn} FTE")
    with col_f4:
        status_fte = "Kapasitas Memadai ✅" if fte_total >= dokter_ideal_jkn else "Defisit Tenaga (Kurang) ⚠️"
        st.metric(label="Evaluasi Rasio JKN", value=status_fte)

    st.markdown("---")
    
    # Metrik Filter Aktif
    total_catatan = len(df_tampil)
    total_jam_filter = df_tampil["Total Jam Praktek"].sum()
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.metric(label="Total Sesi Terpilih", value=f"{total_catatan} Sesi")
    with col_c2:
        st.metric(label="Akumulasi Jam (Filter)", value=f"{total_jam_filter:.1f} Jam")
    with col_c3:
        st.metric(label="Rata-rata Jam per Dokter", value=f"{(total_jam_filter / df_tampil['Nama Dokter'].nunique() if df_tampil['Nama Dokter'].nunique() > 0 else 0):.1f} Jam")

    # --- TABEL UTAMA ---
    # Tambahkan kolom kontribusi FTE per dokter di tabel
    df_tampil_clean = df_tampil[["Hari", "Nama Dokter", "Faskes", "Jam Masuk", "Jam Pulang", "Total Jam Praktek", "Status"]].copy()
    df_tampil_clean.insert(0, "ID", df_tampil.index)

    st.markdown(f"### 📋 Rincian Jadwal ({len(df_tampil_clean)} Data Ditemukan)")
    st.dataframe(df_tampil_clean, use_container_width=True)
    
    st.markdown("### 📊 Grafik Akumulasi Jam Praktek per Dokter")
    if not df_tampil_clean.empty:
        df_grafik = df_tampil_clean.groupby("Nama Dokter")["Total Jam Praktek"].sum()
        st.bar_chart(df_grafik)
    else:
        st.info("Tidak ada data yang cocok dengan filter tersebut.")
    
    st.markdown("---")
    st.subheader("📥 Export Laporan")
    csv_master = df_tampil_clean.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data ke CSV (Excel)",
        data=csv_master,
        file_name='Laporan_Analisis_FTE_JKN.csv',
        mime='text/css',
    )
else:
    st.info("ℹ️ Belum ada data. Silakan upload file Excel atau gunakan form manual di sebelah kiri.")
