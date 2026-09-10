import io
import os
import zipfile
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# ==========================================
# KONFIGURASI HALAMAN (RESPONSIF MOBILE & PC)
# ==========================================
st.set_page_config(
    page_title="CertifiKit Web — Certificate Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan Dark Modern ala SaaS
st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .stButton>button {
            width: 100%;
            background-color: #E11D48;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 0.6rem 1rem;
            border: none;
        }
        .stButton>button:hover {
            background-color: #BE123C;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ CertifiKit Web Studio")
st.caption("Generator Sertifikat HD Otomatis — Bisa Diakses dari Laptop & HP Android")

# ==========================================
# MESIN PENCARI FONT (MENDUKUNG WINDOWS, LINUX & CLOUD)
# ==========================================
def get_font(font_choice, font_size, custom_font_file=None):
    # Jika user upload font custom (.ttf)
    if custom_font_file is not None:
        try:
            return ImageFont.truetype(custom_font_file, font_size)
        except Exception:
            pass

    # Direktori font standar
    font_dirs = [
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
        "/usr/share/fonts",
        "/usr/share/fonts/truetype",
        "."
    ]
    
    font_files = {
        "Times New Roman (Formal)": ["times.ttf", "Times.ttf", "LiberationSerif-Regular.ttf"],
        "Georgia (Elegan)": ["georgia.ttf", "Georgia.ttf"],
        "Arial (Modern/Clean)": ["arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"],
        "Edwardian Script (Latin Mewah)": ["edward.ttf", "EdwardianScriptITC.ttf"],
        "Vivaldi (Latin Artistik)": ["vivaldii.ttf", "Vivaldi.ttf"],
        "Monotype Corsiva (Latin Miring)": ["corsiva.ttf", "MTCORSVA.TTF"]
    }

    selected_files = font_files.get(font_choice, ["arial.ttf"])
    
    for f_name in selected_files:
        for d in font_dirs:
            p = os.path.join(d, f_name)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, font_size)
                except Exception:
                    pass
        try:
            return ImageFont.truetype(f_name, font_size)
        except Exception:
            pass

    return ImageFont.load_default()

def get_auto_fit_font(nama, max_w, max_h, max_allowed_font, font_choice, custom_font_file=None):
    font_size = min(max_allowed_font, int(max_h * 0.8))
    if font_size < 12:
        font_size = 12

    while font_size > 10:
        font = get_font(font_choice, font_size, custom_font_file)
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), nama, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        if text_w <= max_w and text_h <= max_h:
            return font
        font_size -= 2

    return get_font(font_choice, font_size, custom_font_file)

# ==========================================
# SIDEBAR: PENGATURAN & INPUT FILE
# ==========================================
with st.sidebar:
    st.header("📁 1. Upload File")
    cert_file = st.file_uploader("Upload Desain Sertifikat (JPG/PNG)", type=["png", "jpg", "jpeg"])
    excel_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx", "xls"])
    
    st.markdown("---")
    st.header("🎨 2. Kustomisasi Teks")
    font_options = [
        "Times New Roman (Formal)",
        "Georgia (Elegan)",
        "Arial (Modern/Clean)",
        "Edwardian Script (Latin Mewah)",
        "Vivaldi (Latin Artistik)",
        "Monotype Corsiva (Latin Miring)"
    ]
    selected_font = st.selectbox("Pilih Jenis Font:", font_options)
    custom_ttf = st.file_uploader("Atau Pasang Font Sendiri (.ttf)", type=["ttf", "otf"])

    text_color = st.color_picker("Warna Teks Nama:", "#1E293B")
    max_font_size = st.slider("Batas Maksimal Ukuran Font:", 30, 200, 100)

    st.markdown("---")
    st.header("📐 3. Posisi Nama (Sentuh / Geser)")
    pos_x_pct = st.slider("Posisi Horizontal (Kiri ➔ Kanan %):", 0, 100, 50, help="50% adalah tepat di tengah")
    pos_y_pct = st.slider("Posisi Vertikal (Atas ➔ Bawah %):", 0, 100, 55)
    max_w_pct = st.slider("Batas Lebar Area Teks (%):", 20, 95, 75, help="Mencegah nama panjang keluar dari sertifikat")

# ==========================================
# WORKSPACE UTAMA (PREVIEW & PROSES)
# ==========================================
if cert_file is not None:
    original_img = Image.open(cert_file)
    orig_w, orig_h = original_img.size

    # Baca data Excel jika tersedia
    names = []
    if excel_file is not None:
        try:
            df = pd.read_excel(excel_file)
            df.columns = [str(c).strip() for c in df.columns]
            col_target = next((c for c in df.columns if c.lower() in ['nama', 'name', 'peserta']), df.columns[0])
            names = [str(n).strip() for n in df[col_target].dropna().tolist() if str(n).strip() != ""]
            st.sidebar.success(f"✓ Terbaca {len(names)} nama dari kolom '{col_target}'")
        except Exception as e:
            st.sidebar.error(f"Gagal membaca Excel: {e}")

    sample_name = names[0] if names else "Nama Lengkap Peserta (Contoh)"

    # Hitung koordinat piksel berdasarkan persentase slider
    target_center_x = int(orig_w * (pos_x_pct / 100))
    target_center_y = int(orig_h * (pos_y_pct / 100))
    allowed_max_w = int(orig_w * (max_w_pct / 100))
    allowed_max_h = int(orig_h * 0.25)

    # 🌟 RENDER LIVE PREVIEW
    st.subheader("👁️ Live Preview Sertifikat")
    st.caption("Ubah slider posisi atau warna di sidebar, preview di bawah akan langsung ter-update.")

    preview_img = original_img.copy()
    draw_preview = ImageDraw.Draw(preview_img)

    font_preview = get_auto_fit_font(sample_name, allowed_max_w, allowed_max_h, max_font_size, selected_font, custom_ttf)
    bbox = draw_preview.textbbox((0, 0), sample_name, font=font_preview)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    draw_preview.text(
        (target_center_x - (text_w / 2), target_center_y - (text_h / 2)),
        sample_name,
        fill=text_color,
        font=font_preview
    )

    st.image(preview_img, caption="Pratinjau Hasil Desain", use_container_width=True)

    # ==========================================
    # PROSES SEMUA DATA & DOWNLOAD ZIP
    # ==========================================
    st.markdown("---")
    st.subheader("🚀 Ekspor Hasil")

    if not names:
        st.info("💡 Upload file Excel di sidebar kiri untuk memproses semua sertifikat secara massal.")
    else:
        if st.button(f"⚡ PROSES {len(names)} SERTIFIKAT (HD)"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Buat file ZIP di dalam memori RAM
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, nama in enumerate(names, 1):
                    status_text.text(f"Memproses ({idx}/{len(names)}): {nama}")
                    progress_bar.progress(idx / len(names))

                    # Render Gambar HD Asli
                    cert_hd = original_img.copy()
                    draw_hd = ImageDraw.Draw(cert_hd)

                    font_hd = get_auto_fit_font(nama, allowed_max_w, allowed_max_h, max_font_size, selected_font, custom_ttf)
                    bbox_hd = draw_hd.textbbox((0, 0), nama, font=font_hd)
                    tw = bbox_hd[2] - bbox_hd[0]
                    th = bbox_hd[3] - bbox_hd[1]

                    draw_hd.text(
                        (target_center_x - (tw / 2), target_center_y - (th / 2)),
                        nama,
                        fill=text_color,
                        font=font_hd
                    )

                    # Simpan ke ZIP
                    img_buffer = io.BytesIO()
                    cert_hd.save(img_buffer, format="PNG", quality=100)
                    safe_name = "".join(x for x in nama if x.isalnum() or x in " _-")
                    zip_file.writestr(f"Sertifikat_{safe_name}.png", img_buffer.getvalue())

            status_text.success("🎉 Semua sertifikat berhasil dibuat dalam kualitas HD!")
            progress_bar.empty()

            # Tombol Download ZIP
            st.download_button(
                label="📥 DOWNLOAD SEMUA SERTIFIKAT (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name="Hasil_Sertifikat_HD.zip",
                mime="application/zip"
            )

else:
    st.info("👈 Silakan upload file desain sertifikat terlebih dahulu melalui panel di sebelah kiri.")