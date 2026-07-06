import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# ============================================
# KONFIGURASI HALAMAN STREAMLIT
# ============================================
st.set_page_config(
    page_title="Gemini AI Clone",
    page_icon="✨",
    layout="wide"
)

# ============================================
# INISIALISASI SESSION STATE (Riwayat Chat)
# ============================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# ============================================
# SIDEBAR UNTUK API KEY
# ============================================
with st.sidebar:
    st.title("⚙️ Konfigurasi")
    api_key = st.text_input("Masukkan Google API Key:", type="password")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Menggunakan model gemini-1.5-flash (Cepat & Multimodal)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Mulai sesi chat jika belum ada
            if st.session_state.chat_session is None:
                st.session_state.chat_session = model.start_chat(history=[])
                
            st.success("API Key berhasil dimuat!")
            
            if st.button("🗑️ Hapus Riwayat Chat"):
                st.session_state.messages = []
                st.session_state.chat_session = model.start_chat(history=[])
                st.rerun()
        except Exception as e:
            st.error(f"Error konfigurasi API: {e}")
    else:
        st.warning("Silakan masukkan API Key untuk memulai.")
        st.markdown("Dapatkan API Key gratis di [Google AI Studio](https://aistudio.google.com/app/apikey)")

# ============================================
# TAMPILAN UTAMA
# ============================================
st.title("✨ Gemini AI Clone")
st.caption("Sebuah klon AI mirip Gemini menggunakan Streamlit & Google API")

# Tampilkan riwayat chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("image"):
            st.image(message["image"], width=300)
        st.markdown(message["content"])

# ============================================
# INPUT UPLOAD GAMBAR
# ============================================
uploaded_file = st.file_uploader("Unggah gambar (opsional)", type=["jpg", "jpeg", "png"])

# Menyimpan gambar sementara untuk ditampilkan di chat
if uploaded_file is not None:
    img = Image.open(uploaded_file)
    # Simpan gambar ke session state sementara untuk dikirim
    st.session_state.temp_image = img
else:
    st.session_state.temp_image = None

# ============================================
# INPUT CHAT PROMPT
# ============================================
if prompt := st.chat_input("Ketik pesan Anda atau tanyakan tentang gambar..."):
    if not api_key:
        st.warning("Masukkan API Key di sidebar terlebih dahulu!")
    else:
        # Tampilkan pesan user di layar
        with st.chat_message("user"):
            if st.session_state.temp_image:
                st.image(st.session_state.temp_image, width=300)
            st.markdown(prompt)
        
        # Simpan ke riwayat
        st.session_state.messages.append({
            "role": "user", 
            "content": prompt,
            "image": st.session_state.temp_image if st.session_state.temp_image else None
        })

        # ============================================
        # PROSES BALASAN AI
        # ============================================
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Gabungkan prompt teks dengan gambar jika ada
                if st.session_state.temp_image:
                    prompt_parts = [st.session_state.temp_image, prompt]
                else:
                    prompt_parts = [prompt]

                # Kirim ke Gemini API
                response = st.session_state.chat_session.send_message(prompt_parts, stream=True)
                
                # Efek mengetik (Streaming)
                for chunk in response:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                    
                message_placeholder.markdown(full_response)
                
                # Simpan balasan AI ke riwayat
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response,
                    "image": None
                })
                
                # Hapus gambar sementara setelah dikirim
                st.session_state.temp_image = None
                uploaded_file = None
                
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memuat balasan: {e}")
                
