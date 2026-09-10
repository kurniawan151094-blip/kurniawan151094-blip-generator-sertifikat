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
    initial_sidebar_state="collapsed"
)

# Custom CSS Mobile-First
st.markdown("""
    <style>
        #MainMenu, footer, [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"] {
            display: none !important;
        }
        header { background: transparent !important; }
        .block-container { padding: 0.6rem 0.8rem 2rem 0.8rem !important; }
        
        /* Header Ramping */
        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.6rem;
            padding-bottom: 0.4rem;
            border-bottom: 1px solid #334155;
        }
        .app-title { font-size: 1.15rem !important; font-weight: 800; color: #38BDF8; margin: 0; }
        .app-badge { background-color: #0C4A6E; color: #38BDF8; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
        
        /* Tab Menu */
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            background-color: #1E293B;
            padding: 4px;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 6px 10px !important;
            font-size: 0.85rem !important;
            color: #94A3B8 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #E11D48 !important;
            color: white !important;
            border-radius: 6px;
        }

        /* Tombol Ekspor */
        .stButton>button {
            width: 100%;
            background-color: #E11D48;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 0.65rem 1rem;
            border: none;
            font-size: 0.95rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="app-header">
        <span class="app-title">⚡ CertifiKit Studio</span>
        <span class="app-badge">Touch Responsive</span>
    </div>
""", unsafe_allow_html=True)

# Inisialisasi Posisi di Session State
if "pos_x" not in st.session_state:
    st.session_state.pos_x = 50
if "pos_y" not in st.session_state:
    st.session_state.pos_y = 55
if "box_w" not in st.session_state:
    st.session_state.box_w = 75

# ==========================================================
# 2. MESIN FONT
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
    for f_name in font_files.get(font_choice, ["arial.ttf"]):
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
    font_size = min(max_allowed_font, int(max_h * 0.85))
    if font_size < 12:
        font_size = 12

    while font_size > 10:
        font = get_font(font_choice, font_size, custom_font_file)
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), nama, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        if text_w <= (max_w * 0.95) and text_h <= (max_h * 0.85):
            return font
        font_size -= 2

    return get_font(font_choice, font_size, custom_font_file)

# ==========================================================
# 3. UPLOAD FILE (RINGKAS)
# ==========================================================
col_u1, col_u2 = st.columns(2)
with col_u1:
    cert_file = st.file_uploader("1. Desain Sertifikat (JPG/PNG)", type=["png", "jpg", "jpeg"])
with col_u2:
    excel_file = st.file_uploader("2. File Excel (.xlsx)", type=["xlsx", "xls"])

# ==========================================================
# 4. WORKSPACE PREVIEW & KONTROL SENTUH
# ==========================================================
if cert_file is not None:
    original_img = Image.open(cert_file)
    orig_w, orig_h = original_img.size

    # Baca Excel
    names = []
    if excel_file is not None:
        try:
            df = pd.read_excel(excel_file)
            df.columns = [str(c).strip() for c in df.columns]
            col_target = next((c for c in df.columns if c.lower() in ['nama', 'name', 'peserta', 'nama lengkap']), df.columns[0])
            names = [str(n).strip() for n in df[col_target].dropna().tolist() if str(n).strip() != "" and str(n).lower() != "nan"]
        except Exception:
            pass

    sample_name = names[0] if names else "Nama Peserta Sertifikat"

    # Di laptop tampil 2 kolom, di HP bertumpuk rapi
    col_preview, col_controls = st.columns([1.2, 1], gap="medium")

    # --- TAB KONTROL SENTUH DI HP/LAPTOP ---
    with col_controls:
        tab_pos, tab_style, tab_process = st.tabs(["🎮 Atur Posisi", "🎨 Font & Warna", "🚀 Ekspor"])

        with tab_pos:
            st.caption("Sentuh tombol panah untuk menggeser posisi teks langsung:")
            
            # Tombol Preset Cepat
            st.write("**Posisi Cepat:**")
            p_c1, p_c2, p_c3 = st.columns(3)
            if p_c1.button("⬆️ Atas"):
                st.session_state.pos_x = 50
                st.session_state.pos_y = 38
                st.rerun()
            if p_c2.button("⏺️ Tengah"):
                st.session_state.pos_x = 50
                st.session_state.pos_y = 52
                st.rerun()
            if p_c3.button("⬇️ Bawah"):
                st.session_state.pos_x = 50
                st.session_state.pos_y = 65
                st.rerun()

            # D-Pad Tombol Panah Geser
            st.write("**Geser Halus:**")
            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
            if d_col1.button("⬅️ Kiri"):
                st.session_state.pos_x = max(5, st.session_state.pos_x - 3)
                st.rerun()
            if d_col2.button("➡️ Kanan"):
                st.session_state.pos_x = min(95, st.session_state.pos_x + 3)
                st.rerun()
            if d_col3.button("⬆️ Naik"):
                st.session_state.pos_y = max(5, st.session_state.pos_y - 3)
                st.rerun()
            if d_col4.button("⬇️ Turun"):
                st.session_state.pos_y = min(95, st.session_state.pos_y + 3)
                st.rerun()

            # Slider Halus
            st.markdown("---")
            st.session_state.pos_x = st.slider("Posisi X (Kiri-Kanan %):", 0, 100, st.session_state.pos_x)
            st.session_state.pos_y = st.slider("Posisi Y (Atas-Bawah %):", 0, 100, st.session_state.pos_y)
            st.session_state.box_w = st.slider("Lebar Area Teks (%):", 20, 95, st.session_state.box_w)

        with tab_style:
            font_options = [
                "Times New Roman (Formal)",
                "Georgia (Elegan)",
                "Arial (Modern/Clean)",
                "Edwardian Script (Latin Mewah)",
                "Vivaldi (Latin Artistik)",
                "Monotype Corsiva (Latin Miring)"
            ]
            selected_font = st.selectbox("Pilih Font:", font_options)
            custom_ttf = st.file_uploader("Upload Font Sendiri (.ttf)", type=["ttf", "otf"])

            s_col1, s_col2 = st.columns(2)
            with s_col1:
                text_color = st.color_picker("Warna Teks:", "#1E293B")
            with s_col2:
                max_font_size = st.number_input("Max Font (px):", min_value=20, max_value=250, value=100, step=5)

        with tab_process:
            if not names:
                st.warning("⚠️ Upload file Excel di atas untuk mulai membuat sertifikat massal.")
            else:
                st.success(f"✓ Siap memproses **{len(names)} sertifikat HD**.")
                btn_start = st.button(f"⚡ GENERATE {len(names)} SERTIFIKAT")

    # --- GAMBAR PREVIEW LANGSUNG (100% PAS DI HP) ---
    with col_preview:
        target_center_x = int(orig_w * (st.session_state.pos_x / 100))
        target_center_y = int(orig_h * (st.session_state.pos_y / 100))
        allowed_max_w = int(orig_w * (st.session_state.box_w / 100))
        allowed_max_h = int(orig_h * 0.25)

        preview_img = original_img.copy()
        draw_preview = ImageDraw.Draw(preview_img)

        # Gambar garis kotak bantu penanda posisi
        box_left = target_center_x - (allowed_max_w / 2)
        box_right = target_center_x + (allowed_max_w / 2)
        box_top = target_center_y - (allowed_max_h / 2)
        box_bottom = target_center_y + (allowed_max_h / 2)
        draw_preview.rectangle([box_left, box_top, box_right, box_bottom], outline="#38BDF8", width=3)

        # Gambar teks
        font_preview = get_auto_fit_font(sample_name, allowed_max_w, allowed_max_h, max_font_size, selected_font, custom_ttf)
        bbox = draw_preview.textbbox((0, 0), sample_name, font=font_preview)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        draw_preview.text(
            (target_center_x - (tw / 2), target_center_y - (th / 2)),
            sample_name,
            fill=text_color,
            font=font_preview
        )

        st.image(preview_img, caption="Pratinjau Hasil Desain (Kotak biru adalah batas teks)", use_container_width=True)

    # --- EKSEKUSI PROSES DATA ---
    with col_controls:
        with tab_process:
            if names and 'btn_start' in locals() and btn_start:
                progress_bar = st.progress(0)
                status_text = st.empty()

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, nama in enumerate(names, 1):
                        status_text.text(f"Memproses ({idx}/{len(names)}): {nama}")
                        progress_bar.progress(idx / len(names))

                        cert_hd = original_img.copy()
                        draw_hd = ImageDraw.Draw(cert_hd)

                        font_hd = get_auto_fit_font(nama, allowed_max_w, allowed_max_h, max_font_size, selected_font, custom_ttf)
                        bbox_hd = draw_hd.textbbox((0, 0), nama, font=font_hd)
                        t_w = bbox_hd[2] - bbox_hd[0]
                        t_h = bbox_hd[3] - bbox_hd[1]

                        draw_hd.text(
                            (target_center_x - (t_w / 2), target_center_y - (t_h / 2)),
                            nama,
                            fill=text_color,
                            font=font_hd
                        )

                        img_buffer = io.BytesIO()
                        cert_hd.save(img_buffer, format="PNG", quality=100)
                        safe_name = "".join(x for x in nama if x.isalnum() or x in " _-")
                        zip_file.writestr(f"Sertifikat_{safe_name}.png", img_buffer.getvalue())

                status_text.success("🎉 Semua sertifikat HD selesai dibuat!")
                progress_bar.empty()

                st.download_button(
                    label="📥 DOWNLOAD FILE ZIP",
                    data=zip_buffer.getvalue(),
                    file_name="Hasil_Sertifikat_HD.zip",
                    mime="application/zip"
                )

else:
    st.info("👆 Upload file desain sertifikat Anda di kotak atas untuk mulai.")
