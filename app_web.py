import io
import os
import zipfile
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# ==========================================================
# 1. KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(
    page_title="CertifiKit Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar otomatis disembunyikan
)

# ==========================================================
# 2. CUSTOM CSS KHUSUS TAMPILAN HP (MOBILE-FIRST)
# ==========================================================
st.markdown("""
    <style>
        /* Sembunyikan menu bawaan Streamlit & footer */
        #MainMenu, footer, [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"] {
            display: none !important;
        }
        header {
            background: transparent !important;
        }

        /* Padding halaman dibuat sangat compact di HP */
        .block-container {
            padding: 0.8rem 1rem 2rem 1rem !important;
            max-width: 100% !important;
        }

        /* Header / Judul Kecil & Rapi */
        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.8rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #334155;
        }
        .app-title {
            font-size: 1.25rem !important;
            font-weight: 800;
            color: #38BDF8;
            margin: 0;
        }
        .app-badge {
            background-color: #0C4A6E;
            color: #38BDF8;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 6px;
            font-weight: 600;
        }

        /* Styling Tab Menu agar mudah disentuh jempol */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background-color: #1E293B;
            padding: 4px;
            border-radius: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 12px !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            color: #94A3B8 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #E11D48 !important;
            color: white !important;
        }

        /* Tombol Ekspor Utama */
        .stButton>button {
            width: 100%;
            background-color: #E11D48;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 0.7rem 1rem;
            border: none;
            font-size: 0.95rem;
        }
    </style>
""", unsafe_allow_html=True)

# Header Kompak
st.markdown("""
    <div class="app-header">
        <span class="app-title">⚡ CertifiKit Studio</span>
        <span class="app-badge">HD Generator</span>
    </div>
""", unsafe_allow_html=True)

# ==========================================================
# 3. ENGINE FONT
# ==========================================================
def get_font(font_choice, font_size, custom_font_file=None):
    if custom_font_file is not None:
        try:
            return ImageFont.truetype(custom_font_file, font_size)
        except Exception:
            pass

    font_dirs = [
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
        "/usr/share/fonts",
        "/usr/share/fonts/truetype",
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/liberation",
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

# ==========================================================
# 4. AREA UPLOAD CEPAT (JIKA BELUM ADA FILE)
# ==========================================================
# Jika sertifikat belum di-upload, tampilkan kotak upload yang jelas
if "cert_image" not in st.session_state:
    st.session_state.cert_image = None

# Gunakan container responsif
col_up1, col_up2 = st.columns(2)
with col_up1:
    cert_file = st.file_uploader("1. Upload Desain Sertifikat (JPG/PNG)", type=["png", "jpg", "jpeg"])
with col_up2:
    excel_file = st.file_uploader("2. Upload File Excel (.xlsx)", type=["xlsx", "xls"])

# ==========================================================
# 5. TAMPILAN KERJA (PREVIEW DI ATAS / SEJAJAR KONTROL)
# ==========================================================
if cert_file is not None:
    original_img = Image.open(cert_file)
    orig_w, orig_h = original_img.size

    # Baca nama dari Excel
    names = []
    if excel_file is not None:
        try:
            df = pd.read_excel(excel_file)
            df.columns = [str(c).strip() for c in df.columns]
            col_target = next((c for c in df.columns if c.lower() in ['nama', 'name', 'peserta', 'nama lengkap']), df.columns[0])
            names = [str(n).strip() for n in df[col_target].dropna().tolist() if str(n).strip() != "" and str(n).lower() != "nan"]
        except Exception:
            pass

    sample_name = names[0] if names else "Nama Lengkap Peserta (Contoh)"

    # Di PC tampil 2 kolom sejajar, di HP otomatis bertumpuk (Preview di atas, kontrol di bawah)
    col_preview, col_controls = st.columns([1.2, 1], gap="medium")

    # --- PANEL KONTROL DENGAN SISTEM TAB (MUDAH DI HP) ---
    with col_controls:
        tab_pos, tab_font, tab_export = st.tabs(["📐 Posisi", "🎨 Font & Warna", "🚀 Ekspor"])

        with tab_pos:
            st.caption("Geser slider untuk atur posisi teks secara presisi:")
            pos_x_pct = st.slider("Posisi Horizontal (Kiri ➔ Kanan %):", 0, 100, 50)
            pos_y_pct = st.slider("Posisi Vertikal (Atas ➔ Bawah %):", 0, 100, 55)
            max_w_pct = st.slider("Batas Lebar Area Teks (%):", 20, 95, 75)

        with tab_font:
            font_options = [
                "Times New Roman (Formal)",
                "Georgia (Elegan)",
                "Arial (Modern/Clean)",
                "Edwardian Script (Latin Mewah)",
                "Vivaldi (Latin Artistik)",
                "Monotype Corsiva (Latin Miring)"
            ]
            selected_font = st.selectbox("Pilihan Font:", font_options)
            custom_ttf = st.file_uploader("Upload Font Sendiri (.ttf)", type=["ttf", "otf"])

            c_col1, c_col2 = st.columns(2)
            with c_col1:
                text_color = st.color_picker("Warna Teks:", "#1E293B")
            with c_col2:
                max_font_size = st.number_input("Max Font (px):", min_value=20, max_value=250, value=95, step=5)

        with tab_export:
            if not names:
                st.warning("⚠️ Upload file Excel di atas untuk mulai membuat sertifikat massal.")
            else:
                st.success(f"✓ Siap memproses **{len(names)} sertifikat**")
                btn_process = st.button(f"⚡ PROSES SEMUA SERTIFIKAT ({len(names)} FILE)")

    # --- AREA PREVIEW GAMBAR ---
    with col_preview:
        target_center_x = int(orig_w * (pos_x_pct / 100))
        target_center_y = int(orig_h * (pos_y_pct / 100))
        allowed_max_w = int(orig_w * (max_w_pct / 100))
        allowed_max_h = int(orig_h * 0.25)

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

        st.image(preview_img, caption="Pratinjau Hasil Desain (Live Preview)", use_container_width=True)

    # --- PROSES GENERATE JIKA TOMBOL DIKLIK ---
    with col_controls:
        with tab_export:
            if names and 'btn_process' in locals() and btn_process:
                progress_bar = st.progress(0)
                status_text = st.empty()

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, nama in enumerate(names, 1):
                        status_text.text(f"Membuat ({idx}/{len(names)}): {nama}")
                        progress_bar.progress(idx / len(names))

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

                        img_buffer = io.BytesIO()
                        cert_hd.save(img_buffer, format="PNG", quality=100)
                        safe_name = "".join(x for x in nama if x.isalnum() or x in " _-")
                        zip_file.writestr(f"Sertifikat_{safe_name}.png", img_buffer.getvalue())

                status_text.success("🎉 Berhasil selesai dibuat!")
                progress_bar.empty()

                st.download_button(
                    label="📥 DOWNLOAD FILE ZIP",
                    data=zip_buffer.getvalue(),
                    file_name="Sertifikat_HD.zip",
                    mime="application/zip"
                )

else:
    st.info("👆 Mulai dengan mengupload desain sertifikat Anda di kotak atas.")
