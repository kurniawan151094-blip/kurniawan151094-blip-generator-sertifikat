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

# Custom CSS Ringkas & Mobile-Friendly
st.markdown("""
    <style>
        #MainMenu, footer, [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"] {
            display: none !important;
        }
        header { background: transparent !important; }
        .block-container { padding: 0.5rem 0.7rem 1.5rem 0.7rem !important; }
        
        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid #334155;
        }
        .app-title { font-size: 1.1rem !important; font-weight: 800; color: #38BDF8; margin: 0; }
        .app-badge { background-color: #0C4A6E; color: #38BDF8; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: 600; }

        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background-color: #1E293B;
            padding: 3px;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 6px 12px !important;
            font-size: 0.85rem !important;
            color: #94A3B8 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #E11D48 !important;
            color: white !important;
            border-radius: 6px;
        }

        div[data-testid="column"] button {
            padding: 0.35rem 0.2rem !important;
            font-size: 0.85rem !important;
            border-radius: 6px !important;
        }

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
        <span class="app-badge">Compact Mobile</span>
    </div>
""", unsafe_allow_html=True)

# ==========================================================
# INISIALISASI SESSION STATE (AGAR SETELAN TERKUNCI & TIDAK RESET)
# ==========================================================
if "pos_x" not in st.session_state:
    st.session_state.pos_x = 50
if "pos_y" not in st.session_state:
    st.session_state.pos_y = 52
if "font_size" not in st.session_state:
    st.session_state.font_size = 90
if "selected_font" not in st.session_state:
    st.session_state.selected_font = "Times New Roman (Formal)"
if "text_color" not in st.session_state:
    st.session_state.text_color = "#1E293B"

# ==========================================================
# 2. MESIN FONT RESPONSIF
# ==========================================================
def get_font(font_choice, font_size, custom_font_file=None):
    font_size = int(font_size)

    # Reset pointer custom font jika ada
    if custom_font_file is not None:
        try:
            custom_font_file.seek(0)
            return ImageFont.truetype(io.BytesIO(custom_font_file.getvalue()), font_size)
        except Exception:
            pass

    font_dirs = [
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
        "/usr/share/fonts",
        "/usr/share/fonts/truetype",
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/liberation",
        "/usr/share/fonts/truetype/freefont",
        "/Library/Fonts",
        "/System/Library/Fonts",
        "."
    ]
    font_files = {
        "Times New Roman (Formal)": ["times.ttf", "Times.ttf", "LiberationSerif-Regular.ttf", "DejaVuSerif.ttf"],
        "Georgia (Elegan)": ["georgia.ttf", "Georgia.ttf", "LiberationSerif-Regular.ttf"],
        "Arial (Modern/Clean)": ["arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"],
        "Edwardian Script (Latin Mewah)": ["edward.ttf", "EdwardianScriptITC.ttf", "times.ttf"],
        "Vivaldi (Latin Artistik)": ["vivaldii.ttf", "Vivaldi.ttf", "times.ttf"],
        "Monotype Corsiva (Latin Miring)": ["corsiva.ttf", "MTCORSVA.TTF", "times.ttf"]
    }

    for f_name in font_files.get(font_choice, ["arial.ttf", "DejaVuSans.ttf"]):
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

    try:
        return ImageFont.load_default(size=font_size)
    except TypeError:
        return ImageFont.load_default()

# ==========================================================
# 3. AREA UPLOAD FILE
# ==========================================================
col_u1, col_u2 = st.columns(2)
with col_u1:
    cert_file = st.file_uploader("1. Desain Sertifikat (JPG/PNG)", type=["png", "jpg", "jpeg"])
with col_u2:
    excel_file = st.file_uploader("2. File Excel (.xlsx)", type=["xlsx", "xls"])

# ==========================================================
# 4. WORKSPACE UTAMA
# ==========================================================
if cert_file is not None:
    original_img = Image.open(cert_file).convert("RGB")
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

    col_preview, col_controls = st.columns([1.2, 1], gap="medium")

    # --- TAB KONTROL ---
    with col_controls:
        tab_pos, tab_style, tab_process = st.tabs(["📐 Posisi", "🎨 Font & Gaya", "🚀 Ekspor"])

        # TAB 1: POSISI (st.rerun() DIHAPUS AGAR STATE TIDAK TERPUTUS)
        with tab_pos:
            st.caption("📍 **Posisi Cepat (1 Baris):**")
            p1, p2, p3 = st.columns(3)
            if p1.button("⬆️ Atas"):
                st.session_state.pos_x = 50
                st.session_state.pos_y = 38
            if p2.button("⏺️ Tengah"):
                st.session_state.pos_x = 50
                st.session_state.pos_y = 52
            if p3.button("⬇️ Bawah"):
                st.session_state.pos_x = 50
                st.session_state.pos_y = 66

            st.caption("🎮 **Geser Halus (1 Baris):**")
            d1, d2, d3, d4 = st.columns(4)
            if d1.button("⬅️ Kiri"):
                st.session_state.pos_x = max(5, st.session_state.pos_x - 3)
            if d2.button("⬆️ Naik"):
                st.session_state.pos_y = max(5, st.session_state.pos_y - 3)
            if d3.button("⬇️ Turun"):
                st.session_state.pos_y = min(95, st.session_state.pos_y + 3)
            if d4.button("➡️ Kanan"):
                st.session_state.pos_x = min(95, st.session_state.pos_x + 3)

        # TAB 2: FONT & GAYA (SEMUA DIBERI KEY AGAR TIDAK PERNAH RESET)
        with tab_style:
            font_options = [
                "Times New Roman (Formal)",
                "Georgia (Elegan)",
                "Arial (Modern/Clean)",
                "Edwardian Script (Latin Mewah)",
                "Vivaldi (Latin Artistik)",
                "Monotype Corsiva (Latin Miring)"
            ]
            st.selectbox("Pilih Jenis Font:", font_options, key="selected_font")
            
            f_col1, f_col2 = st.columns([1, 2.2])
            with f_col1:
                st.color_picker("Warna Teks:", key="text_color")
            with f_col2:
                st.slider("Ukuran Font (px):", min_value=25, max_value=220, key="font_size")
            
            custom_ttf = st.file_uploader("Upload Font Sendiri (.ttf)", type=["ttf", "otf"], key="custom_font")

        # TAB 3: EKSPOR DATA
        with tab_process:
            if not names:
                st.warning("⚠️ Upload file Excel di atas untuk memproses nama peserta massal.")
            else:
                st.success(f"✓ Siap memproses **{len(names)} sertifikat HD**.")
                btn_start = st.button(f"⚡ GENERATE {len(names)} SERTIFIKAT")

    # --- PANEL PREVIEW LANGSUNG ---
    with col_preview:
        target_center_x = int(orig_w * (st.session_state.pos_x / 100))
        target_center_y = int(orig_h * (st.session_state.pos_y / 100))

        preview_img = original_img.copy()
        draw_preview = ImageDraw.Draw(preview_img)

        # Mengambil font & warna langsung dari session_state terkini
        font_preview = get_font(st.session_state.selected_font, st.session_state.font_size, custom_ttf)
        bbox = draw_preview.textbbox((0, 0), sample_name, font=font_preview)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # Render teks di target posisi
        draw_preview.text(
            (target_center_x - (tw / 2), target_center_y - (th / 2)),
            sample_name,
            fill=st.session_state.text_color,
            font=font_preview
        )

        st.image(preview_img, caption=f"Pratinjau ({st.session_state.font_size}px, X:{st.session_state.pos_x}% Y:{st.session_state.pos_y}%)", use_container_width=True)

    # --- EKSEKUSI PEMBUATAN BATCH ZIP ---
    if cert_file is not None and names and 'btn_start' in locals() and btn_start:
        with col_controls:
            with tab_process:
                progress_bar = st.progress(0)
                status_text = st.empty()

                zip_buffer = io.BytesIO()
                font_hd = get_font(st.session_state.selected_font, st.session_state.font_size, custom_ttf)

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, nama in enumerate(names, 1):
                        status_text.text(f"Memproses ({idx}/{len(names)}): {nama}")
                        progress_bar.progress(idx / len(names))

                        cert_hd = original_img.copy()
                        draw_hd = ImageDraw.Draw(cert_hd)

                        bbox_hd = draw_hd.textbbox((0, 0), nama, font=font_hd)
                        t_w = bbox_hd[2] - bbox_hd[0]
                        t_h = bbox_hd[3] - bbox_hd[1]

                        draw_hd.text(
                            (target_center_x - (t_w / 2), target_center_y - (t_h / 2)),
                            nama,
                            fill=st.session_state.text_color,
                            font=font_hd
                        )

                        img_buffer = io.BytesIO()
                        cert_hd.save(img_buffer, format="PNG")
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
    st.info("👆 Upload desain sertifikat Anda di kotak atas untuk mulai.")
