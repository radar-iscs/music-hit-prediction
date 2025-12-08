import requests
import base64
import csv
import time
from datetime import datetime
from google.colab import userdata

CLIENT_ID = userdata.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = userdata.get('SPOTIFY_CLIENT_SECRET')

BATCH_SIZE = 100

def get_access_token():
    auth_url = "https://accounts.spotify.com/api/token"
    
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(auth_url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Error getting token: {response.status_code}")
        print(response.text)
        return None

def search_tracks(access_token, query, limit=50, offset=0):
    search_url = "https://api.spotify.com/v1/search"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": query,
        "type": "track",
        "limit": limit,
        "offset": offset
    }
    
    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 5))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return search_tracks(access_token, query, limit, offset)
    else:
        print(f"Search error: {response.status_code}")
        print(response.text)
        return None

def get_audio_features(access_token, track_ids):
    if not track_ids:
        return []
        
    features_url = "https://api.spotify.com/v1/audio-features"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"ids": ",".join(track_ids)}
    
    response = requests.get(features_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("audio_features", [])
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 5))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return get_audio_features(access_token, track_ids)
    else:
        print(f"Audio features error: {response.status_code}")
        print(response.text)
        return []

def get_artist_genres(access_token, artist_ids):
    genres_map = {}
    
    if not artist_ids:
        return genres_map
    
    for i in range(0, len(artist_ids), 50):
        batch = artist_ids[i:i+50]
        artists_url = "https://api.spotify.com/v1/artists"
        
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"ids": ",".join(batch)}
        
        response = requests.get(artists_url, headers=headers, params=params)
        if response.status_code == 200:
            artists_data = response.json().get("artists", [])
            for artist in artists_data:
                if artist:
                    genres = artist.get("genres", [])
                    genres_map[artist["id"]] = genres[0] if genres else "various"
        
        time.sleep(0.3)
    
    return genres_map


def main():
    access_token = get_access_token()
    
    if not access_token:
        print("Error: Failed to get access token.")
        return
    
    search_queries = [
        "year:2024",
        "year:2025", 
        "year:2024 pop",
        "year:2024 rock",
        "year:2024 indie",
        "year:2025 pop",
        "year:2024 electronic",
        "year:2024 hip-hop",
        "year:2024 r&b",
        "year:2024 acoustic",
        "year:2024 latin",
        "year:2024 dance",
        "new release 2024",
        "top hits 2024",
        "viral 2024"
    ]
    
    all_tracks = {}
    artist_ids_set = set()
    
    for query in search_queries:
        if len(all_tracks) >= BATCH_SIZE:
            break
            
        results = search_tracks(access_token, query, limit=50, offset=0)
        
        if results and "tracks" in results and "items" in results["tracks"]:
            tracks_found = 0
            for track in results["tracks"]["items"]:
                if len(all_tracks) >= BATCH_SIZE:
                    break
                
                track_id = track["id"]
                if track_id not in all_tracks:
                    artists = ";".join([artist["name"] for artist in track["artists"]])
                    first_artist_id = track["artists"][0]["id"] if track["artists"] else None
                    
                    if first_artist_id:
                        artist_ids_set.add(first_artist_id)
                    
                    all_tracks[track_id] = {
                        "track_id": track_id,
                        "artists": artists,
                        "album_name": track["album"]["name"],
                        "track_name": track["name"],
                        "popularity": track["popularity"],
                        "duration_ms": track["duration_ms"],
                        "explicit": track["explicit"],
                        "first_artist_id": first_artist_id
                    }
                    tracks_found += 1
            
        time.sleep(0.5)
    
    track_ids = list(all_tracks.keys())
    all_features = []
    
    for i in range(0, len(track_ids), BATCH_SIZE):
        batch_ids = track_ids[i:i+BATCH_SIZE]
        features = get_audio_features(access_token, batch_ids)
        if features:
            all_features.extend(features)
        time.sleep(0.5)
    
    artist_ids_list = list(artist_ids_set)
    artist_genres = get_artist_genres(access_token, artist_ids_list)
    
    features_lookup = {}
    for feat in all_features:
        if feat:
            features_lookup[feat["id"]] = feat
    
    final_tracks = []
    for track_id in track_ids:
        track_data = all_tracks[track_id]
        audio_feat = features_lookup.get(track_id, {})
        
        first_artist_id = track_data.get("first_artist_id")
        genre = artist_genres.get(first_artist_id, "various") if first_artist_id else "various"
        
        final_track = {
            "track_id": track_data["track_id"],
            "artists": track_data["artists"],
            "album_name": track_data["album_name"],
            "track_name": track_data["track_name"],
            "popularity": track_data["popularity"],
            "duration_ms": track_data["duration_ms"],
            "explicit": track_data["explicit"],
            "danceability": audio_feat.get("danceability", 0),
            "energy": audio_feat.get("energy", 0),
            "key": audio_feat.get("key", 0),
            "loudness": audio_feat.get("loudness", 0),
            "mode": audio_feat.get("mode", 0),
            "speechiness": audio_feat.get("speechiness", 0),
            "acousticness": audio_feat.get("acousticness", 0),
            "instrumentalness": audio_feat.get("instrumentalness", 0),
            "liveness": audio_feat.get("liveness", 0),
            "valence": audio_feat.get("valence", 0),
            "tempo": audio_feat.get("tempo", 0),
            "time_signature": audio_feat.get("time_signature", 4),
            "track_genre": genre
        }
        final_tracks.append(final_track)
    
    # save to csv file
    output_file = "spotify_tracks.csv"
    columns = [
        "", "track_id", "artists", "album_name", "track_name", "popularity",
        "duration_ms", "explicit", "danceability", "energy", "key", "loudness",
        "mode", "speechiness", "acousticness", "instrumentalness", "liveness",
        "valence", "tempo", "time_signature", "track_genre"
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        
        for idx, track in enumerate(final_tracks):
            row = [
                idx,
                track["track_id"],
                track["artists"],
                track["album_name"],
                track["track_name"],
                track["popularity"],
                track["duration_ms"],
                str(track["explicit"]).upper(),
                track["danceability"],
                track["energy"],
                track["key"],
                track["loudness"],
                track["mode"],
                track["speechiness"],
                track["acousticness"],
                track["instrumentalness"],
                track["liveness"],
                track["valence"],
                track["tempo"],
                track["time_signature"],
                track["track_genre"]
            ]
            writer.writerow(row)

if __name__ == "__main__":
    main()
