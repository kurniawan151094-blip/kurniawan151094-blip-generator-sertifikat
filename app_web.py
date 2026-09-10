import io
import os
import zipfile
import urllib.request
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
        <span class="app-badge">55+ Fonts Pro</span>
    </div>
""", unsafe_allow_html=True)

# ==========================================================
# 2. KATALOG FONT LENGKAP (55+ FONT WEDDING & SERTIFIKAT)
# ==========================================================
BASE_URL = "https://raw.githubusercontent.com/google/fonts/main/"

FONT_CATEGORIES = {
    "💍 Wedding & Kaligrafi Mewah": {
        "Great Vibes (Wedding Klasik)": BASE_URL + "ofl/greatvibes/GreatVibes-Regular.ttf",
        "Allura (Elegan Mengalir)": BASE_URL + "ofl/allura/Allura-Regular.ttf",
        "Alex Brush (Kaligrafi Halus)": BASE_URL + "ofl/alexbrush/AlexBrush-Regular.ttf",
        "Pinyon Script (Aristokrat Ningrat)": BASE_URL + "ofl/pinyonscript/PinyonScript-Regular.ttf",
        "Parisienne (Romantis Prancis)": BASE_URL + "ofl/parisienne/Parisienne-Regular.ttf",
        "Tangerine (Italic Chancery Anggun)": BASE_URL + "ofl/tangerine/Tangerine-Regular.ttf",
        "Italianno (Kaligrafi Italia)": BASE_URL + "ofl/italianno/Italianno-Regular.ttf",
        "Monsieur La Doulaise (Vintage Mewah)": BASE_URL + "ofl/monsieurladoulaise/MonsieurLaDoulaise-Regular.ttf",
        "Herr Von Muellerhoff (Spencerian Halus)": BASE_URL + "ofl/herrvonmuellerhoff/HerrVonMuellerhoff-Regular.ttf",
        "Lovers Quarrel (Swash Hiasan Megah)": BASE_URL + "ofl/loversquarrel/LoversQuarrel-Regular.ttf",
        "Mrs Saint Delafield (Kaligrafi Antik)": BASE_URL + "ofl/mrssaintdelafield/MrsSaintDelafield-Regular.ttf",
        "Miss Fajardose (Filigri Hias)": BASE_URL + "ofl/missfajardose/MissFajardose-Regular.ttf",
        "Rouge Script (Lembut Anggun)": BASE_URL + "ofl/rougescript/RougeScript-Regular.ttf",
        "Petit Formal Script (Formal Elegan)": BASE_URL + "ofl/petitformalscript/PetitFormalScript-Regular.ttf",
        "Qwigley (Lengkung Ramping)": BASE_URL + "ofl/qwigley/Qwigley-Regular.ttf",
        "Ruthie (Lincah Bersambung)": BASE_URL + "ofl/ruthie/Ruthie-Regular.ttf",
        "Meie Script (Klasik Jerman)": BASE_URL + "ofl/meiescript/MeieScript-Regular.ttf",
        "MonteCarlo (Dekoratif Pesta)": BASE_URL + "ofl/montecarlo/MonteCarlo-Regular.ttf",
        "Felipa (Gaya Cursive Spanyol)": BASE_URL + "ofl/felipa/Felipa-Regular.ttf",
        "Engagement (Undangan Pernikahan)": BASE_URL + "ofl/engagement/Engagement-Regular.ttf",
        "Bilbo Swash Caps (Kapital Hias)": BASE_URL + "ofl/bilboswashcaps/BilboSwashCaps-Regular.ttf",
    },
    "🏆 Sertifikat & Piagam Formal": {
        "Cinzel Bold (Imperial Romawi)": BASE_URL + "ofl/cinzel/static/Cinzel-Bold.ttf",
        "Cinzel Decorative (Piagam Ukir)": BASE_URL + "ofl/cinzeldecorative/CinzelDecorative-Bold.ttf",
        "Playfair Display Bold (Serif Mewah)": BASE_URL + "ofl/playfairdisplay/static/PlayfairDisplay-Bold.ttf",
        "Playfair Display Italic (Serif Miring)": BASE_URL + "ofl/playfairdisplay/static/PlayfairDisplay-Italic.ttf",
        "Cormorant Garamond (Klasik Kerajaan)": BASE_URL + "ofl/cormorantgaramond/static/CormorantGaramond-Bold.ttf",
        "EB Garamond Bold (Presisi Akademik)": BASE_URL + "ofl/ebgaramond/static/EBGaramond-Bold.ttf",
        "Prata (Serif Kontras Tinggi)": BASE_URL + "ofl/prata/Prata-Regular.ttf",
        "Marcellus (Monumen Klasik)": BASE_URL + "ofl/marcellus/Marcellus-Regular.ttf",
        "Bellefair (Serif Ramping Elegan)": BASE_URL + "ofl/bellefair/Bellefair-Regular.ttf",
        "Castoro (Serif Buku Berwibawa)": BASE_URL + "ofl/castoro/Castoro-Regular.ttf",
        "Lora Bold (Harmonis & Tajam)": BASE_URL + "ofl/lora/static/Lora-Bold.ttf",
        "Merriweather Bold (Kokoh Formal)": BASE_URL + "ofl/merriweather/Merriweather-Bold.ttf"
    },
    "✍️ Signature & Handwritten": {
        "Arizonia (Kuas Artistik)": BASE_URL + "ofl/arizonia/Arizonia-Regular.ttf",
        "Sacramento (Monoline Kasual)": BASE_URL + "ofl/sacramento/Sacramento-Regular.ttf",
        "Satisfy (Tanda Tangan Lembut)": BASE_URL + "ofl/satisfy/Satisfy-Regular.ttf",
        "Rochester (Gaya Retro Victoria)": BASE_URL + "ofl/rochester/Rochester-Regular.ttf",
        "Marck Script (Tulisan Tangan Pena)": BASE_URL + "ofl/marckscript/MarckScript-Regular.ttf",
        "Yellowtail (Kuas Tebal Kasual)": BASE_URL + "ofl/yellowtail/Yellowtail-Regular.ttf",
        "Courgette (Pena Miring Halus)": BASE_URL + "ofl/courgette/Courgette-Regular.ttf",
        "Damion (Gaya Casual 50-an)": BASE_URL + "ofl/damion/Damion-Regular.ttf",
        "Kaushan Script (Kuas Dinamis)": BASE_URL + "ofl/kaushanscript/KaushanScript-Regular.ttf",
        "Niconne (Feminim Bersahabat)": BASE_URL + "ofl/niconne/Niconne-Regular.ttf",
        "Bad Script (Tulisan Buku Catatan)": BASE_URL + "ofl/badscript/BadScript-Regular.ttf",
        "Cookie (Gaya Pin-up Manis)": BASE_URL + "ofl/cookie/Cookie-Regular.ttf",
        "Stalemate (Skrip Cepat Mengalir)": BASE_URL + "ofl/stalemate/Stalemate-Regular.ttf",
        "Homemade Apple (Tanda Tangan Tinta)": BASE_URL + "ofl/homemadeapple/HomemadeApple-Regular.ttf",
        "Caveat Bold (Spidol Tulisan Tangan)": BASE_URL + "ofl/caveat/static/Caveat-Bold.ttf",
        "La Belle Aurore (Coretan Tangan Alami)": BASE_URL + "ofl/labelleaurore/LaBelleAurore.ttf"
    },
    "✨ Modern & Minimalis": {
        "Montserrat Bold (Modern Berani)": BASE_URL + "ofl/montserrat/static/Montserrat-Bold.ttf",
        "Bebas Neue (Kapital Headline Kuat)": BASE_URL + "ofl/bebasneue/BebasNeue-Regular.ttf",
        "Poppins Bold (Geometris Bersih)": BASE_URL + "ofl/poppins/Poppins-Bold.ttf",
        "Oswald Bold (Ramping Tegas)": BASE_URL + "ofl/oswald/static/Oswald-Bold.ttf",
        "Raleway Bold (Modern Berkelas)": BASE_URL + "ofl/raleway/static/Raleway-Bold.ttf",
        "Lato Bold (Humanis Seimbang)": BASE_URL + "ofl/lato/Lato-Bold.ttf"
    },
    "💻 Font Sistem": {
        "Times New Roman (Sistem)": "times.ttf",
        "Arial (Sistem)": "arial.ttf",
        "Georgia (Sistem)": "georgia.ttf"
    }
}

# Inisialisasi State
if "pos_x" not in st.session_state:
    st.session_state.pos_x = 50
if "pos_y" not in st.session_state:
    st.session_state.pos_y = 52
if "font_size" not in st.session_state:
    st.session_state.font_size = 90
if "text_color" not in st.session_state:
    st.session_state.text_color = "#1E293B"
if "font_cat" not in st.session_state:
    st.session_state.font_cat = "💍 Wedding & Kaligrafi Mewah"
if "selected_font" not in st.session_state:
    st.session_state.selected_font = "Great Vibes (Wedding Klasik)"

# Folder cache lokal
FONTS_DIR = "app_fonts"
os.makedirs(FONTS_DIR, exist_ok=True)

# Mesin font dinamis
def get_font(font_name, font_size, custom_font_file=None):
    font_size = int(font_size)

    # 1. Custom font upload
    if font_name == "📁 Font Kustom (File Upload)" and custom_font_file is not None:
        try:
            custom_font_file.seek(0)
            return ImageFont.truetype(io.BytesIO(custom_font_file.getvalue()), font_size)
        except Exception:
            pass

    # 2. Cari URL dari katalog 55+ font
    font_url = None
    for cat, fonts in FONT_CATEGORIES.items():
        if font_name in fonts:
            font_url = fonts[font_name]
            break

    if font_url and font_url.startswith("http"):
        safe_filename = "".join(c for c in font_name if c.isalnum()) + ".ttf"
        local_path = os.path.join(FONTS_DIR, safe_filename)
        if not os.path.exists(local_path):
            try:
                urllib.request.urlretrieve(font_url, local_path)
            except Exception:
                pass
        if os.path.exists(local_path):
            try:
                return ImageFont.truetype(local_path, font_size)
            except Exception:
                pass

    # 3. Font sistem OS
    system_paths = [
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
        "/usr/share/fonts", "/usr/share/fonts/truetype", "/Library/Fonts"
    ]
    for sp in system_paths:
        p = os.path.join(sp, font_url if font_url else "arial.ttf")
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, font_size)
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

        # TAB 1: POSISI
        with tab_pos:
            st.caption("📍 **Posisi Cepat:**")
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

            st.caption("🎮 **Geser Halus:**")
            d1, d2, d3, d4 = st.columns(4)
            if d1.button("⬅️ Kiri"):
                st.session_state.pos_x = max(5, st.session_state.pos_x - 3)
            if d2.button("⬆️ Naik"):
                st.session_state.pos_y = max(5, st.session_state.pos_y - 3)
            if d3.button("⬇️ Turun"):
                st.session_state.pos_y = min(95, st.session_state.pos_y + 3)
            if d4.button("➡️ Kanan"):
                st.session_state.pos_x = min(95, st.session_state.pos_x + 3)

        # TAB 2: FONT & GAYA (DENGAN FILTER KATEGORI & 55+ FONT)
        with tab_style:
            custom_ttf = st.file_uploader("Upload Font Sendiri (.ttf/.otf)", type=["ttf", "otf"], key="custom_font")

            st.caption("🔍 **Pilih Koleksi & Jenis Font:**")
            cat_options = list(FONT_CATEGORIES.keys())
            if custom_ttf is not None:
                cat_options.insert(0, "📁 Font Kustom (File Upload)")

            selected_cat = st.selectbox("Kategori Font:", cat_options, key="font_cat")

            # Ambil daftar font berdasarkan kategori yang dipilih
            if selected_cat == "📁 Font Kustom (File Upload)":
                font_list = ["📁 Font Kustom (File Upload)"]
            else:
                font_list = list(FONT_CATEGORIES[selected_cat].keys())

            # Sinkronisasi pilihan font jika kategori berganti
            if st.session_state.selected_font not in font_list:
                st.session_state.selected_font = font_list[0]

            selected_font = st.selectbox(
                f"Pilih Font ({len(font_list)} Pilihan):",
                font_list,
                key="selected_font"
            )

            f_col1, f_col2 = st.columns([1, 2.2])
            with f_col1:
                st.color_picker("Warna Teks:", key="text_color")
            with f_col2:
                st.slider("Ukuran Font (px):", min_value=25, max_value=240, key="font_size")

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

        # Muat font terpilih
        font_preview = get_font(st.session_state.selected_font, st.session_state.font_size, custom_ttf)
        bbox = draw_preview.textbbox((0, 0), sample_name, font=font_preview)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # Render teks tepat di titik target
        draw_preview.text(
            (target_center_x - (tw / 2), target_center_y - (th / 2)),
            sample_name,
            fill=st.session_state.text_color,
            font=font_preview
        )

        st.image(
            preview_img,
            caption=f"Pratinjau: {st.session_state.selected_font} ({st.session_state.font_size}px)",
            use_container_width=True
        )

    # --- EKSEKUSI PEMBUATAN BATCH ZIP ---
    if cert_file is not None and names and 'btn_start' in locals() and btn_start:
        with col_controls:
            with tab_process:
                progress_bar = st.progress(0)
                status_text = st.empty()

                zip_buffer = io.BytesIO()
                # Font dimuat 1 kali untuk efisiensi ekspor massal
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
