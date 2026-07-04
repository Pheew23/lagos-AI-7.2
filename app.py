import streamlit as st
import requests
import json
import io
import re
from docx import Document

# --- 1. KONFIGURASI UTAMA STREAMLIT ---
st.set_page_config(
    page_title="MiniMax M3 Shared Workspace",
    page_icon="⚡",
    layout="wide"
)

# --- 2. FUNGSI UNTUK MEMBUAT FILE WORD (.DOCX) DENGAN FORMAT BENAR ---
def buat_file_word(riwayat_pesan):
    doc = Document()
    doc.add_heading('Draf Hasil Kerja AI - MiniMax M3 Workspace', level=0)
    
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
    st.info("⚡ Status Server: Terhubung Otomatis (MiniMax M3 Active)")
    
    st.divider()
    st.markdown("### 📥 Ekspor Dokumen")
    if "messages" in st.session_state and len(st.session_state.messages) > 1:
        file_word = buat_file_word(st.session_state.messages)
        st.download_button(
            label="📥 Download Jadi Word (.docx)",
            data=file_word,
            file_name="Draf_LagosAi_MiniMaxM3.docx",
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

# --- 4. KONFIGURASI INTERFACE MINIMAX M3 NVIDIA ---
API_URL = "https://nvidia.com"
nvidia_api_key = "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"
MODEL_NAME = "minimaxai/minimax-m3"

# --- 5. MANAJEMEN MEMORI CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Anda adalah MiniMax M3, model bahasa canggih dari MiniMax yang di-host di infrastruktur NVIDIA NIM. Jawab dalam Bahasa Indonesia secara terstruktur, cerdas, mendalam, dan natural."}
    ]

# --- 6. TAMPILAN UTAMA INTERFASE CHAT ---
st.title("🔮 Lagos AI 7.6 (MiniMax M3)")
st.caption("Workspace ditenagai oleh model minimaxai/minimax-m3 melalui arsitektur Native Stream Gateway.")

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if len(st.session_state.messages) > 1 and st.session_state.messages[-1]["role"] == "assistant":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Lanjutkan Tulisan Ini", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Lanjutkan penjelasan tulisan Anda sebelumnya secara mengalir tanpa terputus."})
            st.rerun()

# --- 7. PROSES INPUT & RESPONS CHAT VIA NATIVE STREAM PARSING ---
user_input = st.chat_input("Ketik perintah teks Anda di sini...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        try:
            headers = {
                "Authorization": f"Bearer {nvidia_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": MODEL_NAME,
                "messages": st.session_state.messages,
                "temperature": 0.2,
                "max_tokens": 2048,
                "stream": True
            }
            
            response = requests.post(API_URL, headers=headers, json=payload, stream=True)
            
            if response.status_code != 200:
                st.error(f"Server NVIDIA NIM Menolak Akses (Status {response.status_code}).")
                st.code(response.text[:400], language="html")
            else:
                def teks_generator_minimax_fixed():
                    for line in response.iter_lines():
                        if not line:
                            continue
                        
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith("data:"):
                            data_str = decoded_line[5:].strip()
                            
                            if data_str == "[DONE]":
                                break
                                
                            try:
                                data_json = json.loads(data_str)
                                choices = data_json.get('choices', [])
                                if choices:
                                    delta = choices[0].get('delta', {})
                                    
                                    # --- KOREKSI KRITIKAL: Fallback pencarian teks multifield ---
                                    content = delta.get('content', '')
                                    text_alt = delta.get('text', '') # Struktur alternatif tangkapan MoE MiniMax
                                    
                                    if content:
                                        yield content
                                    elif text_alt:
                                        yield text_alt
                            except Exception:
                                pass

                full_response = st.write_stream(teks_generator_minimax_fixed())
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()
            
        except Exception as e:
            st.error(f"Gagal memproses respons. Detail: {e}")
