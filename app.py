import sys
import subprocess

try:
    import google.generativeai as genai
    import fitz  # PyMuPDF
    from docx import Document
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-generativeai", "PyMuPDF", "python-docx"])
    import google.generativeai as genai
    import fitz
    from docx import Document

import streamlit as st
import os
from io import BytesIO
import hr_db

# Initialize database
hr_db.init_db()
from google.api_core.exceptions import ResourceExhausted

def safe_generate(model, prompt_or_parts, enable_search=False):
    import google.generativeai as genai
    import streamlit as st
    
    try:
        # Gerçekten erişilebilir olan modelleri dinamik olarak çek
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        fallback_models = [m.replace('models/', '') for m in available if 'gemini' in m.lower()]
    except Exception:
        fallback_models = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        
    current_model = model
    
    for attempt in range(len(fallback_models) + 1):
        try:
            if enable_search:
                try:
                    return current_model.generate_content(prompt_or_parts, tools='google_search_retrieval')
                except Exception as e:
                    return current_model.generate_content(prompt_or_parts)
            else:
                return current_model.generate_content(prompt_or_parts)
                
        except Exception as e:
            err_msg = str(e).lower()
            # 404 (bulunamadı) veya 429 (kota doldu) hatalarında otomatik diğer modele geç
            if "429" in err_msg or "resourceexhausted" in err_msg or "404" in err_msg or "not found" in err_msg or "not supported" in err_msg:
                if attempt < len(fallback_models):
                    next_model_name = fallback_models[attempt]
                    st.toast(f"Otomatik Geçiş: '{next_model_name}' deneniyor...", icon="🔄")
                    current_model = genai.GenerativeModel(next_model_name)
                else:
                    st.error("Hesabınızdaki kullanılabilir tüm yapay zeka modelleri denendi ancak erişim sağlanamadı. Lütfen API anahtarınızı kontrol edin.")
                    st.stop()
            else:
                st.error(f"Yapay zeka yanıt üretirken beklenmeyen hata: {e}")
                st.stop()

st.set_page_config(page_title="AY Çağrı Merkezi - İK Disiplin", layout="wide", page_icon="🏢")

import base64
import urllib.request

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

logo_path = "logo.png"
logo_b64 = get_base64_of_bin_file(logo_path)

# --- GLOBAL BILGI CSS INJECTION ---
st.markdown(f"""
<style>
/* Ana Arka Plan ve Yazı Rengi */
.stApp {{
    background: #FAFAFA !important; /* Premium pearl white */
    color: #111827 !important; /* Sleek dark gray almost black */
}}

/* Sayfa üst boşluğunu azaltma (Daha yukarıdan başlama) */
.block-container {{
    padding-top: 2.5rem !important; /* Navbar'ın kesmemesi için 2.5rem ideal */
    padding-bottom: 2rem !important;
}}

/* Tüm fontlar daha şık */
html, body, .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}

/* Streamlit etiketlerinin koyu yapılması (Okunabilirlik Garantisi) */
.st-emotion-cache-10trncj, label, .stMarkdown p, .st-emotion-cache-1wivap2 {{
    color: #0033A0 !important; /* Logo Kurumsal Mavi */
    font-weight: 500 !important;
}}

/* Streamlit expander (Ağaç Yapısı) Başlıkları */
[data-testid="stExpander"] {{
    background-color: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    margin-bottom: 8px !important;
}}

/* Expander Başlık Metinleri (Logo Mavisi) */
[data-testid="stExpander"] summary p {{
    color: #0033A0 !important;
    font-weight: 600 !important;
    font-size: 15px !important;
}}

[data-testid="stExpander"]:hover {{
    border-color: #F05A28 !important; /* Logo Turuncu Vurgu */
}}

/* Expander İç Gövdesi (İçerik Kısmı) - Marka Renkleriyle Bütünleşik */
[data-testid="stExpanderDetails"] {{
    background: linear-gradient(to bottom, #F4F8FC, #FFFFFF) !important; /* Çok hafif logo mavisi tonu */
    border-top: 2px solid #F05A28 !important; /* İnce turuncu marka çizgisi */
    border-radius: 0 0 12px 12px !important;
    padding-top: 20px !important;
}}

/* Flat Design Konteynerlar ve Kartlar */
.st-emotion-cache-1wmy9hl, .st-emotion-cache-16txtl3, .stFileUploader, .stTextArea {{
    background: #FFFFFF !important;
    border: 1px solid #F3F4F6 !important;
    border-radius: 16px !important; /* Modern kavisler */
    padding: 24px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.02) !important;
    transition: all 0.3s ease !important;
}}

.st-emotion-cache-1wmy9hl:hover, .st-emotion-cache-16txtl3:hover, .stFileUploader:hover {{
    box-shadow: 0 8px 30px rgba(0,0,0,0.04) !important;
    transform: translateY(-2px) !important;
}}

/* Premium AI Buttons (Logo Colors) */
.stButton > button {{
    background: linear-gradient(135deg, #0033A0 0%, #0055FF 100%) !important; /* Logo Koyu Mavi'den Açık Mavi'ye */
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important; 
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    padding: 0.7rem 1.5rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(0, 51, 160, 0.2) !important;
}}

.stButton > button:hover {{
    background: linear-gradient(135deg, #F05A28 0%, #F57245 100%) !important; /* Hover'da Logo Turuncusu */
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(240, 90, 40, 0.3) !important;
    color: #FFFFFF !important;
    border: none !important;
}}

/* Başlık ve Metin Rengi Düzeltmeleri */
h1, h2, h3, h4, h5, h6 {{
    color: #0033A0 !important; /* Logo Kurumsal Mavi */
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
}}

.main-app-title {{
    color: #F05A28 !important; /* Ana Başlık Turuncu Override */
}}

/* Input Alanları */
.stTextArea textarea, .stTextInput input, .stSelectbox > div > div {{
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    color: #1F2937 !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}}

.stTextArea textarea:focus, .stTextInput input:focus, .stSelectbox > div > div:focus {{
    border-color: #F05A28 !important; /* Odaklanmada Turuncu */
    box-shadow: 0 0 0 3px rgba(240, 90, 40, 0.15) !important;
    background: #FFFFFF !important;
}}
</style>
""", unsafe_allow_html=True)



# Session state initialization
if "step" not in st.session_state:
    st.session_state.step = 0
if "tutanak_text" not in st.session_state:
    st.session_state.tutanak_text = ""
if "tutanak_summary" not in st.session_state:
    st.session_state.tutanak_summary = ""
if "savunma_istem_metni" not in st.session_state:
    st.session_state.savunma_istem_metni = ""
if "savunma_text" not in st.session_state:
    st.session_state.savunma_text = ""
if "karar_sonucu" not in st.session_state:
    st.session_state.karar_sonucu = ""
if "nihai_belge" not in st.session_state:
    st.session_state.nihai_belge = ""
if "yonetmelik_text" not in st.session_state:
    st.session_state.yonetmelik_text = ""


def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

import glob

import datetime
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

def set_text_preserve_style(paragraph, new_text):
    if not paragraph.runs:
        paragraph.add_run(new_text)
        return
    paragraph.runs[0].text = new_text
    for i in range(1, len(paragraph.runs)):
        paragraph.runs[i].text = ""

def set_cell_preserve_style(cell, new_text):
    if cell.paragraphs:
        set_text_preserve_style(cell.paragraphs[0], new_text)
        # Diğer paragrafları temizle
        for i in range(1, len(cell.paragraphs)):
            cell.paragraphs[i].clear()
    else:
        cell.text = new_text

def create_docx(text, title="Belge"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    hr_dir = os.path.join(base_dir, "..", "HR")
    template_files = glob.glob(os.path.join(hr_dir, "*rnek.docx"))
    
    doc = None
    if template_files:
        try:
            doc = Document(template_files[0])
            
            # P0: Tarih
            if len(doc.paragraphs) > 0:
                set_text_preserve_style(doc.paragraphs[0], f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y')}")
            
            # P1: Başlık
            if len(doc.paragraphs) > 1:
                spaced_title = " ".join(list(title.upper()))
                set_text_preserve_style(doc.paragraphs[1], spaced_title)
                
            # Table 0: Bilgi Tablosu
            if len(doc.tables) > 0:
                table = doc.tables[0]
                if len(table.rows) > 2:
                    set_cell_preserve_style(table.rows[0].cells[0], "Konu")
                    set_cell_preserve_style(table.rows[0].cells[1], f": {title}")
                    set_cell_preserve_style(table.rows[1].cells[0], "Tarih")
                    set_cell_preserve_style(table.rows[1].cells[1], f": {datetime.datetime.now().strftime('%d.%m.%Y')}")
                    set_cell_preserve_style(table.rows[2].cells[0], "İlgili Personel")
                    set_cell_preserve_style(table.rows[2].cells[1], ": Belge Tebellüğ Eden")
                    
            # P2 ve P3: Bölüm Başlıkları (Renkleri koruyarak güncelle)
            if len(doc.paragraphs) > 3:
                set_text_preserve_style(doc.paragraphs[2], "1. Belge / Personel Bilgileri")
                set_text_preserve_style(doc.paragraphs[3], "2. İstem ve Karar Detayları")
                
            # P4 ve P5: Eski test metinlerini sil (Gövdeyi temizle)
            if len(doc.paragraphs) > 5:
                p4 = doc.paragraphs[4]
                p4._element.getparent().remove(p4._element)
                p5 = doc.paragraphs[4] # P4 silinince P5 kayarak 4. index'e geldi
                p5._element.getparent().remove(p5._element)
                
                insertion_point = doc.paragraphs[4] # Yeni P6 (Bilginize sunulur.)
            else:
                insertion_point = None
                
            # Yapay Zeka Metnini İki Yana Yaslı (Justify) Olarak Enjekte Et
            for p_text in text.split('\n'):
                if p_text.strip():
                    if insertion_point:
                        new_p = insertion_point.insert_paragraph_before(p_text.strip())
                        new_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        new_p.paragraph_format.space_after = Pt(12)
                    else:
                        new_p = doc.add_paragraph(p_text.strip())
                        new_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        new_p.paragraph_format.space_after = Pt(12)
            
            # Alt kısımdaki 'test yazısı' ibarelerini temizle ve resmiyete dök
            for p in doc.paragraphs:
                if "test belgesinin" in p.text or "test belgesi" in p.text:
                    new_text = p.text.replace("test belgesinin", "belgenin").replace("test belgesi", "belge")
                    new_text = new_text.replace("içeriğini okudum ve teyit ettim", "içeriğini okudum ve bir nüshasını elden teslim aldım")
                    set_text_preserve_style(p, new_text)
                        
            io_stream = BytesIO()
            doc.save(io_stream)
            io_stream.seek(0)
            return io_stream
            
        except Exception as e:
            print(f"Şablon enjeksiyon hatası: {e}")
            doc = None
            
    if doc is None:
        doc = Document()
        doc.add_heading(title, 0)
        for p in text.split('\n'):
            if p.strip():
                doc.add_paragraph(p)
    
    io_stream = BytesIO()
    doc.save(io_stream)
    io_stream.seek(0)
    return io_stream

st.markdown(f"""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
    <div style="display: flex; align-items: center;">
        <div style="background-color: #FFFFFF; border: 2px solid #F05A28; border-radius: 14px; width: 54px; height: 54px; display: flex; align-items: center; justify-content: center; margin-right: 18px; font-size: 26px; box-shadow: 0 4px 12px rgba(240, 90, 40, 0.15);">
            👥
        </div>
        <h1 class='main-app-title' style='font-size: 38px; font-weight: 800; margin: 0;'>
            HR YÖNETİM ASİSTANI
        </h1>
    </div>
    <img src="data:image/png;base64,{logo_b64}" style="max-width:250px; mix-blend-mode: darken;">
</div>
""", unsafe_allow_html=True)

# --- DASHBOARD SUMMARY ---
stats = hr_db.get_summary_stats()

st.markdown(f"""
<div style="display: flex; gap: 15px; margin-bottom: 20px;">
    <div style="flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); text-align: center;">
        <div style="color: #6B7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">Toplam Dosya</div>
        <div style="color: #111827; font-size: 28px; font-weight: 800; margin-top: 5px;">{stats['total']}</div>
    </div>
    <div style="flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); text-align: center;">
        <div style="color: #6B7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">Tutanak Tutuldu</div>
        <div style="color: #F05A28; font-size: 28px; font-weight: 800; margin-top: 5px;">{stats['tutanak']}</div>
    </div>
    <div style="flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); text-align: center;">
        <div style="color: #6B7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">Savunma Beklenen</div>
        <div style="color: #F59E0B; font-size: 28px; font-weight: 800; margin-top: 5px;">{stats['bekleyen']}</div>
    </div>
    <div style="flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); text-align: center;">
        <div style="color: #6B7280; font-size: 13px; font-weight: 600; text-transform: uppercase;">Sonuçlanan</div>
        <div style="color: #10B981; font-size: 28px; font-weight: 800; margin-top: 5px;">{stats['sonuc']}</div>
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("⚙️ Gizli Alan: Uygulama ve Sistem Ayarları", expanded=False):
    import os
    api_key_file = "api_key.txt"
    saved_api_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            saved_api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
        
    if not saved_api_key and os.path.exists(api_key_file):
        with open(api_key_file, "r") as f:
            saved_api_key = f.read().strip()

    col_api1, col_api2 = st.columns(2)
    with col_api1:
        api_key = st.text_input("🔑 Gemini API Key", type="password", value=saved_api_key, help="İlk girişinizden sonra otomatik kaydedilir.")
        st.link_button("Kalan Kotamı Göster", "https://aistudio.google.com/app/apikey")
        
    if api_key:
        if api_key != saved_api_key:
            with open(api_key_file, "w") as f:
                f.write(api_key)
                
        os.environ["GOOGLE_API_KEY"] = api_key
        genai.configure(api_key=api_key)
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            st.success("✅ API Key geçerli.")
            
            clean_models = [m.replace('models/', '') for m in available_models]
            default_idx = 0
            if 'gemini-1.5-flash' in clean_models:
                default_idx = clean_models.index('gemini-1.5-flash')
            elif 'gemini-2.5-flash' in clean_models:
                default_idx = clean_models.index('gemini-2.5-flash')
                
            with col_api2:
                st.session_state.active_model = st.selectbox(
                    "🤖 Yapay Zeka Modeli:",
                    options=clean_models,
                    index=default_idx
                )
                
        except Exception as e:
            st.error(f"API Key geçersiz: {e}")
            st.stop()
    else:
        st.warning("Lütfen işlem yapmadan önce API anahtarınızı girin.")
        st.stop()

# ----------------- ADIM 1: YÖNETMELİK -----------------
with st.expander("🏢 1. Ön Hazırlık: Disiplin Yönetmeliği & Kanunlar", expanded=(st.session_state.step == 1)):
    
    kb_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")
    os.makedirs(kb_dir, exist_ok=True)
    
    permanent_files = glob.glob(os.path.join(kb_dir, "*.txt"))
    permanent_text = ""
    saved_file_names = []
    
    for pf in permanent_files:
        with open(pf, "r", encoding="utf-8") as f:
            permanent_text += f.read() + "\n\n"
        saved_file_names.append(os.path.basename(pf).replace(".txt", ""))
        
    st.write("Bu aşamada sisteme yüklediğiniz ana kanunlar ve yönetmelikler **kalıcı olarak** hafızaya kazınır. Uygulamayı kapatsanız bile silinmez. Her yeni olayda tekrar yüklemenize gerek kalmaz.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Kalıcı Hafıza (Demirbaşlar)")
        if saved_file_names:
            st.info("Kayıtlı Belgeler:\n- " + "\n- ".join(saved_file_names))
            if st.button("Kalıcı Hafızayı Temizle"):
                for pf in permanent_files:
                    os.remove(pf)
                st.session_state.yonetmelik_text = ""
                st.rerun()
        else:
            st.warning("Hafızada henüz kayıtlı kalıcı belge yok.")
            
        yonetmelik_files = st.file_uploader("Kalıcı Belge Ekle (İş Kanunu vb.)", type=["docx", "pdf"], accept_multiple_files=True, key="permanent")
        if yonetmelik_files and st.button("Kalıcı Olarak Kaydet"):
            with st.spinner("🏢 Yapay Zeka belgeleri kalıcı hafızasına kazıyor..."):
                for y_file in yonetmelik_files:
                    text = ""
                    if y_file.type == "application/pdf":
                        try:
                            pdf_bytes = y_file.getvalue()
                            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                            extracted = ""
                            for page in pdf_doc:
                                extracted += page.get_text()
                            
                            if len(extracted.strip()) > 50:
                                text = f"--- Belge: {y_file.name} ---\n{extracted}"
                            else:
                                doc_parts = [{"mime_type": "application/pdf", "data": pdf_bytes}, "Bu dokümandaki tüm metni eksiksiz olarak çıkar ve yaz."]
                                model = genai.GenerativeModel(st.session_state.active_model)
                                response = safe_generate(model, doc_parts)
                                text = f"--- Belge: {y_file.name} ---\n{response.text}"
                        except Exception as e:
                            st.error(f"{y_file.name} Okuma hatası: {e}")
                    else:
                        doc = Document(y_file)
                        text = f"--- Belge: {y_file.name} ---\n" + "\n".join([p.text for p in doc.paragraphs])
                    
                    if text:
                        save_path = os.path.join(kb_dir, f"{y_file.name}.txt")
                        with open(save_path, "w", encoding="utf-8") as f:
                            f.write(text)
            st.success(f"{len(yonetmelik_files)} belge KALICI olarak kaydedildi!")
            st.rerun()

    with col2:
        st.subheader("📎 Olaya Özel İlave Belgeler")
        st.write("Eğer sadece bu tutanak için eklemek istediğiniz geçici bir belge varsa yükleyin. (Sistem kapandığında silinir)")
        gecici_files = st.file_uploader("Geçici Belge Seç", type=["docx", "pdf"], accept_multiple_files=True, key="temporary")
        if gecici_files and st.button("Geçici Olarak İşle"):
            with st.spinner("Geçici belgeler okunuyor..."):
                all_gecici = []
                for g_file in gecici_files:
                    text = ""
                    if g_file.type == "application/pdf":
                        pdf_doc = fitz.open(stream=g_file.getvalue(), filetype="pdf")
                        for page in pdf_doc:
                            text += page.get_text()
                        if len(text.strip()) < 50:
                            model = genai.GenerativeModel(st.session_state.active_model)
                            text = safe_generate(model, [{"mime_type": "application/pdf", "data": g_file.getvalue()}, "Metne dök"]).text
                    else:
                        doc = Document(g_file)
                        text = "\n".join([p.text for p in doc.paragraphs])
                    all_gecici.append(f"--- Belge (Geçici): {g_file.name} ---\n{text}")
                st.session_state.gecici_text = "\n\n".join(all_gecici)
            st.success("Geçici belgeler hafızaya alındı!")

    st.session_state.yonetmelik_text = permanent_text + "\n\n" + st.session_state.get("gecici_text", "")
    
    st.markdown("---")
    if st.button("Sonraki Adım: Tutanak Yükleme"):
        st.session_state.step = 2
        st.rerun()

# ----------------- ADIM 2: TUTANAK YÜKLEME -----------------
with st.expander("📝 2. Tutanak Yükleme ve Analizi", expanded=(st.session_state.step == 2)):
    st.write("Lütfen olaya ilişkin tutanağı PDF veya Word formatında yükleyin.")
    tutanak_file = st.file_uploader("Tutanak Seç", type=["pdf", "docx"])
    
    if tutanak_file:
        if st.button("Tutanağı Analiz Et"):
            with st.spinner("🏢 ISS Yapay Zeka tutanak detaylarını dijitalleştiriyor..."):
                prompt_text = "Aşağıdaki tutanak belgesini incele. Çıktıyı SADECE geçerli bir JSON formatında ver. JSON yapısı şu şekilde olmalı: {\"name\": \"Hakkında tutanak tutulan çalışanın Adı ve Soyadı\", \"details\": \"Varsa sicil numarası ve unvanı (yoksa boş bırak)\", \"summary\": \"Olayın ne olduğu, tarihi ve ihlal edilen kuralların detaylı özeti\"}. Sadece JSON kodu döndür, başka hiçbir metin veya markdown yazma."
                
                try:
                    if tutanak_file.type == "application/pdf":
                        pdf_bytes = tutanak_file.getvalue()
                        doc_parts = [
                            {"mime_type": "application/pdf", "data": pdf_bytes},
                            prompt_text
                        ]
                        model = genai.GenerativeModel(st.session_state.active_model)
                        response = safe_generate(model, doc_parts)
                        st.session_state.tutanak_text = "PDF doğrudan yapay zekaya okutuldu."
                    else:
                        doc = Document(tutanak_file)
                        text = "\n".join([p.text for p in doc.paragraphs])
                        st.session_state.tutanak_text = text
                        prompt = f"{prompt_text}\n\nTutanak Metni: {text}"
                        model = genai.GenerativeModel(st.session_state.active_model)
                        response = safe_generate(model, prompt)
                    
                    # Parse JSON
                    import json
                    raw_text = response.text.replace("```json", "").replace("```", "").strip()
                    try:
                        parsed_data = json.loads(raw_text)
                        emp_name = parsed_data.get("name", "Bilinmeyen Personel")
                        emp_details = parsed_data.get("details", "")
                        st.session_state.tutanak_summary = parsed_data.get("summary", "")
                    except Exception as json_e:
                        st.session_state.tutanak_summary = response.text
                        emp_name = "Bilinmeyen Personel"
                        emp_details = ""
                    
                    # Veritabanına kayıt
                    if not st.session_state.get('current_record_id'):
                        rec_id = hr_db.create_record(emp_name, emp_details, "Tutanak Tutuldu")
                        st.session_state.current_record_id = rec_id
                        
                    st.success("Tutanak analiz edildi ve sistem kaydı otomatik oluşturuldu!")
                    
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")
            
    if st.session_state.tutanak_summary:
        st.subheader("Tutanak Özeti")
        st.write(st.session_state.tutanak_summary)
        if st.button("Sonraki Adım: Savunma İstemi Oluştur"):
            st.session_state.step = 3
            st.rerun()

# ----------------- ADIM 3: SAVUNMA İSTEMİ -----------------
with st.expander("⚖️ 3. Savunma İstem Belgesi", expanded=(st.session_state.step == 3)):
    st.write("Tutanak özetine dayanarak çalışana verilecek resmi savunma istem metni oluşturuluyor.")
    
    if not st.session_state.tutanak_summary:
        st.warning("Lütfen önce 2. adımdan tutanak yükleyin.")
    else:
        if st.button("Savunma İstem Metni Hazırla"):
            with st.spinner("🏢 ISS Yapay Zeka hukuki metin hazırlıyor..."):
                prompt = f"""Sen uzman bir İş Hukuku danışmanısın. Aşağıdaki tutanak özetine dayanarak bir 'Savunma İstem Metni' (SADECE GÖVDE METNİ) hazırla. 
                
                ÇOK ÖNEMLİ KURALLAR:
                1. Mektup antetli kağıda basılacağı için KESİNLİKLE şirket adı, logo, tarih, adres, imza alanı gibi üst/alt bilgi kısımlarını YAZMA. Sadece mektubun içeriğini yaz.
                2. KESİNLİKLE Markdown kullanma! Kalın yazı (**) veya madde işareti (-) kullanma. Sadece düz metin (plain text) paragrafları olsun.
                3. Sadece konuya gir ve doğrudan çalışana hitaben yaz.
                4. 4857 Sayılı İş Kanunu madde 109 uyarınca yazılı savunma istendiğini, 2 gün içerisinde savunma verilmesi gerektiğini belirt.
                5. Bu yazıyı hazırlarken güncel mevzuat.gov.tr kaynaklarını ve İş Kanunu prensiplerini dikkate alan bir İş Hukukçusu gibi davran.
                6. (ÇOK ÖNEMLİ) Aşağıda 'İlgili Yönetmelikler ve Kanunlar' kısmında sana sunulan (İş Kanunu, Personel Disiplin Yönetmeliği, Personel Sözleşmesi vb.) TÜM metinleri dikkate al. Çalışanın KESİNLİKLE bu metinlerin tam olarak hangi maddesini ve bendini ihlal ettiğini açıkça yazarak metnin içinde atıfta bulun (Örn: 'Şirket Personel Disiplin Yönetmeliği Madde 4.2 ve İş Kanunu Madde 25/II uyarınca...'). 
                7. (ÖNEMLİ) Farklı konulara veya alt bölümlere geçtiğinde araya 1 TAM SATIR (ENTER) BOŞLUK BIRAK ki yazılar iç içe geçmesin.
                
                İlgili Yönetmelikler ve Kanunlar (Eğer yüklendiyse):
                {st.session_state.yonetmelik_text if st.session_state.yonetmelik_text else 'Belirtilmedi'}
                
                Tutanak Özeti:
                {st.session_state.tutanak_summary}
                """
                model = genai.GenerativeModel(st.session_state.active_model)
                response = safe_generate(model, prompt)
                st.session_state.savunma_istem_metni = response.text
                
                if st.session_state.get('current_record_id'):
                    hr_db.update_status(st.session_state.current_record_id, "Savunma Bekleniyor")
                
        if st.session_state.savunma_istem_metni:
            st.text_area("Oluşturulan Metin", st.session_state.savunma_istem_metni, height=300)
            
            docx_file = create_docx(st.session_state.savunma_istem_metni, "Savunma İstem Yazısı")
            st.download_button("Word Olarak İndir (DOCX)", data=docx_file, file_name="savunma_istem_yazisi.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
            if st.button("Sonraki Adım: Çalışan Savunmasını Yükle"):
                st.session_state.step = 4
                st.rerun()

# ----------------- ADIM 4: SAVUNMA YÜKLEME -----------------
with st.expander("🛡️ 4. Çalışan Savunması ve Değerlendirme", expanded=(st.session_state.step == 4)):
    st.write("Çalışanın el yazısı ile teslim ettiği PDF formatındaki savunmayı yükleyin.")
    savunma_file = st.file_uploader("Savunma Seç", type=["pdf"])
    
    if savunma_file:
        if st.button("Savunmayı Oku ve Özetle"):
            with st.spinner("🏢 ISS Yapay Zeka el yazısını (OCR) okuyup analiz ediyor..."):
                try:
                    pdf_bytes = savunma_file.getvalue()
                    doc_parts = [
                        {"mime_type": "application/pdf", "data": pdf_bytes},
                        "Bu PDF dosyasındaki el yazısı savunmayı oku ve metne dök. Sonrasında çalışanın temel argümanlarını 3-4 maddede özetle."
                    ]
                    model = genai.GenerativeModel(st.session_state.active_model)
                    response = safe_generate(model, doc_parts)
                    st.session_state.savunma_text = response.text
                    
                    if st.session_state.get('current_record_id'):
                        hr_db.update_status(st.session_state.current_record_id, "Savunma Alındı")
                except Exception as e:
                    st.error(f"OCR hatası: {e}")
            
            st.success("Savunma okundu!")
            
    if st.session_state.savunma_text:
        st.subheader("Çalışan Savunması (Çözümlenmiş)")
        st.write(st.session_state.savunma_text)
        if st.button("Sonraki Adım: Hukuki Karar Motoru"):
            st.session_state.step = 5
            st.rerun()

# ----------------- ADIM 5: KARAR MOTORU -----------------
with st.expander("🧠 5. Nihai Karar Motoru", expanded=(st.session_state.step == 5)):
    st.write("Şirket yönetmeliği, tutanak, savunma, İş Kanunu ve Yargıtay İçtihatları çerçevesinde değerlendirme yapılır.")
    
    if st.button("Karar Önerisi Al"):
        with st.spinner("🏢 ISS Karar Motoru kanunları tarayıp hüküm veriyor..."):
            prompt = f"""Sen bir uzman İnsan Kaynakları ve İş Hukuku yöneticisisin (İş Hukukçusu). 
            Elimizde aşağıdaki veriler var:
            
            Tutanak Özeti: {st.session_state.tutanak_summary}
            
            Çalışanın Savunması: {st.session_state.savunma_text}
            
            İlgili Yönetmelikler ve Kanunlar: {st.session_state.yonetmelik_text if st.session_state.yonetmelik_text else 'Belirtilmedi, genel İş Kanunu hükümlerini baz al.'}
            
            ÇOK ÖNEMLİ KURALLAR:
            1. Üreteceğin bu Nihai Karar Belgesi doğrudan resmi şablona basılacaktır. Bu yüzden BAŞLIK, LOGO, TARİH, İMZA, ADRES gibi antetli kağıt bilgilerini ASLA yazma. Sadece kararın ana metnini yaz.
            1.5. (ÇOK ÖNEMLİ) Kararını verirken KESİNLİKLE 'İlgili Yönetmelikler ve Kanunlar' bölümünde sana sağlanan (İş Kanunu, Sözleşme, Yönetmelik vb.) TÜM metinleri detaylıca incele ve cımbızlayarak alıntı yap. Hangi belgenin hangi maddesinin ihlal edildiğini açıkça belirterek dayanak göster.
            2. Görev: Çalışanın savunmasını, tutanak ile kıyaslayarak (varsa çelişkiler) analiz et.
            3. Görev: Savunmadaki gerekçelerin hukuki geçerliliğini değerlendir.
            4. Görev (DEEP RESEARCH): İlgili konuyu internette güncel Yargıtay İçtihatları ve emsal kararlar ışığında derinlemesine araştır. Hangi disiplin cezasının en uygun olduğuna karar ver. Kararını hukuki bir temele oturt ve araştırdığın güncel örnek Yargıtay içtihadı (Tarih, Esas ve Karar numaralarıyla birlikte) ile destekle. Kesinlikle güncel mevzuat.gov.tr standartlarını referans al ve ezbere hüküm kurma.
            5. (ÖNEMLİ) Farklı konulara veya alt bölümlere geçtiğinde araya 1 TAM SATIR (ENTER) BOŞLUK BIRAK ki yazılar iç içe geçmesin.
            """
            
            # Gemini Pro'yu zorla (Deep Research için en uygun olan)
            pro_model_name = 'gemini-1.5-pro'
            if hasattr(genai, 'list_models'):
                models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                if 'models/gemini-2.5-pro' in models:
                    pro_model_name = 'gemini-2.5-pro'
                elif 'models/gemini-1.5-pro' in models:
                    pro_model_name = 'gemini-1.5-pro'
                    
            model = genai.GenerativeModel(pro_model_name)
            response = safe_generate(model, prompt, enable_search=True)
            st.session_state.karar_sonucu = response.text
            
            if st.session_state.get('current_record_id'):
                hr_db.update_status(st.session_state.current_record_id, "Sonuçlandı")
            
    if st.session_state.karar_sonucu:
        st.subheader("Karar ve Gerekçesi")
        st.write(st.session_state.karar_sonucu)
        if st.button("Sonraki Adım: Karar Belgesi Hazırla"):
            st.session_state.step = 6
            st.rerun()

# ----------------- ADIM 6: KARAR ÇIKTISI -----------------
with st.expander("📄 6. Resmi Karar Çıktısı", expanded=(st.session_state.step == 6)):
    st.write("Verilen karara uygun nihai bildirim metni.")
    
    if st.session_state.karar_sonucu:
        if st.button("Nihai Belgeyi Oluştur"):
            with st.spinner("🏢 ISS Yapay Zeka resmi karar belgesini üretiyor..."):
                prompt = f"""Aşağıdaki karar önerisini baz alarak resmi bir "Disiplin Cezası Bildirimi" veya "İş Akdi Fesih Bildirimi" (SADECE GÖVDE METNİ) hazırla. 
                
                ÇOK ÖNEMLİ KURALLAR:
                1. Üreteceğin bu Nihai Bildirim Belgesi doğrudan resmi şablona basılacaktır. Bu yüzden BAŞLIK, LOGO, TARİH, İMZA, ADRES gibi antetli kağıt bilgilerini ASLA yazma. Sadece bildirimin ana metnini yaz.
                2. Kesinlikle Markdown formatı (**) veya madde işareti (-) KULLANMA. Düz metin paragrafları olarak üret.
                3. (ÇOK ÖNEMLİ) Karar özetinde geçen TÜM yasa maddelerini, "Şirket Personel Yönetmeliği Madde X", "İş Kanunu Madde Y" ve Yargıtay emsal kararlarını bildirim metninin içerisine KESİNLİKLE yedir. Çalışana, eyleminin tam olarak hangi kurumu kurallarını ve sözleşme maddesini ihlal ettiğini net olarak bildir.
                
                Karar Özeti: {st.session_state.karar_sonucu}
                """
                model = genai.GenerativeModel(st.session_state.active_model)
                response = safe_generate(model, prompt)
                st.session_state.nihai_belge = response.text
                
    if st.session_state.nihai_belge:
        st.text_area("Nihai Belge", st.session_state.nihai_belge, height=300)
        docx_file = create_docx(st.session_state.nihai_belge, "Nihai Karar Bildirimi")
        st.download_button("Word Olarak İndir (DOCX)", data=docx_file, file_name="nihai_karar_bildirimi.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# ----------------- ADIM 7: DOSYA TAKİBİ -----------------
with st.expander("📂 7. Dosya ve Süreç Takibi (Arşiv)", expanded=(st.session_state.step == 7)):
    st.write("Sistemdeki tüm disiplin dosyalarının güncel durumları.")
    
    records = hr_db.get_all_records()
    if not records:
        st.info("Henüz sisteme işlenmiş bir disiplin kaydı bulunmuyor.")
    else:
        for r in records:
            status = r['status']
            if status == "Tutanak Tutuldu":
                bg = "#F3F4F6"; text_color = "#4B5563"; border = "#E5E7EB"; icon = "📝"
            elif status == "Savunma Bekleniyor":
                bg = "#FFFBEB"; text_color = "#D97706"; border = "#FEF3C7"; icon = "⏳"
            elif status == "Savunma Alındı":
                bg = "#EFF6FF"; text_color = "#1D4ED8"; border = "#DBEAFE"; icon = "🛡️"
            else: # Sonuçlandı
                bg = "#ECFDF5"; text_color = "#065F46"; border = "#D1FAE5"; icon = "🟢"
                
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px 20px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div>
                    <div style="font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 4px;">{r['employee_name']}</div>
                    <div style="font-size: 13px; color: #6B7280;">{r['details']} • {r['file_number']}</div>
                </div>
                <div style="background-color: {bg}; color: {text_color}; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; border: 1px solid {border}; display: flex; align-items: center;">
                    <span style="font-size: 12px; margin-right: 6px;">{icon}</span> {status}
                </div>
            </div>
            """, unsafe_allow_html=True)
