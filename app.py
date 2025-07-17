import streamlit as st
import openai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import base64

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(image_file):
    bin_str = get_base64_of_bin_file(image_file)
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_background('headset_bg.jpg')

# Load environment variables
def load_api_keys():
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=st.secrets["SPOTIPY_CLIENT_ID"],
        client_secret=st.secrets["SPOTIPY_CLIENT_SECRET"]
    ))
    return openai.api_key, st.secrets["SPOTIPY_CLIENT_ID"], st.secrets["SPOTIPY_CLIENT_SECRET"]

# Setup OpenAI client
def setup_openai(api_key):
    return openai.OpenAI(api_key=api_key)

# Setup Spotify client
def setup_spotify(client_id, client_secret):
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    ))

# Streamlit UI setup
def setup_ui():
    st.set_page_config(page_title="MoodMate", page_icon="🎧")
    st.title("🎧 MoodMate")
    st.markdown("Tell me how you're feeling, and I’ll play the right vibe.")
    return st.text_input("What's your mood right now?", placeholder="e.g., I'm feeling low today")

# GPT prompt for mood classification
def get_music_mood(client, user_input):
    system_prompt = f"""
    You are a helpful assistant that classifies a user's emotional tone and suggests a music mood or genre.

    Examples:
    Input: I'm feeling energetic and ready to take on the world!
    Output: Mood: Excited
    Music: High-tempo Pop, EDM

    Input: I had a really rough day and feel emotionally exhausted.
    Output: Mood: Drained
    Music: Calm Piano, Lo-fi Chill, Acoustic

    Input: I'm feeling nostalgic about college days.
    Output: Mood: Nostalgic
    Music: Indie Rock, Old Bollywood, Soft Pop

    Now classify this:
    {user_input}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a music mood classifier."},
                {"role": "user", "content": system_prompt}
            ]
        )
        result = response.choices[0].message.content.strip()
        print(f"[Debug] GPT Response:\n{result}\n")
        return result

    except openai.RateLimitError:
        # Fallback response
        fallback = (
            "Mood: Happy"
            # "Music: {result}\n"
            # "This is a fallback response due to rate limiting."
        )
        print("[Fallback] Fallback to happy playlist.")
        return fallback

    except Exception as e:
        print(f"[Error] Unexpected error from GPT: {e}")
        return "Mood: Unknown\nMusic: Try uplifting or calming playlists."

# Extract mood from GPT output
def extract_mood(gpt_response):
    for line in gpt_response.split("\n"):
        if "Mood:" in line:
            return line.replace("Mood:", "").strip()
    return None

# Search Spotify for playlist
def search_spotify_playlist(spotify, mood):
    results = spotify.search(q=f"{mood} playlist", type='playlist', limit=1)
    if results["playlists"]["items"]:
        playlist = results["playlists"]["items"][0]
        name = playlist["name"]
        url = playlist["external_urls"]["spotify"]
        return f"[{name}]({url})"
    # Fallback playlist if no match found
    fallback_name = "Happy Hits"
    fallback_url = "https://open.spotify.com/playlist/4nqbYFYZOCospBb4miwHWy"
    return f"[{fallback_name}]({fallback_url}) (fallback)"


# Main function
def main():
    openai_key, spotify_id, spotify_secret = load_api_keys()
    client = setup_openai(openai_key)
    spotify = setup_spotify(spotify_id, spotify_secret)
    user_input = setup_ui()

    if user_input:
        with st.spinner("Analyzing your mood..."):
            gpt_response = get_music_mood(client, user_input)
            st.success("Here's what suits your mood:")
            st.markdown(f"{gpt_response}")

            mood = extract_mood(gpt_response)
            if mood:
                playlist = search_spotify_playlist(spotify, mood)
                st.markdown("🎵 Try this playlist on Spotify:")
                st.markdown(playlist)

# Run the app
if __name__ == "__main__":
    main()
