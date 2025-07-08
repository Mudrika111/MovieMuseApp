import streamlit as st
import pickle
import requests
import os
import random
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background: linear-gradient(to bottom right, #cdeffd, #eaf6ff);
        color: #002244;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #003366;
    }

    /* Text content */
    .css-1v0mbdj p, .stText, .stMarkdown, .stCaption {
        color: #00334d !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #d4ecfa;
        padding: 20px;
        border-right: 2px solid #aacbe3;
    }

    /* Sidebar text */
    .sidebar-content, .css-1d391kg {
        color: #003366 !important;
    }

    /* Buttons */
    button {
        background-color: #007acc !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 8px 16px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    button:hover {
        background-color: #005fa3 !important;
    }

    /* Select box + number input */
    .stNumberInput input, .stSelectbox div {
        background-color: #ffffff !important;
        color: #003366 !important;
        border-radius: 8px;
    }

    /* Images */
    img {
        border-radius: 16px;
        transition: transform 0.2s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }

    img:hover {
        transform: scale(1.02);
    }

    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #e3f3ff;
    }

    ::-webkit-scrollbar-thumb {
        background: #aacbe3;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #7ab4e3;
    }
    </style>
""", unsafe_allow_html=True)

# State control for front screens
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

# Welcome Page
if st.session_state.page == 'welcome':
    st.markdown("<h1 style='text-align: center;'>🎥 Welcome to <span style='color:#ec407a;'>MovieMuse</span>!</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; font-size: 20px; padding: 10px; line-height: 1.8;'>
    🎬 <strong>Welcome to MovieMuse</strong> — your cozy corner for finding what to watch next!  
    <br><br>
    🍿 Tired of endless scrolling through movie lists?  
    💡 Want smart, personal suggestions that actually match your vibe?  
    🌈 Let MovieMuse help you discover hidden gems and fan favorites — in seconds.  
    <br><br>
    <span style='color:#1565c0; font-weight:bold;'>Ready to dive in?</span>
</div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if st.button("🌈 Start Now"):
        st.session_state.page = 'age'
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Age Selection Page
if st.session_state.page == 'age':
    st.markdown("<h1 style='text-align: center;'>🎂 Just One Step...</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; font-size: 18px;'>
        To personalize your MovieMuse experience,  
        choose your age group below 👇
    </div><br>
    """, unsafe_allow_html=True)

    age_options = {
        "Under 13": 12,
        "13–17": 15,
        "18–25": 21,
        "26–40": 30,
        "Above 40": 50
    }

    age_group = st.selectbox("🎯 Choose your age group:", list(age_options.keys()))
    if st.button("🚀 Enter MovieMuse"):
        st.session_state.age = age_options[age_group]
        st.session_state.page = 'main'
    st.stop()

# Fetch movie poster and details
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=c7ec19ffdd3279641fb606d19ceb9bb1&language=en-US"
    data = requests.get(url).json()

    # Hide adult movies for underage users
    if data.get("adult", False) and st.session_state.age < 18:
        return None

    poster_path = data.get('poster_path')
    poster = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None

    return {
        "poster": poster,
        "overview": data.get("overview", "Overview not available"),
        "rating": data.get("vote_average", "N/A"),
        "release_date": data.get("release_date", "N/A"),
        "genres": ', '.join([genre['name'] for genre in data.get('genres', [])]),
    }

# Fetch trending movies
@st.cache_data
def fetch_trending():
    url = "https://api.themoviedb.org/3/trending/movie/week?api_key=c7ec19ffdd3279641fb606d19ceb9bb1"
    data = requests.get(url).json()

    trending_movies = []
    for movie in data['results'][:10]:
        if movie.get("adult", False) and st.session_state.age < 18:
            continue
        trending_movies.append({
            "title": movie['title'],
            "poster": f"https://image.tmdb.org/t/p/w500/{movie['poster_path']}" if movie.get('poster_path') else None,
            "rating": movie.get('vote_average', "N/A"),
        })
    return trending_movies

# Load pickle files
movies_file = "movies_list.pkl"
similarity_file = "similarity.pkl"

if os.path.exists(movies_file) and os.path.exists(similarity_file):
    movies = pickle.load(open(movies_file, 'rb'))
    similarity = pickle.load(open(similarity_file, 'rb'))
else:
    st.error("Pickle files not found. Please check the file paths.")
    st.stop()

# UI: Title and Age
st.title("🎥 MovieMuse")
# Movie selection
movies_list = movies['title'].values
movie_to_recommend = st.selectbox("🔍 Select or Search a movie to get recommendations", movies_list)

# Recommendation logic
def recommend(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda vector: vector[1])

        recommendations = []
        for i in distances[1:]:
            movie_id = movies.iloc[i[0]].id
            details = fetch_movie_details(movie_id)
            if details:
                recommendations.append({
                    "title": movies.iloc[i[0]].title,
                    "poster": details["poster"],
                    "rating": details["rating"],
                    "release_date": details["release_date"],
                    "overview": details["overview"],
                    "genres": details["genres"]
                })
            if len(recommendations) == 5:
                break
        return recommendations
    except IndexError:
        st.error("Movie not found. Please check the spelling or select from the dropdown.")
        return []

# Button states
if 'show_recommendations' not in st.session_state:
    st.session_state.show_recommendations = True
if 'feeling_lucky' not in st.session_state:
    st.session_state.feeling_lucky = False

# Buttons
if st.button("Show Recommendations"):
    st.session_state.show_recommendations = True
    st.session_state.feeling_lucky = False

if st.button("🎲 Feeling Lucky"):
    st.session_state.show_recommendations = False
    st.session_state.feeling_lucky = True

# Show recommendations side-by-side
if st.session_state.show_recommendations:
    recommendations = recommend(movie_to_recommend)
    if recommendations:
        cols = st.columns(2)
        for idx, movie in enumerate(recommendations):
            with cols[idx % 2]:
                st.subheader(movie['title'])
                if movie['poster']:
                    st.image(movie['poster'], width=200)
                st.text(f"⭐ Rating: {movie['rating']}")
                st.text(f"📅 Release: {movie['release_date']}")
                st.text(f"🎭 Genres: {movie['genres']}")
                st.caption(movie['overview'])
                st.markdown("---")
    else:
        st.warning("No recommendations available.")

# Show 2 random movies in "Feeling Lucky"
if st.session_state.feeling_lucky:
    shown = 0
    attempts = 0
    cols = st.columns(2)

    while shown < 2 and attempts < 15:
        idx = random.randint(0, len(movies) - 1)
        title = movies.iloc[idx].title
        movie_id = movies.iloc[idx].id
        details = fetch_movie_details(movie_id)

        if details:
            with cols[shown % 2]:
                st.subheader(f"🎉 You might like: {title}")
                if details['poster']:
                    st.image(details['poster'], width=250)
                st.text(f"⭐ Rating: {details['rating']}")
                st.text(f"📅 Release: {details['release_date']}")
                st.text(f"🎭 Genres: {details['genres']}")
                st.caption(details['overview'])
            shown += 1
        attempts += 1

# Sidebar: Trending movies
st.sidebar.header("🔥 Trending Movies This Week")
trending_movies = fetch_trending()
for movie in trending_movies:
    st.sidebar.text(movie['title'])
    if movie['poster']:
        st.sidebar.image(movie['poster'], width=250)
    st.sidebar.text(f"⭐ Rating: {movie['rating']}")
