import streamlit as st
import pandas as pd
import pickle
import requests
import random
import json
import urllib.parse
import streamlit.components.v1 as components

# --- Page Config ---
st.set_page_config(page_title="CinePulse", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_profile' not in st.session_state:
    st.session_state.current_profile = None
if 'my_list' not in st.session_state:
    st.session_state.my_list = []
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'movie_detail' not in st.session_state:
    st.session_state.movie_detail = None
if 'profiles' not in st.session_state:
    st.session_state.profiles = [
        {"name": "Harsh", "avatar": "https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png"},
        {"name": "Guest", "avatar": "https://mir-s3-cdn-cf.behance.net/project_modules/disp/84c20033850498.56ba69ac290ea.png"},
        {"name": "Kids", "avatar": "https://mir-s3-cdn-cf.behance.net/project_modules/disp/64623a33850498.56ba69ac2a6f7.png"},
    ]
if 'adding_profile' not in st.session_state:
    st.session_state.adding_profile = False
if 'editing_profile' not in st.session_state:
    st.session_state.editing_profile = False

# --- Custom CSS ---
def local_css():
    st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #fff; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #141414; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #555; }
    .navbar {
        position: fixed; top: 0; width: 100%;
        background: linear-gradient(to bottom, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 100%);
        padding: 20px 4%; z-index: 1000; display: flex;
        justify-content: space-between; align-items: center; transition: background-color 0.3s;
    }
    .nav-brand {
        color: #E50914; font-size: 2rem; font-weight: 700;
        text-decoration: none; cursor: pointer; user-select: none;
    }
    .nav-brand:hover { opacity: 0.85; }
    .profile-container { display: flex; justify-content: center; gap: 30px; margin-top: 50px; flex-wrap: wrap; }
    .profile-card { text-align: center; cursor: pointer; transition: transform 0.2s; }
    .profile-card:hover { transform: scale(1.1); }
    .profile-card img { width: 150px; height: 150px; border-radius: 10px; border: 2px solid transparent; }
    .profile-card:hover img { border-color: white; }
    .profile-name { margin-top: 10px; color: #808080; font-size: 1.2rem; }
    .profile-card:hover .profile-name { color: white; }
    .hero {
        position: relative; height: 60vh; width: 100%; background-size: cover;
        background-position: center top; margin-top: 10px;
        display: flex; align-items: flex-end; padding-bottom: 10vh; padding-left: 4%;
    }
    .hero-overlay {
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(to top, #141414 0%, transparent 60%),
                    linear-gradient(to right, rgba(0,0,0,0.8) 0%, transparent 50%);
    }
    .hero-content { position: relative; z-index: 2; max-width: 50%; }
    .hero-title { font-size: 4rem; font-weight: bold; margin-bottom: 1rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.45); }
    .hero-desc {
        font-size: 1.2rem; line-height: 1.4; margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.45);
        display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
    }
    .hero-buttons button {
        padding: 0.8rem 2rem; font-size: 1.2rem; font-weight: bold;
        border-radius: 4px; border: none; margin-right: 1rem; cursor: pointer; transition: opacity 0.2s;
    }
    .hero-buttons button:hover { opacity: 0.8; }
    .btn-play { background-color: white; color: black; }
    .btn-info { background-color: rgba(109, 109, 110, 0.7); color: white; }
    .row-title { color: #e5e5e5; font-size: 1.5rem; font-weight: 600; margin: 0 4% 10px 4%; }
    .row-container {
        display: flex; overflow-x: auto; overflow-y: hidden;
        padding: 20px 4%; gap: 10px; scroll-behavior: smooth;
    }
    .row-container::-webkit-scrollbar { display: none; }
    .movie-poster-card {
        flex: 0 0 auto; width: 200px; transition: transform 0.4s;
        border-radius: 4px; cursor: pointer; position: relative;
    }
    .movie-poster-card img { width: 100%; border-radius: 4px; object-fit: cover; }
    .movie-poster-card:hover { transform: scale(1.08); z-index: 10; }
    .movie-title-tooltip {
        position: absolute; bottom: 0; left: 0; right: 0;
        background: rgba(0,0,0,0.8); color: white; padding: 5px;
        font-size: 0.9rem; text-align: center; opacity: 0; transition: opacity 0.3s;
        border-bottom-left-radius: 4px; border-bottom-right-radius: 4px;
    }
    .movie-poster-card:hover .movie-title-tooltip { opacity: 1; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    .stTextInput>div>div>input { background-color: rgba(0,0,0,0.7); color: white; border: 1px solid white; }
    .stSelectbox div[data-baseweb="select"] { background-color: rgba(0,0,0,0.7); color: white; border: 1px solid white; }
    .search-wrapper { margin: 80px 4% 20px 4%; position: relative; z-index: 2000; display: flex; gap: 20px; }
    .rating-badge {
        display: inline-block; background-color: rgba(0,0,0,0.6);
        border: 1px solid #E50914; color: white; padding: 5px 10px;
        border-radius: 4px; font-weight: bold; margin-bottom: 1rem;
    }
    .rating-badge span { color: #FFD700; }
    .video-modal {
        display: none; position: fixed; z-index: 9999;
        left: 0; top: 0; width: 100%; height: 100%; overflow: auto;
        background-color: rgba(0,0,0,0.9);
    }
    .video-content { margin: 10% auto; padding: 20px; width: 80%; max-width: 800px; position: relative; }
    .close-video {
        color: white; float: right; font-size: 28px; font-weight: bold;
        cursor: pointer; position: absolute; top: -30px; right: 0;
    }
    .close-video:hover { color: #E50914; }

    /* ===== MOVIE DETAIL PAGE ===== */
    .detail-backdrop {
        position: relative; width: 100%; height: 72vh;
        background-size: cover; background-position: center top; overflow: hidden;
    }
    .detail-overlay {
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(to top, #141414 15%, rgba(20,20,20,0.5) 60%, rgba(20,20,20,0.1) 100%),
                    linear-gradient(to right, rgba(0,0,0,0.85) 0%, transparent 65%);
    }
    .detail-content-wrapper {
        position: absolute; bottom: 0; left: 0; right: 0;
        padding: 3% 4% 5% 4%; z-index: 10; display: flex; align-items: flex-end; gap: 28px;
    }
    .detail-poster-thumb {
        width: 145px; min-width: 145px; border-radius: 8px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.8); border: 2px solid rgba(255,255,255,0.15);
    }
    .detail-info { flex: 1; }
    .detail-title {
        font-size: 3.2rem; font-weight: bold; color: white;
        margin-bottom: 0.5rem; text-shadow: 2px 2px 6px rgba(0,0,0,0.5); line-height: 1.1;
    }
    .detail-meta {
        color: #ccc; font-size: 0.95rem; margin-bottom: 1rem;
        display: flex; gap: 12px; flex-wrap: wrap; align-items: center;
    }
    .meta-rating { color: #46d369; font-weight: bold; font-size: 1.1rem; }
    .meta-genre {
        background: rgba(255,255,255,0.15); padding: 3px 10px;
        border-radius: 20px; font-size: 0.8rem;
    }
    .detail-desc {
        font-size: 1rem; line-height: 1.65; color: #ddd; margin-bottom: 0;
        max-width: 600px; display: -webkit-box;
        -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden;
    }
    .section-title { color: #e5e5e5; font-size: 1.4rem; font-weight: 600; padding: 20px 4% 10px 4%; margin: 0; }
    .cast-row { display: flex; overflow-x: auto; padding: 10px 4% 20px 4%; gap: 15px; }
    .cast-row::-webkit-scrollbar { display: none; }
    .cast-card { flex: 0 0 auto; width: 110px; text-align: center; }
    .cast-card img {
        width: 100px; height: 100px; border-radius: 50%;
        object-fit: cover; border: 2px solid #333; display: block; margin: 0 auto;
    }
    .cast-name { font-size: 0.8rem; color: #ccc; margin-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .cast-char { font-size: 0.72rem; color: #888; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* ===== PROFILE PAGE ===== */
    .profiles-flex {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        gap: 32px;
        margin-top: 40px;
        flex-wrap: wrap;
        padding: 0 4%;
    }
    .profile-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 10px;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .profile-item:hover { transform: scale(1.08); }
    .profile-item img {
        width: 150px; height: 150px; border-radius: 10px;
        border: 2px solid transparent; object-fit: cover;
    }
    .profile-item:hover img { border-color: white; }
    .profile-item-name { color: #808080; font-size: 1.1rem; }
    .profile-item:hover .profile-item-name { color: white; }
    /* ===== ADD PROFILE ===== */
    .add-profile-icon {
        width: 150px; height: 150px; border-radius: 10px;
        background: rgba(255,255,255,0.07); border: 2px dashed rgba(255,255,255,0.4);
        display: flex; align-items: center; justify-content: center;
        font-size: 3rem; color: rgba(255,255,255,0.5); transition: all 0.2s;
        cursor: pointer; margin: 0 auto;
    }
    .add-profile-icon:hover { border-color: white; color: white; background: rgba(255,255,255,0.12); }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- Load Data ---
@st.cache_data
def load_data():
    movies_dict = pickle.load(open('movies_dict.pkl', 'rb'))
    movies = pd.DataFrame(movies_dict)
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    movie_genre = pickle.load(open('genre_map.pkl', 'rb'))
    return movies, similarity, movie_genre

movies, similarity, movie_genre = load_data()

# --- TMDB API ---
API_KEY = '14a28bbe51139037bdb77720e4e3f694'

@st.cache_data(ttl=3600)
def fetch_movie_details(movie_id):
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US&append_to_response=videos',
            timeout=5
        )
        data = response.json()
        poster = f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get('poster_path') else "https://via.placeholder.com/500x750/141414/ffffff?text=No+Poster"
        backdrop = f"https://image.tmdb.org/t/p/original{data['backdrop_path']}" if data.get('backdrop_path') else None
        overview = data.get('overview', 'No description available.')
        rating = round(data.get('vote_average', 0.0), 1)
        trailer_key = ""
        if 'videos' in data and 'results' in data['videos']:
            for video in data['videos']['results']:
                if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                    trailer_key = video['key']
                    break
        return poster, backdrop, overview, rating, trailer_key
    except Exception:
        return "https://via.placeholder.com/500x750/141414/ffffff?text=Error", None, "Error fetching details.", 0.0, ""

@st.cache_data(ttl=3600)
def fetch_movie_credits(movie_id):
    """Fetch cast, genres, year, runtime for detail page."""
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US&append_to_response=credits',
            timeout=5
        )
        data = response.json()
        cast = []
        if 'credits' in data and 'cast' in data['credits']:
            for c in data['credits']['cast'][:8]:
                cast.append({
                    'name': c['name'],
                    'character': c.get('character', ''),
                    'profile': f"https://image.tmdb.org/t/p/w185{c['profile_path']}" if c.get('profile_path') else None
                })
        genres = [g['name'] for g in data.get('genres', [])]
        year = data.get('release_date', '')[:4] if data.get('release_date') else 'N/A'
        runtime = data.get('runtime') or 0
        return cast, genres, year, runtime
    except Exception:
        return [], [], 'N/A', 0

# --- Helper Functions ---
def get_recommendations(movie_title):
    try:
        movie_index = movies[movies['title'] == movie_title].index[0]
        movies_list = similarity[movie_index]
        recs = []
        for i in movies_list:
            idx = i[0]
            m_id = movies.iloc[idx].movie_id
            m_title = movies.iloc[idx].title
            recs.append((m_title, m_id))
        return recs
    except Exception:
        return []

def get_genre_movies(genre, limit=15):
    if genre in movie_genre:
        indices = movie_genre[genre][:limit]
        return [(movies.iloc[idx].title, movies.iloc[idx].movie_id) for idx in indices]
    return []

# --- Render Components ---
@st.cache_data(ttl=3600)
def fetch_poster_only(movie_id):
    """Lightweight cached poster fetch using smaller image size."""
    try:
        response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US',
            timeout=5
        )
        data = response.json()
        if data.get('poster_path'):
            return f"https://image.tmdb.org/t/p/w342{data['poster_path']}"
        return "https://via.placeholder.com/342x513/141414/ffffff?text=No+Poster"
    except Exception:
        return "https://via.placeholder.com/342x513/141414/ffffff?text=Error"

def render_movie_row(title, movie_list):
    if not movie_list:
        return
    st.markdown(f"<div class='row-title'>{title}</div>", unsafe_allow_html=True)
    cards_html = ""
    for m_title, m_id in movie_list:
        poster = fetch_poster_only(int(m_id))
        encoded_title = urllib.parse.quote(m_title)
        # Use native <a href> for guaranteed navigation in Streamlit
        cards_html += f"""
        <a href="/?movie_detail={encoded_title}" style="text-decoration:none;" target="_self">
            <div class="movie-poster-card">
                <img src="{poster}" alt="{m_title}" loading="lazy"/>
                <div class="movie-title-tooltip">{m_title}</div>
            </div>
        </a>"""
    st.markdown(f'<div class="row-container">{cards_html}</div>', unsafe_allow_html=True)


# --- Movie Detail Page ---
def show_movie_detail_page():
    movie_title = st.session_state.movie_detail
    movie_row = movies[movies['title'] == movie_title]
    if movie_row.empty:
        st.session_state.movie_detail = None
        st.rerun()
        return

    movie_id = int(movie_row.iloc[0].movie_id)
    poster, backdrop, overview, rating, trailer_key = fetch_movie_details(movie_id)
    cast, genres, year, runtime = fetch_movie_credits(movie_id)

    bg_url = backdrop if backdrop else "https://via.placeholder.com/1920x1080/141414/333333?text=CinePulse"
    genres_html = "".join([f'<span class="meta-genre">{g}</span>' for g in genres])
    runtime_str = f"{runtime // 60}h {runtime % 60}m" if runtime and runtime > 0 else ""

    # Backdrop with overlay info
    st.markdown(f"""
<div class="detail-backdrop" style="background-image: url('{bg_url}');">
    <div class="detail-overlay"></div>
    <div class="detail-content-wrapper">
        <img class="detail-poster-thumb" src="{poster}" alt="{movie_title}" />
        <div class="detail-info">
            <div class="detail-title">{movie_title}</div>
            <div class="detail-meta">
                <span class="meta-rating">★ {rating}/10</span>
                {'<span>' + year + '</span>' if year != 'N/A' else ''}
                {'<span>' + runtime_str + '</span>' if runtime_str else ''}
                {genres_html}
            </div>
            <div class="detail-desc">{overview}</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

    # Trailer modal HTML (needs to be in DOM)
    st.markdown("""
<div id="trailerModal" class="video-modal">
    <div class="video-content">
        <span class="close-video" onclick="window.parent.document.closeTrailer()">&times;</span>
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
            <iframe id="trailerIframe" src="" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

    # Init trailer JS
    components.html(f"""<script>
    var pd = window.parent.document;
    pd.openTrailer = function(k) {{
        if (!k) {{ alert('Trailer unavailable.'); return; }}
        pd.getElementById('trailerModal').style.display = 'block';
        pd.getElementById('trailerIframe').src = 'https://www.youtube.com/embed/' + k;
    }};
    pd.closeTrailer = function() {{
        pd.getElementById('trailerModal').style.display = 'none';
        pd.getElementById('trailerIframe').src = '';
    }};
    </script>""", height=0)

    # Action buttons
    st.markdown("<div style='margin: 16px 4%;'>", unsafe_allow_html=True)
    b1, b2, b3, _ = st.columns([1, 1, 1, 7])
    with b1:
        if trailer_key:
            if st.button("▶  Trailer", key="detail_play"):
                components.html(f"<script>window.parent.document.openTrailer('{trailer_key}');</script>", height=0)
        else:
            st.button("▶  Trailer", key="detail_play_dis", disabled=True)
    with b2:
        in_list = movie_title in [m[0] for m in st.session_state.my_list]
        if in_list:
            if st.button("✓ In My List", key="detail_rm"):
                st.session_state.my_list = [m for m in st.session_state.my_list if m[0] != movie_title]
                st.rerun()
        else:
            if st.button("＋ My List", key="detail_add"):
                st.session_state.my_list.append((movie_title, movie_id))
                st.rerun()
    with b3:
        if st.button("← Back", key="detail_back"):
            st.session_state.movie_detail = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Cast
    if cast:
        st.markdown('<div class="section-title">Cast</div>', unsafe_allow_html=True)
        cast_cards = ""
        for member in cast:
            img = member['profile'] if member['profile'] else "https://via.placeholder.com/100x100/333/888?text=?"
            char = member['character'][:22] if member['character'] else ''
            cast_cards += f"""<div class="cast-card">
    <img src="{img}" alt="{member['name']}" />
    <div class="cast-name">{member['name']}</div>
    <div class="cast-char">{char}</div>
</div>"""
        st.markdown(f'<div class="cast-row">{cast_cards}</div>', unsafe_allow_html=True)

    # More Like This
    recs = get_recommendations(movie_title)
    if recs:
        render_movie_row("More Like This", recs[:12])

# --- Login Page ---
def login_page():
    st.markdown("<h1 style='text-align: center; color: #E50914; margin-top: 10vh; font-size: 3rem;'>CinePulse</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>Who's watching?</h2>", unsafe_allow_html=True)

    profiles = st.session_state.profiles

    # Use native <a href> links - most reliable way to navigate in Streamlit's HTML context
    cards_html = ""
    for i, profile in enumerate(profiles):
        cards_html += f"""
        <a href="/?login_profile={i}" style="text-decoration:none;" target="_self">
            <div class="profile-item">
                <img src="{profile['avatar']}" alt="{profile['name']}" />
                <div class="profile-item-name">{profile['name']}</div>
            </div>
        </a>"""

    # Add Profile card
    cards_html += """
        <a href="/?add_profile=1" style="text-decoration:none;" target="_self">
            <div class="profile-item">
                <div class="add-profile-icon">&#xFF0B;</div>
                <div class="profile-item-name">Add Profile</div>
            </div>
        </a>"""

    st.markdown(f'<div class="profiles-flex">{cards_html}</div>', unsafe_allow_html=True)

    # Add Profile Form (shown when ?add_profile=1 is in URL, handled in routing)
    if st.session_state.adding_profile:
        st.markdown("<hr style='border-color:#333; margin: 30px 10%;'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: white;'>Create New Profile</h3>", unsafe_allow_html=True)
        _, form_col, _ = st.columns([3, 4, 3])
        with form_col:
            new_name = st.text_input("Profile Name:", key="new_profile_name_input", placeholder="Enter name...")
            avatar_options = {
                "Blue": "https://upload.wikimedia.org/wikipedia/commons/0/0b/Netflix-avatar.png",
                "Red": "https://mir-s3-cdn-cf.behance.net/project_modules/disp/84c20033850498.56ba69ac290ea.png",
                "Purple": "https://mir-s3-cdn-cf.behance.net/project_modules/disp/64623a33850498.56ba69ac2a6f7.png",
                "Green": "https://i.pravatar.cc/150?img=12",
                "Orange": "https://i.pravatar.cc/150?img=35",
            }
            chosen_color = st.selectbox("Choose Avatar:", list(avatar_options.keys()), key="avatar_select")
            chosen_avatar = avatar_options[chosen_color]
            st.image(chosen_avatar, width=80)
            sc, cc = st.columns(2)
            with sc:
                if st.button("✓ Create", key="btn_create_profile", use_container_width=True):
                    if new_name.strip():
                        st.session_state.profiles.append({"name": new_name.strip(), "avatar": chosen_avatar})
                        st.session_state.adding_profile = False
                        st.rerun()
                    else:
                        st.error("Please enter a name.")
            with cc:
                if st.button("✕ Cancel", key="btn_cancel_profile", use_container_width=True):
                    st.session_state.adding_profile = False
                    st.rerun()

# --- Main App ---
def main_app():
    # Handle query parameters
    query_params = st.query_params



    # Navbar — CinePulse brand links to /?home=1 which routing handles WITHOUT resetting session
    st.markdown(f"""
    <div class="navbar">
        <a href="/?home=1" style="text-decoration:none;" target="_self">
            <div class="nav-brand">CinePulse</div>
        </a>
        <div style="color: white; font-size: 1.2rem; display: flex; align-items: center; gap: 15px;">
            <span>Profile: {st.session_state.current_profile}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Search / Genre controls
    st.markdown("<div class='search-wrapper'>", unsafe_allow_html=True)
    search_col, genre_col, profile_col, logout_col = st.columns([3, 2, 1, 1])
    with search_col:
        selected_movie = st.selectbox('Search for a movie...', [''] + list(movies['title'].values), key="search_movie_dropdown")
    with genre_col:
        selected_genre = st.selectbox('Filter by Genre', ['None'] + sorted(movie_genre.keys()))
    with profile_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Edit Profile", use_container_width=True):
            st.session_state.editing_profile = True
            st.rerun()
    with logout_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Edit Profile Panel
    if st.session_state.get("editing_profile", False):
        st.markdown("<div style='margin: 0 4% 30px 4%; padding: 20px; background: rgba(0,0,0,0.6); border: 1px solid #333; border-radius: 8px;'>", unsafe_allow_html=True)
        st.text_input("New Profile Name:", value=st.session_state.current_profile, key="new_profile_name")
        col1, col2, _ = st.columns([1, 1, 8])
        with col1:
            if st.button("Save"):
                st.session_state.current_profile = st.session_state.new_profile_name
                st.session_state.editing_profile = False
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.editing_profile = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    is_home = (selected_movie == '' and selected_genre == 'None')

    # ---- HOME PAGE: show rotating hero + ALL genre rows ----
    if is_home:
        top_5 = get_genre_movies('Action', 5)
        featured_movies_data = []
        for m_title, m_id in top_5:
            _, f_bg, f_desc, f_rating, f_trailer = fetch_movie_details(m_id)
            featured_movies_data.append({
                "title": m_title,
                "id": int(m_id),
                "bg": f_bg if f_bg else "https://via.placeholder.com/1920x1080/141414/333333?text=CinePulse",
                "desc": f_desc,
                "rating": f_rating,
                "trailer": f_trailer
            })

        if featured_movies_data:
            movies_json = json.dumps(featured_movies_data)
            first_m = featured_movies_data[0]

            js_code = f"""
<script>
    var parentDoc = window.parent.document;
    if (!parentDoc.heroScriptLoaded) {{
        parentDoc.heroScriptLoaded = true;
        parentDoc.openTrailer = function(trailerKey) {{
            if (!trailerKey) {{ alert('Trailer currently unavailable for this title.'); return; }}
            parentDoc.getElementById('trailerModal').style.display = 'block';
            parentDoc.getElementById('trailerIframe').src = 'https://www.youtube.com/embed/' + trailerKey;
        }};
        parentDoc.closeTrailer = function() {{
            parentDoc.getElementById('trailerModal').style.display = 'none';
            parentDoc.getElementById('trailerIframe').src = '';
        }};
        parentDoc.rotatingMovies = {movies_json};
        parentDoc.currentIdx = 0;
        parentDoc.rotateHero = function() {{
            if (parentDoc.rotatingMovies.length <= 1) return;
            parentDoc.currentIdx = (parentDoc.currentIdx + 1) % parentDoc.rotatingMovies.length;
            var m = parentDoc.rotatingMovies[parentDoc.currentIdx];
            var hBanner = parentDoc.getElementById('hero-banner');
            if (hBanner) hBanner.style.backgroundImage = "url('" + m.bg + "')";
            var hTitle = parentDoc.getElementById('hero-title');
            if (hTitle) hTitle.innerText = m.title;
            var hDesc = parentDoc.getElementById('hero-desc');
            if (hDesc) hDesc.innerText = m.desc;
            var hRating = parentDoc.getElementById('hero-rating');
            if (hRating) hRating.innerText = '★ ' + m.rating + '/10';
            var bPlay = parentDoc.getElementById('btn-play-hero');
            if (bPlay) bPlay.setAttribute('onclick', "window.parent.document.openTrailer('" + m.trailer + "')");
        }};
        if (parentDoc.rotatingMovies.length > 1) {{ setInterval(parentDoc.rotateHero, 3000); }}
    }}
</script>"""
            components.html(js_code, height=0, width=0)

            st.markdown(f"""
<div id="trailerModal" class="video-modal">
    <div class="video-content">
        <span class="close-video" onclick="window.parent.document.closeTrailer()">&times;</span>
        <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
            <iframe id="trailerIframe" src="" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
                frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

            st.markdown(f"""
<div id="hero-banner" class="hero" style="background-image: url('{first_m['bg']}'); transition: background-image 1s ease-in-out;">
    <div class="hero-overlay"></div>
    <div class="hero-content">
        <div id="hero-title" class="hero-title">{first_m['title']}</div>
        <div class="rating-badge">TMDB Rating: <span id="hero-rating">★ {first_m['rating']}/10</span></div>
        <div id="hero-desc" class="hero-desc">{first_m['desc']}</div>
        <div class="hero-buttons">
            <button id="btn-play-hero" class="btn-play" onclick="window.parent.document.openTrailer('{first_m['trailer']}')">▶ Play Trailer</button>
            <button class="btn-info">☆ Rate Movie</button>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

        # Default genre rows — shown on home
        st.markdown("<div style='margin-top: -50px; position: relative; z-index: 10;'>", unsafe_allow_html=True)
        if st.session_state.my_list:
            render_movie_row("⭐ My List", st.session_state.my_list)
        render_movie_row("🔥 Trending Now (Action)", get_genre_movies('Action', 15))
        render_movie_row("🚀 Sci-Fi Masterpieces", get_genre_movies('Science Fiction', 15))
        render_movie_row("🎭 Critically Acclaimed Dramas", get_genre_movies('Drama', 15))
        render_movie_row("😂 Comedy Hits", get_genre_movies('Comedy', 15))
        render_movie_row("👻 Thriller & Horror", get_genre_movies('Thriller', 15))
        render_movie_row("🎬 Animated Wonders", get_genre_movies('Animation', 15))
        render_movie_row("❤️ Romance", get_genre_movies('Romance', 15))
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- SEARCH / GENRE: show ONLY poster rows, NO hero ----
    else:
        st.markdown("<div style='margin-top: 30px; position: relative; z-index: 10;'>", unsafe_allow_html=True)

        if selected_movie != '':
            recs = get_recommendations(selected_movie)
            render_movie_row(f"🔍 Results for: {selected_movie}", recs)

        if selected_genre != 'None':
            g_movies = get_genre_movies(selected_genre, 30)
            render_movie_row(f"🎬 Top Picks in {selected_genre}", g_movies)

        if st.session_state.my_list:
            render_movie_row("⭐ My List", st.session_state.my_list)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; color: #555; padding: 50px;'>CinePulse Recommender © 2026</div>", unsafe_allow_html=True)


# --- Routing ---
_qp = st.query_params

# CinePulse logo click: go home, clear movie_detail, preserve login session
if "home" in _qp:
    st.query_params.clear()
    st.session_state.movie_detail = None
    if "search_movie_dropdown" in st.session_state:
        st.session_state.search_movie_dropdown = ""
    st.rerun()

# Handle profile selection via URL (profile image click sets ?login_profile=INDEX)
if "login_profile" in _qp:
    try:
        _idx = int(_qp["login_profile"])
        if 0 <= _idx < len(st.session_state.profiles):
            st.session_state.logged_in = True
            st.session_state.current_profile = st.session_state.profiles[_idx]["name"]
    except (ValueError, IndexError):
        pass
    st.query_params.clear()
    st.rerun()

# Handle Add Profile click via URL
if "add_profile" in _qp:
    st.query_params.clear()
    st.session_state.adding_profile = True
    st.rerun()

if "movie_detail" in _qp:
    _val = urllib.parse.unquote(_qp["movie_detail"])
    if _val in movies["title"].values:
        # Auto-login as first profile if visiting a movie detail link while not logged in
        if not st.session_state.logged_in:
            st.session_state.logged_in = True
            st.session_state.current_profile = st.session_state.profiles[0]["name"]
        st.session_state.movie_detail = _val
        st.query_params.clear()
        st.rerun()

if "reset" in _qp:
    st.query_params.clear()
    st.session_state.movie_detail = None
    if "search_movie_dropdown" in st.session_state:
        st.session_state.search_movie_dropdown = ""
    st.rerun()

if not st.session_state.logged_in:
    login_page()
elif st.session_state.movie_detail:
    show_movie_detail_page()
else:
    main_app()