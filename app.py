import streamlit as st
import pandas as pd
import datetime
import math

# Konfigurasi Halaman Web
st.set_page_config(page_title="Dashboard Analisis FTE, JKN & Kebutuhan Poli", page_icon="🏥", layout="wide")

# Inisialisasi Database Sementara di Sesi Web
if 'database_kehadiran' not in st.session_state:
    st.session_state.database_kehadiran = []

# Judul Aplikasi
st.title("🏥 Dashboard Analisis Beban Kerja, Rasio JKN & Kebutuhan Poli")
st.markdown("Pusat monitoring kehadiran tenaga medis berbasis analisis kesenjangan (*Gap Analysis*) dan deteksi kebutuhan unit poli simultan.")

# --- GENERATE PILIHAN PERIODE BULAN ---
def generate_periode_list():
    daftar_periode = []
    start_date = datetime.date(2025, 9, 1)
    end_date = datetime.date(2027, 12, 31)
    nama_bulan_indo = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    curr = start_date
    while curr <= end_date:
        label = f"{nama_bulan_indo[curr.month]} {curr.year}"
        daftar_periode.append(label)
        if curr.month == 12:
            curr = datetime.date(curr.year + 1, 1, 1)
        else:
            curr = datetime.date(curr.year, curr.month + 1, 1)
    return daftar_periode

list_periode_tersedia = generate_periode_list()

# --- SIDEBAR: PENGATURAN PARAMETER ---
st.sidebar.header("⚙️ Pengaturan Standar & Kapasitas")
jumlah_peserta_faskes = st.sidebar.number_input("Total Peserta JKN (Default/Global):", min_value=500, max_value=500000, value=7873, step=500)
standar_rasio = st.sidebar.number_input("Standar Target Rasio JKN:", min_value=1000, max_value=10000, value=5000, step=500)
standar_jam_fulltime_mingguan = st.sidebar.number_input("Standar Jam Full-Time / Minggu:", min_value=20, max_value=50, value=40)

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
                    periode = str(row.get("Periode", row.get("Bulan", "September 2025"))).strip()
                    
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
                    status_beban = "Normal 🟢" if durasi_jam <= 8 else "Lebih Batas Harian ⚠️"
                    
                    st.session_state.database_kehadiran.append({
                        "Periode": periode,
                        "Hari": hari,
                        "Nama Dokter": nama,
                        "Faskes": faskes,
                        "Jam Masuk": f"{m_jam:02d}:{m_menit:02d}",
                        "Jam Pulang": f"{p_jam:02d}:{p_menit:02d}",
                        "Total Jam Praktek": durasi_jam,
                        "Status Sesi": status_beban,
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
    input_periode = st.sidebar.selectbox("Pilih Periode Bulan:", list_periode_tersedia)
    input_nama = st.sidebar.text_input("Nama Lengkap Dokter:")
    input_hari = st.sidebar.selectbox("Pilih Hari:", pilihan_hari)
    input_faskes = st.sidebar.text_input("Nama Faskes / Klinik:")

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
            status_beban = "Normal 🟢" if durasi_jam <= 8 else "Lebih Batas Harian ⚠️"

            st.session_state.database_kehadiran.append({
                "Periode": input_periode,
                "Hari": input_hari,
                "Nama Dokter": input_nama,
                "Faskes": input_faskes,
                "Jam Masuk": input_mulai.strftime("%H:%M"),
                "Jam Pulang": input_selesai.strftime("%H:%M"),
                "Total Jam Praktek": durasi_jam,
                "Status Sesi": status_beban,
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
        f"ID {idx}: {item['Nama Dokter']} ({item['Periode']} - {item['Faskes']})"
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
    
    # --- PANEL FILTER & PENCARIAN ---
    st.markdown("### 🔍 Panel Filter & Pencarian Lanjutan")
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        list_periode_unik = ["Semua Periode"] + [p for p in list_periode_tersedia if p in df_master["Periode"].unique().tolist()]
        filter_periode = st.selectbox("Filter Periode (Bulan):", list_periode_unik)
    with f_col2:
        list_faskes_unik = ["Semua Faskes"] + sorted(df_master["Faskes"].unique().tolist())
        filter_faskes = st.selectbox("Filter Faskes:", list_faskes_unik)
    with f_col3:
        list_dokter_unik = ["Semua Dokter"] + sorted(df_master["Nama Dokter"].unique().tolist())
        filter_dokter = st.selectbox("Filter Nama Dokter:", list_dokter_unik)
    with f_col4:
        filter_hari = st.selectbox("Filter Hari:", ["Semua Hari"] + pilihan_hari)

    # --- PROSES FILTER DATA ---
    df_tampil = df_master.copy()
    if filter_periode != "Semua Periode":
        df_tampil = df_tampil[df_tampil["Periode"] == filter_periode]
    if filter_faskes != "Semua Faskes":
        df_tampil = df_tampil[df_tampil["Faskes"] == filter_faskes]
    if filter_dokter != "Semua Dokter":
        df_tampil = df_tampil[df_tampil["Nama Dokter"] == filter_dokter]
    if filter_hari != "Semua Hari":
        df_tampil = df_tampil[df_tampil["Hari"] == filter_hari]

    # --- DINAMIS JUMLAH PESERTA BERDASARKAN FILTER FASKES ---
    peserta_aktif = jumlah_peserta_faskes
    if filter_faskes != "Semua Faskes":
        st.markdown(f"**Pengaturan Khusus untuk Faskes: `{filter_faskes}`**")
        peserta_aktif = st.number_input(f"Masukkan Total Peserta JKN untuk {filter_faskes}:", min_value=100, max_value=500000, value=jumlah_peserta_faskes, step=500)

    # --- KALKULASI FTE & RASIO (1 : Sekian) ---
    total_jam_filter = df_tampil["Total Jam Praktek"].sum()
    headcount_filter = df_tampil["Nama Dokter"].nunique()
    fte_filter = round(total_jam_filter / standar_jam_fulltime_mingguan, 2)
    
    # 1. Rasio Berdasarkan Headcount (Orang Fisik): Peserta / Headcount
    rasio_headcount_val = int(round(peserta_aktif / headcount_filter)) if headcount_filter > 0 else 0
    str_rasio_headcount = f"1 : {rasio_headcount_val:,}"

    # 2. Rasio Berdasarkan Tenaga Riil (FTE): Peserta / FTE
    rasio_fte_val = int(round(peserta_aktif / fte_filter)) if fte_filter > 0 else 0
    str_rasio_fte = f"1 : {rasio_fte_val:,}"

    dokter_ideal_jkn = round(peserta_aktif / standar_rasio, 2)
    gap_fte = round(max(0.0, dokter_ideal_jkn - fte_filter), 2)
    gap_jam_mingguan = round(gap_fte * standar_jam_fulltime_mingguan, 1)
    tambahan_dokter_bulat = math.ceil(gap_fte)

    status_evaluasi_keseluruhan = "Memadai ✅" if fte_filter >= dokter_ideal_jkn else "Defisit Tenaga (Kurang) ⚠️"

    # Deteksi Kebutuhan Poli Simultan
    max_poli_simultan = 1
    if not df_tampil.empty:
        for h in df_tampil["Hari"].unique():
            df_hari = df_tampil[df_tampil["Hari"] == h]
            menit_timeline = [0] * 1440
            for _, row in df_hari.iterrows():
                m_start = row["Obj_Mulai"]
                m_end = row["Obj_Selesai"]
                for m in range(int(m_start), int(m_end)):
                    if m < 1440:
                        menit_timeline[m] += 1
            if menit_timeline:
                maks_hari_ini = max(menit_timeline)
                if maks_hari_ini > max_poli_simultan:
                    max_poli_simultan = maks_hari_ini

    st.markdown("---")
    st.markdown(f"### 📊 Analisis Rasio JKN & Kapasitas Riil (*Gap Analysis*)")

    # Baris Metrik Pertama (Menampilkan Angka Rasio 1 : Sekian)
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric(label="Rasio Headcount (Berdasarkan Orang)", value=str_rasio_headcount, help="Contoh: 7.873 peserta dibagi 4 orang dokter fisik = 1 : 1.968")
    with col_r2:
        st.metric(label="Rasio FTE (Berdasarkan Jam Kerja Riil)", value=str_rasio_fte, help="Angka akurat: Peserta dibagi dengan total jam kerja setara dokter penuh.")
    with col_r3:
        st.metric(label="Target Standar Rasio JKN", value=f"1 : {standar_rasio:,}")

    # Baris Metrik Kedua (Evaluasi Tenaga)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        st.metric(label="Jumlah Orang (Headcount)", value=f"{headcount_filter} Orang")
    with col_f2:
        st.metric(label="Tenaga Riil (FTE)", value=f"{fte_filter} FTE")
    with col_f3:
        st.metric(label="Kebutuhan Ideal JKN", value=f"{dokter_ideal_jkn} FTE")
    with col_f4:
        st.metric(label="Evaluasi Rasio JKN", value=status_evaluasi_keseluruhan)

    # --- KOTAK REKOMENDASI PENAMBAHAN ---
    st.markdown("---")
    st.subheader("💡 Rekomendasi Solusi & Kebutuhan Poli Ideal")
    
    if gap_fte > 0:
        st.warning(f"""
        ⚠️ **Faskes Anda mengalami kekurangan tenaga (Defisit FTE sebesar {gap_fte} FTE dari {peserta_aktif:,} peserta):**
        * **Kekurangan Jumlah Dokter:** Anda membutuhkan tambahan **~{tambahan_dokter_bulat} orang dokter** penuh, atau penambahan akumulasi jam praktek sebanyak **{gap_jam_mingguan} jam per minggu** secara keseluruhan.
        """)
    else:
        st.success(f"✅ **Kapasitas tenaga riil (FTE) untuk {peserta_aktif:,} peserta JKN sudah mencukupi!**")

    st.info(f"""
    🏥 **Analisis Kebutuhan Poli Berdasarkan Jam Beririsan (Simultan):**
    * **Jumlah Unit Poli Minimal yang Seharusnya Tersedia:** **{max_poli_simultan} Poli**
    * *Penjelasan:* Berdasarkan jadwal yang ada, pada jam-jam sibuk terdapat **{max_poli_simultan} dokter** yang tercatat praktek pada waktu yang sama secara bersamaan (beririsan). Faskes wajib menyediakan minimal {max_poli_simultan} unit ruang poli aktif.
    """)

    st.markdown("---")
    
    total_catatan = len(df_tampil)
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.metric(label="Total Sesi Terpilih", value=f"{total_catatan} Sesi")
    with col_c2:
        st.metric(label="Akumulasi Jam Praktek", value=f"{total_jam_filter:.1f} Jam")
    with col_c3:
        st.metric(label="Rata-rata Jam per Dokter", value=f"{(total_jam_filter / headcount_filter if headcount_filter > 0 else 0):.1f} Jam")

    # --- TABEL UTAMA ---
    df_tampil_clean = df_tampil[["Periode", "Hari", "Nama Dokter", "Faskes", "Jam Masuk", "Jam Pulang", "Total Jam Praktek", "Status Sesi"]].copy()
    df_tampil_clean.insert(0, "ID", df_tampil.index)

    st.markdown(f"### 📋 Rincian Jadwal ({len(df_tampil_clean)} Data Ditemukan)")
    st.dataframe(df_tampil_clean, use_container_width=True)
    
    st.markdown("### 📊 Grafik Akumulasi Jam Praktek per Dokter")
    if not df_tampil_clean.empty:
        df_grafik = df_tampil_clean.groupby("Nama Dokter")["Total Jam Praktek"].sum()
        st.bar_chart(df_grafik)
    else:
        st.info("Tidak ada data yang cocok dengan filter tersebut.")
    
    # --- FITUR DOWNLOAD LAPORAN EKSEKUTIF ---
    st.markdown("---")
    st.subheader("📥 Export Laporan Analisis Lengkap")

    ringkasan_laporan = f"""LAPORAN ANALISIS BEBAN KERJA, RASIO JKN & KEBUTUHAN POLI
==================================================
Filter Periode : {filter_periode}
Filter Faskes  : {filter_faskes}
Total Peserta JKN : {peserta_aktif:,} Jiwa

RINGKASAN RASIO & KAPASITAS:
- Rasio Headcount (Orang Fisik)   : {str_rasio_headcount}
- Rasio FTE (Jam Kerja Riil)      : {str_rasio_fte}
- Target Standar Rasio JKN        : 1 : {standar_rasio:,}
- Jumlah Orang (Headcount) Dokter : {headcount_filter} Orang
- Kekuatan Tenaga Riil (FTE)      : {fte_filter} FTE
- Kebutuhan Ideal JKN             : {dokter_ideal_jkn} FTE
- Status Evaluasi Keseluruhan     : {status_evaluasi_keseluruhan}
- Kekurangan (Defisit) FTE        : {gap_fte} FTE (Butuh tambahan ~{tambahan_dokter_bulat} dokter / {gap_jam_mingguan} jam/minggu)
- Kebutuhan Unit Poli Simultan    : Minimal {max_poli_simultan} Unit Poli Aktif

==================================================
RINCIAN JADWAL PRAKTEK:
"""
    csv_tabel = df_tampil_clean.to_csv(index=False)
    laporan_final = ringkasan_laporan + "\n" + csv_tabel

    st.download_button(
        label="📥 Download Laporan Ringkasan & Rincian (TXT/CSV)",
        data=laporan_final.encode('utf-8'),
        file_name=f'Laporan_Analisis_JKN_{filter_faskes.replace(" ", "_")}.txt',
        mime='text/plain',
    )
else:
    st.info("ℹ️ Belum ada data. Silakan upload file Excel atau gunakan form manual di sebelah kiri.")
