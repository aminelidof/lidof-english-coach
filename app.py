import streamlit as st
import asyncio
import base64
from engine_ai import EliasBrain
from engine_audio import VoiceEngine
from streamlit_mic_recorder import mic_recorder

# --- 1. CONFIGURATION & GESTION DU THÈME ---
st.set_page_config(page_title="LIDOF English Coach", layout="wide", page_icon="🎓")

if "theme" not in st.session_state:
    st.session_state.theme = "Professional Blue"

themes = {
    "Professional Blue": {
        "bg": "#f0f2f6", "accent": "#003366", "card": "#ffffff", 
        "text": "#31333F", "border": "#003366", "sidebar": "#e0e4eb"
    },
    "Luxury Gold": {
        "bg": "#1a1a1a", "accent": "#d4af37", "card": "#2d2d2d", 
        "text": "#f1f1f1", "border": "#d4af37", "sidebar": "#111111"
    },
    "Dark Deep": {
        "bg": "#0e1117", "accent": "#3b82f6", "card": "#161b22", 
        "text": "#ffffff", "border": "#30363d", "sidebar": "#0e1117"
    }
}

def apply_theme(theme_name):
    t = themes[theme_name]
    st.markdown(f"""
        <style>
        /* Fond global */
        .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
        
        /* Sidebar responsive */
        [data-testid="stSidebar"] {{ background-color: {t['sidebar']}; border-right: 1px solid {t['border']}; }}

        /* Boîte d'entête adaptative */
        .header-box {{
            text-align: center; padding: 15px;
            background: {t['card']}; border-radius: 15px;
            border: 2px solid {t['border']}; margin-bottom: 20px;
        }}

        /* --- OPTIMISATION MOBILE (CSS Media Queries) --- */
        @media (max-width: 768px) {{
            .header-box h1 {{ font-size: 1.4rem !important; }}
            .contact-info {{ font-size: 0.75rem !important; }}
            /* Force les colonnes à s'empiler sur mobile */
            [data-testid="column"] {{ width: 100% !important; flex: 1 1 100% !important; }}
            .main-logo {{ width: 70px !important; margin: 0 auto; display: block; }}
        }}

        /* Harmonisation */
        h1, h2, h3, p, span, label {{ color: {t['text']} !important; }}
        .contact-info {{ color: {t['accent']}; font-weight: bold; }}
        button {{ border-color: {t['accent']} !important; width: 100%; }}
        </style>
    """, unsafe_allow_html=True)

apply_theme(st.session_state.theme)

# --- 2. INITIALISATION DES MOTEURS ---
if "brain" not in st.session_state:
    api_key = st.secrets.get("GROQ_KEY") or st.secrets.get("GROQ_API_KEY")
    if not api_key: 
        st.error("🔑 API Key manquante")
        st.stop()
    st.session_state.brain = EliasBrain(api_key)
    st.session_state.voice = VoiceEngine(api_key)
    st.session_state.chat_history = []
    st.session_state.performance_data = []
    st.session_state.audio_to_play = None
    st.session_state.last_audio_bytes = None

# --- 3. SIDEBAR (DASHBOARD) ---
with st.sidebar:
    st.title("🎓 Pro Dashboard")
    new_theme = st.selectbox("🎨 Thème Visuel", list(themes.keys()), 
                             index=list(themes.keys()).index(st.session_state.theme))
    
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.divider()
    level = st.select_slider("My Level", ["Beginner", "Intermediate", "Advanced"], "Intermediate")
    scenario = st.selectbox("Scenario", ["Free Talk", "Job Interview", "Business Meeting", "Travel"])
    
    st.divider()
    if st.session_state.performance_data:
        avg = sum(st.session_state.performance_data) / len(st.session_state.performance_data)
        st.metric("Global Accuracy", f"{int(avg)}%")
        st.progress(avg / 100)
    
    if st.button("🧹 Clear Session", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.performance_data = []
        st.session_state.last_analysis = None
        st.rerun()

# --- 4. ENTÊTE LIDOF (RESPONSIVE) ---
t_active = themes[st.session_state.theme]
# Utilisation de colonnes qui s'adaptent
h_col1, h_col2, h_col3 = st.columns([1, 4, 1])

with h_col1:
    st.image("FABLAB-modified.png", use_container_width=True)

with h_col2:
    st.markdown(f"""
        <div class="header-box">
            <h1 style="color: {t_active['accent']}; margin: 0;">LIDOF English Coach</h1>
            <div class="contact-info">
                📧 {st.secrets.get("MAIL", "m.fodil@cu-maghnia.dz")} <br class="mobile-only">| 📞 {st.secrets.get("TEL", "0550139987")}
            </div>
        </div>
    """, unsafe_allow_html=True)

with h_col3:
    st.image("CUM.png", use_container_width=True)

# --- 5. INTERFACE DE CHAT & ANALYSE ---
# Disposition 2:1 sur PC, Empilée sur Mobile
col_chat, col_ana = st.columns([2, 1])

with col_chat:
    container = st.container(height=450)
    for msg in st.session_state.chat_history:
        container.chat_message(msg["role"]).write(msg["content"])

with col_ana:
    st.subheader("🕵️ Analysis Monitor")
    if "last_analysis" in st.session_state and st.session_state.last_analysis:
        an = st.session_state.last_analysis['analysis']
        st.info(f"**Try this instead:**\n{an['corrected']}")
        st.warning(f"**Grammar Tip:**\n{an['rule']}")
        st.success(f"**Phrase Score:** {an['score']}%")
    else:
        st.info("Start speaking, I will analyze your English.")

# --- 6. GESTION AUDIO & MICRO ---
st.divider()
# Micro large sur mobile pour faciliter le clic
_, mic_col, _ = st.columns([1, 2, 1])
with mic_col:
    audio = mic_recorder(start_prompt="🎤 START COACHING", stop_prompt="🛑 STOP & SEND", key='recorder')

if audio and audio.get('bytes') != st.session_state.last_audio_bytes:
    st.session_state.last_audio_bytes = audio['bytes']
    with st.spinner("LIDOF AI is processing..."):
        user_text = st.session_state.voice.transcribe(audio['bytes'])
        if user_text:
            res = st.session_state.brain.process_interaction(user_text, st.session_state.chat_history, scenario, level)
            audio_b64 = asyncio.run(st.session_state.voice.generate_speech(res['reply']))
            st.session_state.audio_to_play = audio_b64
            st.session_state.chat_history.append({"role": "user", "content": user_text})
            st.session_state.chat_history.append({"role": "assistant", "content": res['reply']})
            st.session_state.last_analysis = res
            st.session_state.performance_data.append(res['analysis']['score'])
            st.rerun()

# --- 7. LECTURE AUDIO ---
if st.session_state.audio_to_play:
    st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{st.session_state.audio_to_play}">', unsafe_allow_html=True)
    st.session_state.audio_to_play = None
