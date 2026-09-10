import io
import os
import zipfile
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from streamlit_drawable_canvas import st_canvas

# ==========================================================
# 1. KONFIGURASI HALAMAN
# ==========================================================
st.set_page_config(
    page_title="CertifiKit Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS Responsif HP
st.markdown("""
    <style>
        #MainMenu, footer, [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"] {
            display: none !important;
        }
        header { background: transparent !important; }
        .block-container { padding: 0.6rem 0.8rem 2rem 0.8rem !important; }
        
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
        
        /* Pastikan kanvas tidak meluber keluar layar HP */
        iframe {
            max-width: 100% !important;
            border-radius: 8px;
            border: 1px solid #334155;
        }
        
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

st.markdown("""
    <div class="app-header">
        <span class="app-title">⚡ CertifiKit Studio</span>
        <span class="app-badge">Mobile Responsive</span>
    </div>
""", unsafe_allow_html=True)

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
# 3. AREA UPLOAD FILE
# ==========================================================
col_u1, col_u2 = st.columns(2)
with col_u1:
    cert_file = st.file_uploader("1. Desain Sertifikat (JPG/PNG)", type=["png", "jpg", "jpeg"])
with col_u2:
    excel_file = st.file_uploader("2. File Excel (.xlsx)", type=["xlsx", "xls"])

# ==========================================================
# 4. KANVAS & KONTROL
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

    # Pengaturan Tampilan Kanvas agar PAS di Layar HP
    st.markdown("---")
    ctrl_col1, ctrl_col2 = st.columns([1, 1])
    with ctrl_col1:
        device_view = st.radio("📱 Ukuran Layar:", ["📱 Pas Layar HP (340px)", "💻 Layar Laptop (600px)"], horizontal=True)
        display_w = 340 if "HP" in device_view else 600
    with ctrl_col2:
        action_mode = st.radio("✋ Mode Sentuh Kanvas:", ["✏️ Tarik Kotak Baru", "✋ Geser / Ubah Ukuran"], horizontal=True)
        drawing_mode = "rect" if "Tarik" in action_mode else "transform"

    # Skala Kanvas
    scale_ratio = orig_w / display_w
    display_h = int(orig_h / scale_ratio)
    preview_bg = original_img.resize((display_w, display_h), Image.Resampling.LANCZOS)

    # Layout Sejajar di PC, Bertumpuk di HP
    col_canvas, col_tools = st.columns([1.2, 1], gap="medium")

    with col_canvas:
        st.caption("👉 **Cara pakai:** Pilih '✏️ Tarik Kotak Baru' untuk buat area nama. Pilih '✋ Geser' lalu sentuh kotaknya untuk memindahkan.")
        
        canvas_result = st_canvas(
            fill_color="rgba(56, 189, 248, 0.25)",
            stroke_width=2,
            stroke_color="#38BDF8",
            background_image=preview_bg,
            update_streamlit=True,
            height=display_h,
            width=display_w,
            drawing_mode=drawing_mode,
            key=f"canvas_{display_w}_{drawing_mode}"
        )

    # Baca Koordinat Kotak
    box_coords = None
    if canvas_result.json_data is not None and len(canvas_result.json_data["objects"]) > 0:
        rect = canvas_result.json_data["objects"][-1]
        c_left = rect.get("left", 0)
        c_top = rect.get("top", 0)
        c_width = rect.get("width", 0) * rect.get("scaleX", 1)
        c_height = rect.get("height", 0) * rect.get("scaleY", 1)

        if c_width > 15 and c_height > 10:
            hd_x = int(c_left * scale_ratio)
            hd_y = int(c_top * scale_ratio)
            hd_w = int(c_width * scale_ratio)
            hd_h = int(c_height * scale_ratio)
            box_coords = (hd_x, hd_y, hd_w, hd_h)

    with col_tools:
        st.subheader("🎨 Gaya Huruf & Warna")
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

        sub_col1, sub_col2 = st.columns(2)
        with sub_col1:
            text_color = st.color_picker("Warna Teks:", "#1E293B")
        with sub_col2:
            max_font_size = st.number_input("Max Font (px):", min_value=20, max_value=250, value=110, step=5)

        st.markdown("---")
        st.subheader("🚀 Proses Data")
        
        if box_coords is None:
            st.info("👆 Buat area kotak nama terlebih dahulu di kanvas di atas/sebelah kiri.")
        elif not names:
            st.warning("⚠️ Upload file Excel di atas untuk mulai membuat sertifikat massal.")
        else:
            st.success(f"✓ Area aktif ({box_coords[2]}x{box_coords[3]}px)! Siap memproses **{len(names)} sertifikat**.")
            if st.button(f"⚡ PROSES {len(names)} SERTIFIKAT (HD)"):
                hd_x, hd_y, hd_w, hd_h = box_coords
                center_box_x = hd_x + (hd_w / 2)
                center_box_y = hd_y + (hd_h / 2)

                progress_bar = st.progress(0)
                status_text = st.empty()

                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, nama in enumerate(names, 1):
                        status_text.text(f"Memproses ({idx}/{len(names)}): {nama}")
                        progress_bar.progress(idx / len(names))

                        cert_hd = original_img.copy()
                        draw_hd = ImageDraw.Draw(cert_hd)

                        font_hd = get_auto_fit_font(nama, hd_w, hd_h, max_font_size, selected_font, custom_ttf)
                        bbox_hd = draw_hd.textbbox((0, 0), nama, font=font_hd)
                        tw = bbox_hd[2] - bbox_hd[0]
                        th = bbox_hd[3] - bbox_hd[1]

                        draw_hd.text(
                            (center_box_x - (tw / 2), center_box_y - (th / 2)),
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
                    file_name="Hasil_Sertifikat_HD.zip",
                    mime="application/zip"
                )

else:
    st.info("👆 Upload desain sertifikat Anda di kotak atas untuk membuka kanvas.")
