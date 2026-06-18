import streamlit as st
from transformers import pipeline
import feedparser
import urllib.parse
from fpdf import FPDF
from datetime import datetime
import google.generativeai as genai

# ==========================================
# 1. KONFIGURASI & MEMORI STATE
# ==========================================
st.set_page_config(page_title="Radar Kejaksaan", layout="wide")

if 'data_berita' not in st.session_state:
    st.session_state.data_berita = [] 
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# ==========================================
# 2. INISIALISASI MESIN AI LOKAL (SENTIMEN)
# ==========================================
@st.cache_resource
def panggil_otak_sentimen():
    return pipeline("sentiment-analysis", model="w11wo/indonesian-roberta-base-sentiment-classifier")

mesin_sentimen = panggil_otak_sentimen()

# ==========================================
# 3. FUNGSI PEMBUAT PDF (FORMAT L.IN.2)
# ==========================================
def buat_pdf_laporan(kata_kunci, berita_terpilih, teks_ringkasan, teks_trend, teks_saran):
    pdf = FPDF(format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    def bersihkan_teks(teks):
        return str(teks).encode('latin-1', 'replace').decode('latin-1')

    tanggal_hari_ini = datetime.now().strftime("%d %B %Y")

    # Header RAHASIA
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 5, txt="RAHASIA", ln=True, align='R')
    pdf.cell(0, 5, txt="L.IN.2", ln=True, align='R')
    
    # Kop Institusi
    pdf.set_font("Arial", 'BU', 11)
    pdf.cell(0, 5, txt="KEJAKSAAN NEGERI HALMAHERA TIMUR", ln=True, align='L')
    pdf.ln(5)
    
    # Identitas Laporan
    pdf.set_font("Arial", '', 11)
    pdf.cell(25, 5, txt="DARI", border=0); pdf.cell(5, 5, txt=":", border=0)
    pdf.cell(0, 5, txt="Kasi Intelijen Kejaksaan Negeri Halmahera Timur", ln=True)
    pdf.cell(25, 5, txt="KEPADA", border=0); pdf.cell(5, 5, txt=":", border=0)
    pdf.cell(0, 5, txt="Kepala Kejaksaan Negeri Halmahera Timur", ln=True)
    pdf.cell(25, 5, txt="TANGGAL", border=0); pdf.cell(5, 5, txt=":", border=0)
    pdf.cell(0, 5, txt=tanggal_hari_ini, ln=True)
    pdf.ln(5)
    
    # Judul
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 6, txt="LAPORAN INFORMASI HARIAN", ln=True, align='C')
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, txt=f"Perihal: Analisis Intelijen OSINT Terkait '{kata_kunci}'", ln=True, align='C')
    pdf.ln(8)
    
    # I. INFORMASI YANG DIPEROLEH
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, txt="I. INFORMASI YANG DIPEROLEH:", ln=True)
    pdf.set_font("Arial", '', 11)
    pengantar = f"Bahwa pada tanggal {tanggal_hari_ini}, tim Intelijen telah melakukan pemantauan media digital dan memperoleh informasi sebagai berikut:"
    pdf.multi_cell(0, 5, txt=bersihkan_teks(pengantar))
    pdf.ln(2)
    
    # Memasukkan ringkasan naratif karangan AI (Paragraf Murni)
    pdf.multi_cell(0, 5, txt=bersihkan_teks(teks_ringkasan))
    pdf.ln(3)
    
    # Memasukkan daftar tautan referensi tanpa penomoran angka
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, txt="Sumber tautan berita:", ln=True)
    pdf.set_font("Arial", '', 10)
    for b in berita_terpilih:
        pdf.multi_cell(0, 5, txt=bersihkan_teks(f"- {b['judul']} ({b['link']})"))
    pdf.ln(4)
    
    # II. SUMBER INFORMASI
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, txt="II. SUMBER INFORMASI:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 5, txt="Pemantauan Media Terbuka (Open Source Intelligence / OSINT).")
    pdf.ln(3)
    
    # III. TREND PERKEMBANGAN (Paragraf Murni)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, txt="III. TREND PERKEMBANGAN / PERKIRAAN:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 5, txt=bersihkan_teks(teks_trend))
    pdf.ln(3)
    
    # IV. SARAN TINDAK (Paragraf Murni)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, txt="IV. SARAN / TINDAK:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 5, txt=bersihkan_teks(teks_saran))
    pdf.ln(10)
    
    # Otentikasi Tanda Tangan (NAMA DIHAPUS, HANYA JABATAN)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, txt=f"Maba, {tanggal_hari_ini}", ln=True, align='R')
    pdf.cell(0, 6, txt="KEPALA SEKSI INTELIJEN", ln=True, align='R')
    pdf.ln(25) # Ruang kosong ekstra untuk tanda tangan basah
    
    nama_file = "Lapinhar_Temp.pdf"
    pdf.output(nama_file)
    with open(nama_file, "rb") as f:
        return f.read()

# ==========================================
# 4. TAMPILAN DASHBOARD (UI)
# ==========================================
with st.sidebar:
    st.header("⚙️ Pengaturan Sistem")
    api_key_input = st.text_input("Masukkan Kunci API Gemini:", type="password", help="Dapatkan di aistudio.google.com")
    st.info("Kunci API diperlukan untuk menyusun paragraf analitis pada laporan.")

st.title("📡 Command Center OSINT")
st.subheader("Kurasi Berita & Analisis Intelijen Otomatis")
st.write("---")

col_search, col_btn = st.columns([3, 1])
with col_search:
    kata_kunci = st.text_input("🔍 Masukkan Kata Kunci Sasaran:", value="Kejaksaan Agung")
with col_btn:
    st.write("") 
    st.write("") 
    tombol_cari = st.button("Mulai Pemindaian 🚀", use_container_width=True)

if tombol_cari:
    st.session_state.data_berita = [] 
    st.session_state.pdf_data = None
    
    with st.spinner("Memindai jaringan internet..."):
        url_berita = f"https://news.google.com/rss/search?q={urllib.parse.quote(kata_kunci)}+when:1d&hl=id&gl=ID&ceid=ID:id"
        sumber = feedparser.parse(url_berita)
        
        for i, berita in enumerate(sumber.entries):
            judul = berita.title
            label = mesin_sentimen(judul)[0]['label'].lower()
            st.session_state.data_berita.append({
                "id": i,
                "judul": judul,
                "link": berita.link,
                "waktu": berita.published,
                "label": label,
                "dipilih": False 
            })

# ==========================================
# 5. AREA KURASI (PEMILIHAN BERITA)
# ==========================================
if st.session_state.data_berita:
    st.write("### 📌 Kurasi Temuan Informasi")
    st.caption("Centang berita yang menurut Anda krusial untuk Lapinhar.")
    
    col_pos, col_net, col_neg = st.columns(3)
    berita_terpilih = []
    
    with col_pos:
        st.success("🟢 POSITIF")
        for b in [x for x in st.session_state.data_berita if x['label'] == 'positive']:
            if st.checkbox(b['judul'], key=f"chk_{b['id']}"): berita_terpilih.append(b)
                
    with col_net:
        st.warning("🟡 NETRAL")
        for b in [x for x in st.session_state.data_berita if x['label'] == 'neutral']:
            if st.checkbox(b['judul'], key=f"chk_{b['id']}"): berita_terpilih.append(b)
                
    with col_neg:
        st.error("🔴 NEGATIF")
        for b in [x for x in st.session_state.data_berita if x['label'] == 'negative']:
            if st.checkbox(b['judul'], key=f"chk_{b['id']}"): berita_terpilih.append(b)

    st.write("---")

    # ==========================================
    # 6. AREA PEMBUATAN LAPORAN (OTAK AI INTELIJEN)
    # ==========================================
    st.write("### 🤖 Analisis & Ekspor Laporan")
    
    if st.button("Susun Laporan dengan AI dari Berita Terpilih", type="primary"):
        if not api_key_input:
            st.error("❌ Masukkan Kunci API Gemini di menu sebelah kiri terlebih dahulu!")
        elif len(berita_terpilih) == 0:
            st.warning("⚠️ Anda belum mencentang satu pun berita!")
        else:
            with st.spinner("AI Generatif merumuskan Ringkasan, Trend, dan Saran Tindak..."):
                try:
                    genai.configure(api_key=api_key_input)
                    model_tersedia = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    nama_model_aktif = model_tersedia[0]
                    model_gemini = genai.GenerativeModel(nama_model_aktif)
                    
                    kumpulan_judul = "\n".join([f"- {b['judul']}" for b in berita_terpilih])
                    
                    # PROMPT BARU: Instruksi Super Ketat Tanpa Angka/Penomoran
                    perintah_ai = f"""
                    Bertindaklah sebagai Perwira Intelijen Kejaksaan Negeri. Berdasarkan isu berita berikut:
                    {kumpulan_judul}
                    
                    Tugas Anda merumuskan 3 bagian teks.
                    ATURAN SANGAT KETAT: 
                    - JANGAN menggunakan penomoran (1, 2, 3), bullet point, atau format list sama sekali.
                    - JANGAN menuliskan judul atau label seperti "Bagian 1", "Trend:", atau "Saran:".
                    - Langsung tulis kalimat paragrafnya saja secara utuh dan mengalir.
                    - Pisahkan ketiga paragraf tersebut HANYA dengan kata "BATAS_PEMISAH".
                    
                    Paragraf Pertama: Rangkum kejadian dari berita tersebut secara naratif (maks 3 kalimat).
                    BATAS_PEMISAH
                    Paragraf Kedua: Analisis naratif mengenai perkiraan dampak kedepan dari isu ini terhadap citra, keamanan, atau penegakan hukum Kejaksaan.
                    BATAS_PEMISAH
                    Paragraf Ketiga: Berikan saran taktis untuk pimpinan (Kajari) dalam bentuk SATU paragraf naratif utuh. Jika positif/netral: pertahankan kinerja. Jika negatif: saran klarifikasi/koordinasi.
                    """
                    
                    respon_ai = model_gemini.generate_content(perintah_ai)
                    hasil_teks = [x.strip() for x in respon_ai.text.split("BATAS_PEMISAH")]
                    
                    # Mengekstrak 3 bagian dengan aman dan memastikan tidak ada sisa label yang menempel
                    teks_ringkasan = hasil_teks[0].replace("Bagian 1", "").replace(":", "").strip() if len(hasil_teks) > 0 else "Ringkasan isu."
                    teks_trend = hasil_teks[1].replace("Bagian 2", "").replace(":", "").strip() if len(hasil_teks) > 1 else "Masih dalam pemantauan intelijen."
                    teks_saran = hasil_teks[2].replace("Bagian 3", "").replace(":", "").strip() if len(hasil_teks) > 2 else "Lanjutkan pemantauan media."
                    
                    st.session_state.pdf_data = buat_pdf_laporan(kata_kunci, berita_terpilih, teks_ringkasan, teks_trend, teks_saran)
                    st.success("✅ Laporan Intelijen berhasil disusun sempurna tanpa format angka!")
                    
                except Exception as e:
                    st.error(f"Gagal memanggil AI: {e}")

    if st.session_state.pdf_data is not None:
        nama_file = f"L.IN.2_{kata_kunci.replace(' ', '_')}.pdf"
        st.download_button(
            label=f"📥 Download Lapinhar ({nama_file})",
            data=st.session_state.pdf_data,
            file_name=nama_file,
            mime="application/pdf"
        )

# ==========================================
# 7. FOOTER IDENTITAS PENGEMBANG
# ==========================================
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>🛡️ Sistem OSINT Intelijen | Dikembangkan oleh <b>Muhammad Fariz Rahman</b></p>", unsafe_allow_html=True)