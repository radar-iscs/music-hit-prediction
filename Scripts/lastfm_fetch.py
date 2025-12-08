import requests
import hashlib
from google.colab import userdata

API_KEY = userdata.get('LASTFM_API_KEY')
API_SECRET = userdata.get('LASTFM_API_SECRET')
BASE_URL = "https://ws.audioscrobbler.com/2.0/"

def make_request(params: dict) -> dict:
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": True, "message": f"Request failed: {str(e)}"}
    except ValueError as e:
        return {"error": True, "message": f"Invalid JSON response: {str(e)}"}

def get_chart_top_tracks(limit: int = 20) -> dict:
    params = {
        "method": "chart.getTopTracks",
        "api_key": API_KEY,
        "limit": limit,
        "format": "json"
    }
    return make_request(params)

def fetch_and_save_top_tracks(limit: int = 100, output_file: str = "lastfm_tracks.csv") -> None:
    import csv
    
    data = get_chart_top_tracks(limit=limit)
    
    if "error" in data:
        print(f"Error: {data.get('message', 'Unknown error')}")
        return
    
    if "tracks" not in data:
        print("No tracks found in response.")
        return
    
    tracks = data["tracks"].get("track", [])
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "Track Name", "Artist", "Playcount", "Listeners", "URL"
        ])
        
        for i, track in enumerate(tracks, 1):
            artist_name = track.get("artist", {})
            if isinstance(artist_name, dict):
                artist_name = artist_name.get("name", "N/A")
            
            writer.writerow([
                i,
                track.get("name", "N/A"),
                artist_name,
                track.get("playcount", "N/A"),
                track.get("listeners", "N/A"),
                track.get("url", "N/A")
            ])
    
    print(f"Saved {len(tracks)} tracks to {output_file}")


if __name__ == "__main__":
    fetch_and_save_top_tracks(limit=100, output_file="lastfm_tracks.csv")