import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

scope = "playlist-modify-public user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

tracks = sp.current_user_top_tracks(limit=50, time_range='short_term')

recommended_tracks = set() 

for track in tqdm(tracks['items'], desc='Fetching recommended tracks'):
    if ((len(track['uri'])) == 36):
        track_uri = track['uri']
        mod_track_uri = track_uri.split(':')[-1]
        song_radio = sp.recommendations(seed_tracks=[mod_track_uri], limit=100)
        for song in song_radio['tracks']:
            if song['uri'] not in recommended_tracks:
                track_id = song['uri'].split(':')[-1]
                response = sp.current_user_saved_tracks_contains([track_id])
                if not any(response):
                    recommended_tracks.add(song['uri'])
                else:
                    continue
            else:
                continue
    else:
        continue




max_tracks_per_playlist = 10000
max_chunk_size = 50

playlist_name = 'Song Radio Playlist'
total_tracks = len(recommended_tracks)

if total_tracks <= max_tracks_per_playlist:
    new_playlist = sp.user_playlist_create(user=sp.current_user()['id'], name=playlist_name)
    track_uris = list(recommended_tracks) 
    with tqdm(total=len(track_uris), desc='Adding songs to playlist') as pbar:
        for i in range(0, len(track_uris), max_chunk_size):
            sp.playlist_add_items(new_playlist['id'], track_uris[i:i+max_chunk_size])
            pbar.update(max_chunk_size)

else:
    playlist_count = 1
    with tqdm(total=total_tracks, desc='Creating playlists') as pbar:
        while total_tracks > 0:
            playlist_name = f'Song Radio Playlist {playlist_count}'
            if total_tracks > max_tracks_per_playlist:
                playlist_tracks = list(recommended_tracks)[:max_tracks_per_playlist]  
                recommended_tracks = recommended_tracks.difference(playlist_tracks)  
                total_tracks -= max_tracks_per_playlist
            else:
                playlist_tracks = list(recommended_tracks)
                total_tracks = 0
            new_playlist = sp.user_playlist_create(user=sp.current_user()['id'], name=playlist_name)
            playlist_tracks_filtered = []
            with tqdm(total=len(playlist_tracks), desc='Adding songs to playlist') as inner_pbar:
                for track in playlist_tracks:
                    track_id = track.split(':')[-1]
                    response = sp.current_user_saved_tracks_contains([track_id])
                    if not any(response):
                        playlist_tracks_filtered.append(track)
                        inner_pbar.update(1)
                    else:
                        print(f"Skipping liked song: {song['name']} by {song['artists'][0]['name']}")
                        inner_pbar.update(1)
            track_uris = [track for track in playlist_tracks_filtered]
            
            if len(track_uris) <= max_chunk_size:
                sp.playlist_add_items(new_playlist['id'], track_uris)
            else:
                for i in range(0, len(track_uris), max_chunk_size):
                    sp.playlist_add_items(new_playlist['id'], track_uris[i:i+max_chunk_size])
                    pbar.update(len(playlist_tracks))
                    playlist_count += 1