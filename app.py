import streamlit as st
import requests
import json
import io
import re
from docx import Document

# --- 1. KONFIGURASI UTAMA STREAMLIT ---
st.set_page_config(
    page_title="DeepSeek V4 Flash Shared Workspace",
    page_icon="⚡",
    layout="wide"
)

# --- 2. FUNGSI UNTUK MEMBUAT FILE WORD (.DOCX) DENGAN FORMAT BENAR ---
def buat_file_word(riwayat_pesan):
    doc = Document()
    doc.add_heading('Draf Hasil Kerja AI - DeepSeek V4 Flash Workspace', level=0)
    
    for msg in riwayat_pesan:
        if msg["role"] == "system":
            continue
            
        if msg["role"] == "user":
            doc.add_heading("Pertanyaan / Instruksi Anda:", level=2)
            if isinstance(msg["content"], str) and "Lanjutkan penjelasan" not in msg["content"]:
                doc.add_paragraph(msg["content"])
                    
        elif msg["role"] == "assistant":
            doc.add_heading("Jawaban AI:", level=2)
            
            paragraf_list = msg["content"].split('\n')
            for p_text in paragraf_list:
                if not p_text.strip():
                    continue
                
                match_heading = re.match(r'^(#{1,6})\s+(.*)$', p_text.strip())
                if match_heading:
                    level_pagar = len(match_heading.group(1))
                    teks_judul = match_heading.group(2)
                    teks_judul_bersih = teks_judul.replace('**', '')
                    level_word = min(level_pagar, 3) 
                    doc.add_heading(teks_judul_bersih, level=level_word)
                    continue
                
                p = doc.add_paragraph()
                parts = re.split(r'(\*\*.*?\*\*)', p_text)
                for part in parts:
                    if part.startswith('**') and part.endswith('**'):
                        clean_text = part.replace('**', '')
                        p.add_run(clean_text).bold = True
                    else:
                        p.add_run(part)
                        
            p_line = doc.add_paragraph()
            p_line.add_run("_" * 40).italic = True
            
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 3. PANEL CONTROL SIDEBAR ---
with st.sidebar:
    st.title("⚡ Kontrol AI")
    st.info("⚡ Status Server: Terhubung Otomatis (DeepSeek V4 Flash Active)")
    
    st.divider()
    st.markdown("### 📥 Ekspor Dokumen")
    if "messages" in st.session_state and len(st.session_state.messages) > 1:
        file_word = buat_file_word(st.session_state.messages)
        st.download_button(
            label="📥 Download Jadi Word (.docx)",
            data=file_word,
            file_name="Draf_LagosAi_DeepSeek_Flash.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        st.info("Mulai obrolan terlebih dahulu untuk mengunduh berkas Word.")
            
    st.divider()
    if st.button("🗑️ Reset & Bersihkan Semua Memori"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 4. KONFIGURASI DEEPSEEK V4 FLASH NVIDIA ---
API_URL = "https://nvidia.com"
nvidia_api_key = "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"
MODEL_NAME = "deepseek-ai/deepseek-v4-flash"

# --- 5. MANAJEMEN MEMORI CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Anda adalah DeepSeek V4 Flash, model bahasa besar super cepat dari DeepSeek yang di-host di infrastruktur NVIDIA NIM. Jawab dalam Bahasa Indonesia secara terstruktur, cerdas, mendalam, dan natural."}
    ]

# --- 6. TAMPILAN UTAMA INTERFASE CHAT ---
st.title("🔮 Lagos AI 7.3 (DeepSeek V4 Flash)")
st.caption("Workspace ditenagai oleh model deepseek-ai/deepseek-v4-flash melalui NVIDIA API.")

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if len(st.session_state.messages) > 1 and st.session_state.messages[-1]["role"] == "assistant":
    col1, col2 = st.columns()
    with col1:
        if st.button("📝 Lanjutkan Tulisan Ini", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Lanjutkan penjelasan tulisan Anda sebelumnya secara mengalir tanpa terputus."})
            st.rerun()

# --- 7. PROSES INPUT & RESPONS CHAT VIA NATIVE HTTP REQUESTS ---
user_input = st.chat_input("Ketik perintah teks Anda di sini...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        try:
            # Membuat headers autentikasi API NVIDIA
            headers = {
                "Authorization": f"Bearer {nvidia_api_key}",
                "Content-Type": "application/json"
            }
            
            # CRITICAL FIX: Menyuntikkan parameter khusus untuk server NIM DeepSeek V4
            payload = {
                "model": MODEL_NAME,
                "messages": st.session_state.messages,
                "temperature": 0.3,
                "max_tokens": 2048,
                "stream": True,
                "chat_template_kwargs": {
                    "enable_thinking": True,
                    "thinking": True
                }
            }
            
            # Melakukan request POST dengan mode streaming aktif
            response = requests.post(API_URL, headers=headers, json=payload, stream=True)
            
            # Validasi jika server mengembalikan error HTML atau kode HTTP selain 200
            if response.status_code != 200:
                st.error(f"Server NVIDIA merespons dengan Error {response.status_code}. Silakan periksa kembali kuota atau status API Key Anda.")
                st.code(response.text[:500], language="html")
            else:
                def teks_generator_native():
                    for line in response.iter_lines():
                        if line:
                            # Mengonversi baris byte mentah menjadi teks string
                            decoded_line = line.decode('utf-8').strip()
                            if decoded_line.startswith("data: "):
                                data_str = decoded_line[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    data_json = json.loads(data_str)
                                    content = data_json['choices'][0]['delta'].get('content', '')
                                    if content:
                                        yield content
                                except:
                                    pass

                full_response = st.write_stream(teks_generator_native())
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()
            
        except Exception as e:
            st.error(f"Gagal memproses teks. Detail: {e}")
            
