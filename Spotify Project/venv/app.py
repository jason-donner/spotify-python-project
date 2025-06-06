import spotipy
import os
from flask import Flask, session, redirect, url_for, request, render_template
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

client_id = "017746cf3102498190e0977e02205ed7"
client_secret = "b7e90f3243aa485bb0bb73bff4beae41"
redirect_uri = "http://127.0.0.1:5000/callback"
scope = "user-top-read playlist-modify-private playlist-modify-public"

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

@app.route("/")
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return redirect(sp_oauth.get_authorize_url())
    return redirect(url_for('get_top_tracks'))

@app.route("/callback")
def callback():
    code = request.args.get('code')
    if code:
        sp_oauth.get_access_token(code)
    return redirect(url_for('get_top_tracks'))

@app.route("/get_top_tracks", methods=["GET", "POST"])
def get_top_tracks():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return redirect(sp_oauth.get_authorize_url())

    token_info = cache_handler.get_cached_token()
    sp = Spotify(auth=token_info['access_token'])

    time_range = request.args.get('time_range', 'medium_term')
    top_tracks = sp.current_user_top_tracks(limit=25, time_range=time_range)

    tracks_info = []
    for track in top_tracks['items']:
        artist_id = track['artists'][0]['id']
        artist = sp.artist(artist_id)
        genres = artist.get('genres', [])

        tracks_info.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "album_image": track['album']['images'][0]['url'] if track['album']['images'] else None,
            "spotify_url": track['external_urls']['spotify'],
            "genres": genres
        })

    return render_template("top_tracks.html", tracks=tracks_info, time_range=time_range)

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return redirect(sp_oauth.get_authorize_url())

    token_info = cache_handler.get_cached_token()
    sp = Spotify(auth=token_info['access_token'])

    playlist_name = request.form.get("playlist_name", "My Top Tracks")
    is_public = request.form.get("playlist_public", "false").lower() == "true"
    time_range = request.form.get("time_range", "medium_term")

    user = sp.current_user()
    user_id = user["id"]

    top_tracks = sp.current_user_top_tracks(limit=25, time_range=time_range)
    track_uris = [track["uri"] for track in top_tracks["items"]]

    playlist = sp.user_playlist_create(
        user=user_id,
        name=playlist_name,
        public=is_public,
        description=f"Top tracks from your {time_range.replace('_', ' ')} listening"
    )

    sp.playlist_add_items(playlist_id=playlist["id"], items=track_uris)

    return redirect(playlist["external_urls"]["spotify"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
