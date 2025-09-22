from flask import Flask, render_template_string, request, jsonify, send_file
import requests
import os
import urllib.parse
import uuid
from parser import route_media_display

app = Flask(__name__)

# Kodi connection details - fallback IP and user/pass can be hardcoded if no .env file exists
KODI_HOST = os.getenv("KODI_HOST", "http://<insert_IP_to_Kodi_Device:Port_KODI_HTTP")
KODI_USER = os.getenv("KODI_USER", "<your_Kodi_HTTP_username>")
KODI_PASS = os.getenv("KODI_PASS", "<your_Kodi_HTTP_password")
AUTH = (KODI_USER, KODI_PASS) if KODI_USER else None
HEADERS = {"Content-Type": "application/json"}

ART_TYPES = ["poster", "fanart", "clearlogo", "clearart", "discart", "cdart", "banner", "season.poster", "thumbnail"]

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kodi Now Playing</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(to bottom right, #222, #444);
                color: white;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                opacity: 1;
                transition: opacity 1.5s ease;
                animation: fadeIn 1.5s ease;
            }
            body.fade-out {
                opacity: 0;
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .message-box {
                background: rgba(0,0,0,0.6);
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.8);
                font-size: 1.5em;
                font-style: italic;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="message-box">
            🎬 No Media Currently Playing<br>Awaiting Media Playback
        </div>
        <script>
            let lastPlaybackState = false; // Initialize to false

            function checkPlaybackChange() {
                fetch('/poll_playback')
                    .then(res => {
                        if (!res.ok) {
                            throw new Error(`HTTP ${res.status}`);
                        }
                        return res.json();
                    })
                    .then(data => {
                        const currentState = data.playing;
                        if (currentState !== lastPlaybackState) {
                            document.body.classList.add('fade-out');
                            setTimeout(() => {
                                window.location.href = '/nowplaying';
                            }, 1500);
                        }
                        lastPlaybackState = currentState;
                    })
                    .catch(error => {
                        console.error('Polling error:', error);
                        // Don't change state on error, just retry
                        setTimeout(checkPlaybackChange, 3000);
                    });
            }
            setInterval(checkPlaybackChange, 2000); // Poll every 2 seconds
        </script>
    </body>
    </html>
    """

@app.route("/poll_playback")
def poll_playback():
    try:
        players = kodi_rpc("Player.GetActivePlayers")
        if players and players.get("result"):
            return jsonify({"playing": True})
        return jsonify({"playing": False})
    except Exception as e:
        print(f"[ERROR] Poll playback failed: {e}", flush=True)
        # Return False on error - this will trigger retry logic on frontend
        return jsonify({"playing": False, "error": True})

def kodi_rpc(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1
    }
    try:
        r = requests.post(f"{KODI_HOST}/jsonrpc", headers=HEADERS, json=payload, auth=AUTH, timeout=8)
        r.raise_for_status()
        response_json = r.json()
        print(f"[DEBUG] Kodi response for {method}:", response_json, flush=True)
        return response_json
    except Exception as e:
        print(f"[ERROR] Kodi RPC failed for method {method}: {e}", flush=True)
        return None


def prepare_and_download_art(item, session_id):
    downloaded = {}

    art_map = item.get("art", {})
    if item.get("thumbnail") and not art_map.get("poster"):
        art_map["poster"] = item["thumbnail"]

    # Handle TV show artwork with tvshow. prefix
    tvshow_art_map = {}
    for key, value in art_map.items():
        if key.startswith("tvshow."):
            # Map tvshow.poster to poster, tvshow.fanart to fanart, etc.
            clean_key = key.replace("tvshow.", "")
            tvshow_art_map[clean_key] = value

    # Handle music artwork with album., artist., and albumartist. prefixes
    music_art_map = {}
    for key, value in art_map.items():
        if key.startswith("album."):
            # Map album.thumb to thumbnail, album.poster to poster, etc.
            clean_key = key.replace("album.", "")
            if clean_key == "thumb":
                clean_key = "thumbnail"
            music_art_map[clean_key] = value
        elif key.startswith("artist."):
            # Map artist.fanart to fanart, artist.clearlogo to clearlogo, etc.
            clean_key = key.replace("artist.", "")
            music_art_map[clean_key] = value
        elif key.startswith("albumartist."):
            # Map albumartist.fanart to fanart, albumartist.clearlogo to clearlogo, etc.
            clean_key = key.replace("albumartist.", "")
            music_art_map[clean_key] = value

    # Merge all artwork (music takes precedence, then TV show, then regular)
    art_map = {**art_map, **tvshow_art_map, **music_art_map}
    
    # Debug logging for artwork
    print(f"[DEBUG] Original art_map keys: {list(item.get('art', {}).keys())}", flush=True)
    print(f"[DEBUG] Final art_map keys: {list(art_map.keys())}", flush=True)

    for art_type in ART_TYPES:
        raw_path = art_map.get(art_type)
        print(f"[DEBUG] Processing art_type: {art_type}, raw_path: {raw_path}", flush=True)
        if not raw_path:
            continue

        if raw_path.startswith("image://"):
            raw_path = urllib.parse.unquote(raw_path[len("image://"):])
        if raw_path.endswith("/"):
            raw_path = raw_path[:-1]

        # Handle external URLs directly (like fanart.tv, theaudiodb.com)
        if raw_path.startswith("https://") or raw_path.startswith("http://"):
            image_url = raw_path
        else:
            # Handle local Kodi paths
            try:
                response = kodi_rpc("Files.PrepareDownload", {"path": raw_path})
                details = response.get("result", {}).get("details", {})
                token = details.get("token")
                path = details.get("path")

                if token:
                    basename = os.path.basename(raw_path)
                    image_url = f"{KODI_HOST}/vfs/{token}/{urllib.parse.quote(basename)}"
                elif path:
                    image_url = f"{KODI_HOST}/{path}"
                else:
                    print(f"[ERROR] No valid download path for {art_type}", flush=True)
                    continue
            except Exception as e:
                print(f"[WARNING] Failed to prepare download for {art_type}: {e}", flush=True)
                continue

        filename = f"{session_id}_{art_type}.jpg"
        local_path = f"/tmp/{filename}"

        try:
            # Use authentication only for Kodi internal URLs
            if image_url.startswith(KODI_HOST):
                print(f"[DEBUG] Downloading with auth: {image_url}", flush=True)
                r = requests.get(image_url, auth=AUTH, timeout=5)
            else:
                print(f"[DEBUG] Downloading without auth: {image_url}", flush=True)
                r = requests.get(image_url, timeout=5)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
            downloaded[art_type] = filename
            print(f"[INFO] Downloaded {art_type} to {local_path}", flush=True)
        except Exception as e:
            print(f"[ERROR] Failed to download {art_type}: {e}", flush=True)

    return downloaded

@app.route("/media/<filename>")
def serve_image(filename):
    path = f"/tmp/{filename}"
    if os.path.exists(path):
        return send_file(path, mimetype="image/jpeg")
    return "Image not found", 404

# New route to serve static files like the IMDb icon
@app.route("/static/<filename>")
def serve_static(filename):
    return send_file(os.path.join(os.path.dirname(__file__), filename))

# Specific favicon route to ensure it works
@app.route("/favicon.ico")
def favicon():
    try:
        favicon_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
        print(f"[DEBUG] Favicon path: {favicon_path}", flush=True)
        print(f"[DEBUG] Favicon exists: {os.path.exists(favicon_path)}", flush=True)
        if os.path.exists(favicon_path):
            return send_file(favicon_path, mimetype="image/x-icon")
        else:
            print(f"[ERROR] Favicon file not found at: {favicon_path}", flush=True)
            return "Favicon not found", 404
    except Exception as e:
        print(f"[ERROR] Favicon route error: {e}", flush=True)
        return "Favicon error", 500


@app.route("/nowplaying")
def now_playing():
    if request.args.get("json") == "1":
        active_response = kodi_rpc("Player.GetActivePlayers")
        active = active_response.get("result") if active_response else None
        if not active:
            return jsonify({"elapsed": 0, "duration": 0, "paused": True})
        player_id = active[0]["playerid"]
        progress_response = kodi_rpc("Player.GetProperties", {
            "playerid": player_id,
            "properties": ["time", "totaltime", "speed"]
        })
        progress = progress_response.get("result") if progress_response else {}
        t = progress.get("time", {})
        d = progress.get("totaltime", {})
        speed = progress.get("speed", 0)
        def to_secs(t): return t.get("hours", 0) * 3600 + t.get("minutes", 0) * 60 + t.get("seconds", 0)
        return jsonify({
            "elapsed": to_secs(t),
            "duration": to_secs(d),
            "paused": speed == 0
        })

    # Get active players - this is critical, so if it fails, show error
    try:
        active_response = kodi_rpc("Player.GetActivePlayers")
        active = active_response.get("result") if active_response else None
        if not active:
            return render_template_string("""
            <html>
            <head>
              <style>
                body {
                  margin: 0;
                  padding: 0;
                  background: linear-gradient(to bottom right, #222, #444);
                  font-family: sans-serif;
                  color: white;
                  display: flex;
                  justify-content: center;
                  align-items: center;
                  height: 100vh;
                }
                .message-box {
                  background: rgba(0,0,0,0.6);
                  padding: 40px;
                  border-radius: 12px;
                  box-shadow: 0 4px 20px rgba(0,0,0,0.8);
                  font-size: 1.5em;
                  font-style: italic;
                }
              </style>
              <script>
                let lastPlaybackState = false; // Initialize to false

                function checkPlaybackChange() {
                  fetch('/poll_playback')
                    .then(res => res.json())
                    .then(data => {
                      const currentState = data.playing;
                      if (currentState !== lastPlaybackState) {
                        document.body.classList.add('fade-out');
                        setTimeout(() => {
                           location.reload(true);
                        }, 800);
                      }
                      lastPlaybackState = currentState;
                    });
                }
                setInterval(checkPlaybackChange, 5000); // Poll every 5 seconds
              </script>
            </head>
            <body>
              <div class="message-box">
                🎬 No Media Currently Playing<br>Awaiting Media Playback
              </div>
            </body>
            </html>
            """)

        player_id = active[0]["playerid"]
        
        # Get current item - this is critical, so if it fails, show error
        try:
            item_response = kodi_rpc("Player.GetItem", {
                "playerid": player_id,
                "properties": [
                    "title", "album", "artist", "season", "episode", "showtitle",
                    "tvshowid", "duration", "file", "director", "art", "plot", 
                    "cast", "resume", "genre", "rating", "streamdetails", "year"
                ]
            })
            result = item_response.get("result", {})
            item = result.get("item", {})
        except Exception as e:
            print(f"[ERROR] Failed to get current item: {e}", flush=True)
            raise e  # This is critical, so re-raise
        
        # Get item type to know which API call to make
        playback_type = item.get("type", "unknown")
        
        # Initialize details with basic fallback structure
        details = {
            "album": {"title": item.get("album", ""), "year": item.get("year", "")},
            "artist": {"label": ", ".join(item.get("artist", [])) if item.get("artist") else "Unknown Artist"}
        }
        
        # Get enhanced details for episodes, movies, and songs
        print(f"[DEBUG] Playback type detected: {playback_type}", flush=True)
        print(f"[DEBUG] Available IDs - songid: {item.get('songid')}, albumid: {item.get('albumid')}, artistid: {item.get('artistid')}", flush=True)
        if playback_type == "episode":
            try:
                print(f"[DEBUG] Getting enhanced details for episode", flush=True)
                episode_response = kodi_rpc("VideoLibrary.GetEpisodeDetails", {
                    "episodeid": item.get("id"),
                    "properties": ["streamdetails", "genre", "director", "cast", "uniqueid", "rating"]
                })
                if episode_response and episode_response.get("result"):
                    episode_details = episode_response["result"].get("episodedetails", {})
                    # Merge enhanced details with basic item data
                    details.update(episode_details)
                    # Ensure basic item data is preserved
                    details.update({
                        "title": item.get("title", ""),
                        "plot": item.get("plot", ""),
                        "season": item.get("season", 0),
                        "episode": item.get("episode", 0),
                        "showtitle": item.get("showtitle", ""),
                        "director": item.get("director", []),
                        "cast": item.get("cast", []),
                        "year": item.get("year", "")
                    })
                    print(f"[DEBUG] Enhanced episode details loaded", flush=True)
            except Exception as e:
                print(f"[WARNING] Failed to get enhanced episode details: {e}", flush=True)
                print(f"[DEBUG] Using basic item data for {playback_type}", flush=True)
        elif playback_type == "movie":
            try:
                print(f"[DEBUG] Getting enhanced details for movie", flush=True)
                movie_response = kodi_rpc("VideoLibrary.GetMovieDetails", {
                    "movieid": item.get("id"),
                    "properties": ["streamdetails", "genre", "director", "cast", "uniqueid", "rating"]
                })
                if movie_response and movie_response.get("result"):
                    movie_details = movie_response["result"].get("moviedetails", {})
                    # Merge enhanced details with basic item data
                    details.update(movie_details)
                    # Ensure basic item data is preserved
                    details.update({
                        "title": item.get("title", ""),
                        "plot": item.get("plot", ""),
                        "director": item.get("director", []),
                        "cast": item.get("cast", []),
                        "year": item.get("year", "")
                    })
                    print(f"[DEBUG] Enhanced movie details loaded", flush=True)
            except Exception as e:
                print(f"[WARNING] Failed to get enhanced movie details: {e}", flush=True)
                print(f"[DEBUG] Using basic item data for {playback_type}", flush=True)
        elif playback_type == "song":
            try:
                print(f"[DEBUG] Getting enhanced details for song", flush=True)
                print(f"[DEBUG] Basic item ID: {item.get('id')}", flush=True)
                # Get song details using the basic item ID
                song_response = kodi_rpc("AudioLibrary.GetSongDetails", {
                    "songid": item.get("id"),
                    "properties": ["title", "album", "artist", "duration", "rating", "year", "genre", "fanart", "thumbnail", "albumid", "artistid", "bitrate", "channels", "samplerate", "bpm", "comment", "lyrics", "mood", "playcount", "track", "disc"]
                })
                if song_response and song_response.get("result"):
                    song_details = song_response["result"].get("songdetails", {})
                    details.update(song_details)
                    print(f"[DEBUG] Enhanced song details loaded", flush=True)
                
                # Get album details if we have albumid
                albumid = song_details.get("albumid")
                if albumid:
                    try:
                        album_response = kodi_rpc("AudioLibrary.GetAlbumDetails", {
                            "albumid": albumid,
                            "properties": ["title", "artist", "year", "rating", "fanart", "thumbnail", "description", "genre", "mood", "style", "theme", "albumduration", "playcount", "albumlabel", "compilation", "totaldiscs"]
                        })
                        if album_response and album_response.get("result"):
                            album_details = album_response["result"].get("albumdetails", {})
                            details["album"] = album_details
                            print(f"[DEBUG] Enhanced album details loaded", flush=True)
                    except Exception as e:
                        print(f"[WARNING] Failed to get album details: {e}", flush=True)
                
                # Get artist details if we have artistid
                artistid = song_details.get("artistid")
                if artistid:
                    # Handle artistid as array (take first one) or single value
                    print(f"[DEBUG] Original artistid: {artistid}, type: {type(artistid)}", flush=True)
                    if isinstance(artistid, list) and len(artistid) > 0:
                        artistid = artistid[0]
                        print(f"[DEBUG] Converted artistid to: {artistid}, type: {type(artistid)}", flush=True)
                    try:
                        artist_response = kodi_rpc("AudioLibrary.GetArtistDetails", {
                            "artistid": artistid,
                            "properties": ["fanart", "thumbnail", "description", "born", "formed", "died", "disbanded", "genre", "mood", "style", "yearsactive"]
                        })
                        if artist_response and artist_response.get("result"):
                            artist_details = artist_response["result"].get("artistdetails", {})
                            details["artist"] = artist_details
                            print(f"[DEBUG] Enhanced artist details loaded", flush=True)
                    except Exception as e:
                        print(f"[WARNING] Failed to get artist details: {e}", flush=True)
                
                # Ensure basic item data is preserved
                details.update({
                    "title": item.get("title", ""),
                    "album": item.get("album", ""),
                    "artist": item.get("artist", []),
                    "year": item.get("year", "")
                })
                
            except Exception as e:
                print(f"[WARNING] Failed to get enhanced song details: {e}", flush=True)
                print(f"[DEBUG] Using basic item data for {playback_type}", flush=True)
        else:
            print(f"[DEBUG] Using basic item data for {playback_type}", flush=True)


        # Playback progress
        progress_response = kodi_rpc("Player.GetProperties", {
            "playerid": player_id,
            "properties": ["time", "totaltime", "speed"]
        })
        progress = progress_response.get("result") if progress_response else {}
        t = progress.get("time", {})
        d = progress.get("totaltime", {})
        speed = progress.get("speed", 0)
        def to_secs(t): return t.get("hours", 0) * 3600 + t.get("minutes", 0) * 60 + t.get("seconds", 0)
        elapsed = to_secs(t)
        duration = to_secs(d)
        percent = int((elapsed / duration) * 100) if duration else 0
        paused = speed == 0

        session_id = uuid.uuid4().hex
        
        # Try to download artwork, but don't fail if this breaks
        try:
            downloaded_art = prepare_and_download_art(item, session_id)
        except Exception as e:
            print(f"[WARNING] Artwork download failed, continuing without artwork: {e}", flush=True)
            downloaded_art = {}  # Empty artwork - page will still work

        # Prepare progress data
        progress_data = {
            "elapsed": elapsed,
            "duration": duration,
            "paused": paused
        }

        # Use the modular system to generate HTML
        html = route_media_display(item, session_id, downloaded_art, progress_data, details)
        return render_template_string(html)
    except Exception as e:
        print(f"[ERROR] Critical failure in now_playing route: {e}", flush=True)
        return render_template_string("""
        <html>
        <head>
          <style>
            body {
              margin: 0;
              padding: 0;
              background: linear-gradient(to bottom right, #222, #444);
              font-family: sans-serif;
              color: white;
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
            }
            .message-box {
              background: rgba(0,0,0,0.6);
              padding: 40px;
              border-radius: 12px;
              box-shadow: 0 4px 20px rgba(0,0,0,0.8);
              font-size: 1.5em;
              font-style: italic;
            }
          </style>
        </head>
        <body>
          <div class="message-box">
            🎬 No Media Currently Playing<br>Awaiting Media Playback
          </div>
        </body>
        </html>
        """)

def generate_fallback_html(item, progress_data):
    """Generate basic HTML when the modular system fails"""
    title = item.get("title", "Unknown Title")
    artist = ", ".join(item.get("artist", [])) if item.get("artist") else "Unknown Artist"
    album = item.get("album", "")
    elapsed = progress_data.get("elapsed", 0)
    duration = progress_data.get("duration", 0)
    paused = progress_data.get("paused", False)
    
    # Format time
    def format_time(seconds):
        if seconds == 0:
            return "0:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    return f"""
    <html>
    <head>
        <title>Now Playing - {title}</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: linear-gradient(to bottom right, #222, #444);
                font-family: sans-serif;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .now-playing {{
                background: rgba(0,0,0,0.6);
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.8);
                text-align: center;
                max-width: 600px;
            }}
            .title {{
                font-size: 2em;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .artist {{
                font-size: 1.5em;
                margin-bottom: 5px;
                color: #ccc;
            }}
            .album {{
                font-size: 1.2em;
                margin-bottom: 20px;
                color: #aaa;
            }}
            .progress {{
                font-size: 1em;
                color: #888;
            }}
            .status {{
                font-size: 1.2em;
                margin-top: 20px;
                color: {'#ff6b6b' if paused else '#51cf66'};
            }}
        </style>
    </head>
    <body>
        <div class="now-playing">
            <div class="title">{title}</div>
            <div class="artist">{artist}</div>
            <div class="album">{album}</div>
            <div class="progress">{format_time(elapsed)} / {format_time(duration)}</div>
            <div class="status">{'⏸️ Paused' if paused else '▶️ Playing'}</div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)