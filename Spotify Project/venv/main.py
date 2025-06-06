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
scope = "playlist-read-private"

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)
sp = Spotify(auth_manager=sp_oauth)


@app.route("/")
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists'))


@app.route("/callback")
def callback():
    sp_oauth.get_access_token(request.args.get('code'))
    return redirect(url_for('get_playlists'))


@app.route("/get_playlists")
def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    playlists = sp.current_user_playlists()
    playlists_info = [
    {
        "name": pl['name'],
        "url": pl['external_urls']['spotify'],
        "id": pl['id'],
        "image": pl['images'][0]['url'] if pl['images'] else None
    }
    for pl in playlists['items'][:5]  # Only top 5 playlists
]

    return render_template("playlists.html", playlists=playlists_info)


@app.route("/playlist/<playlist_id>")
def view_playlist(playlist_id):
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return redirect(sp_oauth.get_authorize_url())

    playlist = sp.playlist(playlist_id)
    tracks = [
        {
            "name": t['track']['name'],
            "artist": t['track']['artists'][0]['name']
        }
        for t in playlist['tracks']['items']
        if t['track']  # Ensure track isn't None
    ]
    return render_template("tracks.html", tracks=tracks, playlist_name=playlist['name'])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
# This code is a Flask application that integrates with the Spotify API to display a user's playlists and tracks.