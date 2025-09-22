"""
Music-specific HTML generation for Kodi Now Playing application.
Handles music display with album poster, discart/cdart spinning animation, and music-specific layout.
"""

def generate_html(item, session_id, downloaded_art, progress_data, details):
    """
    Generate HTML for music display.
    
    Args:
        item (dict): Media item from Kodi API
        session_id (str): Session ID for file naming
        downloaded_art (dict): Downloaded artwork files
        progress_data (dict): Playback progress information
        details (dict): Detailed media information
        
    Returns:
        str: HTML content for music display
    """
    # Extract additional details from the enhanced API calls (define early to avoid variable scope issues)
    # Use safe fallbacks to prevent crashes
    if isinstance(details, dict):
        album_details = details.get("album", {})
        artist_details = details.get("artist", {})
    else:
        print(f"[WARNING] Details is not a dict: {type(details)}, value: {details}", flush=True)
        album_details = {}
        artist_details = {}
        # If details is not a dict, create a safe fallback
        if not isinstance(details, dict):
            details = {}
    
    # Extract URLs for artwork - use safe fallbacks
    try:
        # Ensure downloaded_art is a dict
        if not isinstance(downloaded_art, dict):
            print(f"[WARNING] Downloaded_art is not a dict: {type(downloaded_art)}", flush=True)
            downloaded_art = {}
        
        # For music, use thumbnail for album artwork, fallback to poster
        album_poster_url = f"/media/{downloaded_art.get('thumbnail')}" if downloaded_art.get("thumbnail") else f"/media/{downloaded_art.get('poster')}" if downloaded_art.get("poster") else ""
        # Try to get fanart from downloaded art, or from various sources
        fanart_url = f"/media/{downloaded_art.get('fanart')}" if downloaded_art.get("fanart") else ""
        if not fanart_url:
            # Try multiple sources for fanart
            if isinstance(album_details, dict) and album_details.get("fanart"):
                fanart_url = album_details.get("fanart")
                print(f"[DEBUG] Using album fanart: {fanart_url}", flush=True)
            elif isinstance(artist_details, dict) and artist_details.get("fanart"):
                fanart_url = artist_details.get("fanart")
                print(f"[DEBUG] Using artist fanart: {fanart_url}", flush=True)
            elif item.get("art", {}).get("fanart"):
                fanart_url = item.get("art", {}).get("fanart")
                print(f"[DEBUG] Using item fanart: {fanart_url}", flush=True)
            elif item.get("art", {}).get("albumartist.fanart"):
                fanart_url = item.get("art", {}).get("albumartist.fanart")
                print(f"[DEBUG] Using albumartist.fanart: {fanart_url}", flush=True)
            elif item.get("art", {}).get("artist.fanart"):
                fanart_url = item.get("art", {}).get("artist.fanart")
                print(f"[DEBUG] Using artist.fanart: {fanart_url}", flush=True)
    except Exception as e:
        print(f"[WARNING] Artwork URL generation failed: {e}", flush=True)
        album_poster_url = ""
        fanart_url = ""
    # Look for both discart and cdart for music
    discart_url = f"/media/{downloaded_art.get('discart')}" if downloaded_art.get("discart") else ""
    cdart_url = f"/media/{downloaded_art.get('cdart')}" if downloaded_art.get("cdart") else ""
    # Use discart if available, otherwise use cdart
    discart_display_url = discart_url if discart_url else cdart_url
    banner_url = f"/media/{downloaded_art.get('banner')}" if downloaded_art.get("banner") else ""
    clearlogo_url = f"/media/{downloaded_art.get('clearlogo')}" if downloaded_art.get("clearlogo") else ""
    clearart_url = f"/media/{downloaded_art.get('clearart')}" if downloaded_art.get("clearart") else ""
    
    # Extract music information
    title = item.get("title", "Untitled Track")
    album = item.get("album", "")
    artist = item.get("artist", [])
    artist_names = ", ".join(artist) if artist else "Unknown Artist"
    plot = item.get("plot", item.get("description", ""))
    
    # Additional details already extracted above
    
    # Get artist biography (use description field from official schema)
    artist_bio = artist_details.get("description", "") if isinstance(artist_details, dict) else ""
    
    # Get additional album info (fallback to item data if API failed)
    album_year = album_details.get("year", item.get("year", "")) if isinstance(album_details, dict) else item.get("year", "")
    album_rating = album_details.get("rating", item.get("rating", 0)) if isinstance(album_details, dict) else item.get("rating", 0)
    
    # Get additional song info - ensure details is a dict
    if not isinstance(details, dict):
        details = {}
    song_comment = details.get("comment", "")
    song_lyrics = details.get("lyrics", "")
    song_disc = details.get("disc", 0)
    song_votes = details.get("votes", 0)
    song_user_rating = details.get("userrating", 0)
    song_bpm = details.get("bpm", 0)
    song_samplerate = details.get("samplerate", 0)
    song_bitrate = details.get("bitrate", 0)
    song_channels = details.get("channels", 0)
    song_release_date = details.get("releasedate", "")
    song_original_date = details.get("originaldate", "")
    
    
    # Get additional artist info - ensure artist_details is a dict
    if not isinstance(artist_details, dict):
        artist_details = {}
    artist_born = artist_details.get("born", "")
    artist_formed = artist_details.get("formed", "")
    artist_years_active = artist_details.get("yearsactive", "")
    artist_genre = artist_details.get("genre", [])
    artist_mood = artist_details.get("mood", [])
    artist_style = artist_details.get("style", [])
    artist_gender = artist_details.get("gender", "")
    artist_instrument = artist_details.get("instrument", [])
    artist_type = artist_details.get("type", "")
    artist_sortname = artist_details.get("sortname", "")
    artist_disambiguation = artist_details.get("disambiguation", "")
    
    # If API calls failed, use basic item data
    if not isinstance(album_details, dict) and album:
        album_details = {"title": album, "year": item.get("year", "")}
    if not isinstance(artist_details, dict) and artist_names:
        artist_details = {"name": artist_names}
    
    # Debug logging
    print(f"[DEBUG] Album details: {album_details}", flush=True)
    print(f"[DEBUG] Artist details: {artist_details}", flush=True)
    print(f"[DEBUG] Fanart URL: {fanart_url}", flush=True)
    print(f"[DEBUG] Album year: {album_year}, Album rating: {album_rating}", flush=True)
    
    # Get rating from details or fallback - ensure details is a dict
    if not isinstance(details, dict):
        details = {}
    rating = round(details.get("rating", 0.0), 1)
    rating_html = f"<strong>⭐ {rating}</strong>" if rating > 0 else ""
    
    # Initialize defaults
    hdr_type = "SDR"
    audio_languages = "N/A"
    subtitle_languages = "N/A"
    
    # Extract streamdetails - ensure details is a dict
    if not isinstance(details, dict):
        details = {}
    streamdetails = details.get("streamdetails", {})
    if not isinstance(streamdetails, dict):
        streamdetails = {}
    video_info = streamdetails.get("video", [{}])[0] if isinstance(streamdetails.get("video"), list) and len(streamdetails.get("video", [])) > 0 else {}
    audio_info = streamdetails.get("audio", []) if isinstance(streamdetails.get("audio"), list) else []
    subtitle_info = streamdetails.get("subtitle", []) if isinstance(streamdetails.get("subtitle"), list) else []
    
    # HDR type (usually not applicable for music, but keeping for consistency)
    hdr_type = video_info.get("hdrtype", "").upper() or "SDR"
    
    # Audio languages
    audio_languages = ", ".join(sorted(set(
        a.get("language", "")[:3].upper() for a in audio_info if a.get("language")
    ))) or "N/A"
    
    # Subtitle languages
    subtitle_languages = ", ".join(sorted(set(
        s.get("language", "")[:3].upper() for s in subtitle_info if s.get("language")
    ))) or "N/A"
    
    # Genre and formatting - ensure details is a dict
    if not isinstance(details, dict):
        details = {}
    genre_list = details.get("genre", [])
    if not isinstance(genre_list, list):
        genre_list = []
    genres = [g.capitalize() for g in genre_list]
    genre_badges = genres[:3]
    
    # Format media info
    resolution = "Audio"  # Music doesn't have video resolution
    audio_codec = audio_info[0].get("codec", "Unknown").upper() if audio_info else "Unknown"
    channels = audio_info[0].get("channels", 0) if audio_info else 0
    
    # Playback progress
    elapsed = progress_data.get("elapsed", 0)
    duration = progress_data.get("duration", 0)
    percent = int((elapsed / duration) * 100) if duration else 0
    paused = progress_data.get("paused", False)
    
    # Generate HTML
    html = f"""
    <html>
    <head>
      <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
      <style>
        body {{
          font-family: sans-serif;
          animation: fadeIn 1s;
          background: url('{fanart_url}') center center / cover no-repeat fixed;
          position: relative;
          margin: 0;
          padding: 0;
          opacity: 1;
          transition: opacity 1.5s ease;
        }}
        body.fade-out {{
          opacity: 0;
        }}
        .content {{
          position: relative;
          background: rgba(0,0,0,0.5);
          border-radius: 12px;
          padding: 80px 40px 40px 40px;
          backdrop-filter: blur(5px);
          box-shadow: 0 8px 32px rgba(0,0,0,0.8);
          display: flex;
          gap: 40px;
          color: white;
        }}
        .poster-container {{
          position: relative;
          overflow: visible;
          height: 240px;
          width: auto;
        }}
        .poster {{
          height: 240px;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.6);
          position: relative;
          z-index: 2;
        }}
        .discart-wrapper {{
          position: absolute;
          top: -60px;
          left: 50%;
          transform: translateX(-50%);
          z-index: 1;
          height: 120px;
          width: 160px;
        }}
        .discart {{
          width: 160px;
          animation: spin 4s linear infinite;
          opacity: 1;
          filter: drop-shadow(0 0 4px rgba(0,0,0,0.6));
        }}
        @keyframes spin {{
          from {{ transform: rotate(0deg); }}
          to  {{ transform: rotate(360deg); }}
        }}
        .progress {{
          background: #2a2a2a;
          border-radius: 15px;
          height: 20px;
          margin-top: 6px;
          overflow: hidden;
          border: 1px solid rgba(0,0,0,0.75);
          box-shadow: 
            inset 0 1px 0 rgba(255,255,255,0.1),
            inset 0 0 5px rgba(0,0,0,0.3),
            0 2px 2px rgba(255,255,255,0.1),
            inset 0 5px 10px rgba(0,0,0,0.4);
          position: relative;
        }}
        .bar {{
          background: linear-gradient(135deg, #4caf50 0%, #45a049 50%, #4caf50 100%);
          height: 20px;
          border-radius: 15px 3px 3px 15px;
          width: {percent}%;
          transition: width 0.5s;
          position: relative;
          box-shadow: 
            inset 0 8px 0 rgba(255,255,255,0.2),
            inset 0 1px 1px rgba(0,0,0,0.125);
          border-right: 1px solid rgba(0,0,0,0.3);
        }}
        .small {{
          font-size: 0.9em;
          color: #ccc;
        }}
        .badges {{
          display: flex;
          gap: 8px;
          margin-top: 10px;
          flex-wrap: wrap;
          align-items: center;
        }}
        .badge {{
          background: #333;
          color: white;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 0.8em;
          box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        }}
        .badge-imdb {{
          display: flex;
          align-items: center;
          gap: 4px;
          background: #f5c518;
          color: black;
          padding: 4px 10px;
          border-radius: 20px;
          font-size: 0.8em;
          box-shadow: 0 2px 6px rgba(0,0,0,0.4);
          text-decoration: none;
          font-weight: bold;
        }}
        .badge-imdb img {{
          height: 14px;
        }}
        .banner {{
          display: block;
          margin-bottom: 10px;
          max-width: 360px;
          width: 100%;
        }}
        .logo {{
          display: block;
          margin-bottom: 10px;
          max-height: 150px;
        }}
        .clearart {{
          display: block;
          margin-top: 10px;
          max-height: 80px;
        }}
        .music-info {{
          margin-bottom: 20px;
        }}
        .track-title {{
          font-size: 1.5em;
          font-weight: bold;
          margin-bottom: 5px;
          color: #4caf50;
        }}
        .album-title {{
          font-size: 1.2em;
          font-weight: bold;
          margin-bottom: 10px;
          color: #ccc;
        }}
        .marquee {{
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 80px;
          background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
          border: 3px solid #333;
          border-radius: 0 0 15px 15px;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          box-shadow: 0 4px 20px rgba(0,0,0,0.8);
          margin-bottom: 20px;
        }}
        .marquee-toggle {{
          position: absolute;
          bottom: -15px;
          left: 50%;
          transform: translateX(-50%);
          width: 50px;
          height: 15px;
          background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
          border: none;
          border-radius: 0 0 25px 25px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
          z-index: 1001;
        }}
        .marquee-toggle::before {{
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(45deg, #ff6b35, #f7931e, #ff6b35, #f7931e);
          border-radius: 0 0 25px 25px;
          z-index: -1;
          animation: marqueeGlow 2s ease-in-out infinite alternate;
        }}
        .marquee-toggle:hover {{
          transform: translateX(-50%) scale(1.05);
        }}
        .marquee-toggle.hidden {{
          background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
        }}
        .marquee-toggle.hidden::before {{
          opacity: 0.5;
        }}
        .arrow {{
          width: 0;
          height: 0;
          border-left: 8px solid transparent;
          border-right: 8px solid transparent;
          border-bottom: 12px solid white;
          transition: transform 0.3s ease;
        }}
        .arrow.up {{
          transform: rotate(180deg);
        }}
        .marquee::before {{
          content: "";
          position: absolute;
          top: -8px;
          left: -8px;
          right: -8px;
          bottom: -8px;
          background: linear-gradient(45deg, #ff6b35, #f7931e, #ff6b35, #f7931e);
          border-radius: 0 0 20px 20px;
          z-index: -1;
          animation: marqueeGlow 2s ease-in-out infinite alternate;
        }}
        .marquee-text {{
          font-family: 'Arial Black', Arial, sans-serif;
          font-size: 2.2em;
          font-weight: 900;
          color: #fff;
          text-shadow: 
            0 0 10px #ff6b35,
            0 0 20px #ff6b35,
            0 0 30px #ff6b35,
            2px 2px 4px rgba(0,0,0,0.8);
          letter-spacing: 4px;
          text-transform: uppercase;
          animation: marqueePulse 1.5s ease-in-out infinite alternate;
        }}
        @keyframes marqueeGlow {{
          0% {{ opacity: 0.7; }}
          100% {{ opacity: 1; }}
        }}
        @keyframes marqueePulse {{
          0% {{ 
            text-shadow: 
              0 0 10px #ff6b35,
              0 0 20px #ff6b35,
              0 0 30px #ff6b35,
              2px 2px 4px rgba(0,0,0,0.8);
          }}
          100% {{ 
            text-shadow: 
              0 0 15px #ff6b35,
              0 0 25px #ff6b35,
              0 0 35px #ff6b35,
              2px 2px 4px rgba(0,0,0,0.8);
          }}
        }}
        .content {{
          margin-top: 100px;
        }}
        .marquee.hidden {{
          transform: translateY(-100%);
          transition: transform 0.5s ease-in-out;
        }}
        .content.no-marquee {{
          margin-top: 20px;
        }}
      </style>
      <script>
        let elapsed = {elapsed};
        let duration = {duration};
        let paused = {str(paused).lower()};
        let lastPlaybackState = null;

        function updateTime() {{
          if (!paused && elapsed < duration) {{
            elapsed++;
            let percent = Math.floor((elapsed / duration) * 100);
            document.querySelector('.bar').style.width = percent + '%';
            let min = Math.floor(elapsed / 60);
            let sec = elapsed % 60;
            document.getElementById('elapsed').textContent = min + ':' + (sec < 10 ? '0' : '') + sec;
          }}
        }}

        function resyncTime() {{
          fetch('/nowplaying?json=1')
            .then(res => res.json())
            .then(data => {{
              elapsed = data.elapsed;
              duration = data.duration;
              paused = data.paused;
            }});
        }}

        function checkPlaybackChange() {{
          fetch('/poll_playback')
            .then(res => {{
              if (!res.ok) {{
                throw new Error(`HTTP ${{res.status}}`);
              }}
              return res.json();
            }})
            .then(data => {{
              const currentState = data.playing;
              if (lastPlaybackState === null) {{
                lastPlaybackState = currentState;
              }} else if (currentState !== lastPlaybackState) {{
                document.body.classList.add('fade-out');
                setTimeout(() => {{
                  window.location.href = '/'; // Redirect to root when playback stops
                }}, 1500);
              }}
              lastPlaybackState = currentState;
            }})
            .catch(error => {{
              console.error('Polling error:', error);
              // Retry after shorter interval on error
              setTimeout(checkPlaybackChange, 2000);
            }});
        }}

        function toggleMarquee() {{
          const marquee = document.querySelector('.marquee');
          const toggle = document.querySelector('.marquee-toggle');
          const content = document.querySelector('.content');
          
          marquee.classList.toggle('hidden');
          toggle.classList.toggle('hidden');
          
          if (marquee.classList.contains('hidden')) {{
            content.classList.add('no-marquee');
            toggle.innerHTML = '<div class="arrow up"></div>';
          }} else {{
            content.classList.remove('no-marquee');
            toggle.innerHTML = '<div class="arrow"></div>';
          }}
        }}

        setInterval(updateTime, 1000);
        setInterval(resyncTime, 5000);
        setInterval(checkPlaybackChange, 2000);
      </script>
    </head>
    <body>
      <div class="marquee">
        <div class="marquee-text">NOW PLAYING</div>
        <div class="marquee-toggle" onclick="toggleMarquee()" title="Hide Marquee">
          <div class="arrow up"></div>
        </div>
      </div>
      <div class="content">
        <div class="poster-container">
          {"<div class='discart-wrapper'><img class='discart' src='" + discart_display_url + "' /></div>" if discart_display_url else ""}
          {f"<img class='poster' src='{album_poster_url}' />" if album_poster_url else ""}
          {f"<img class='clearart' src='{clearart_url}' />" if clearart_url else ""}
        </div>
        <div>
          {f"<img class='logo' src='{clearlogo_url}' />" if clearlogo_url else (f"<img class='banner' src='{banner_url}' />" if banner_url else f"<h2 style='margin-bottom: 4px;'>🎵 {title}</h2>")}
          
          <div class="music-info">
            <div class="track-title">{title}</div>
            <div class="album-title">by {artist_names}</div>
            {f"<div class='album-title'>from {album}" + (f" ({album_year})" if album_year else "") + "</div>" if album else ""}
            {f"<div class='album-title'>Album Rating: ⭐ {album_rating}</div>" if album_rating > 0 else ""}
          </div>
          
          {f"<h3 style='margin-top:20px;'>👤 Artist Info</h3>" if artist_born or artist_formed or artist_years_active or artist_genre or artist_mood or artist_style or artist_gender or artist_instrument or artist_type else ""}
          {f"<p><strong>Born:</strong> {artist_born}</p>" if artist_born else ""}
          {f"<p><strong>Formed:</strong> {artist_formed}</p>" if artist_formed else ""}
          {f"<p><strong>Years Active:</strong> {artist_years_active}</p>" if artist_years_active else ""}
          {f"<p><strong>Gender:</strong> {artist_gender}</p>" if artist_gender else ""}
          {f"<p><strong>Type:</strong> {artist_type}</p>" if artist_type else ""}
          {f"<p><strong>Instruments:</strong> {', '.join(artist_instrument)}</p>" if artist_instrument else ""}
          {f"<p><strong>Genre:</strong> {', '.join(artist_genre)}</p>" if artist_genre else ""}
          {f"<p><strong>Mood:</strong> {', '.join(artist_mood)}</p>" if artist_mood else ""}
          {f"<p><strong>Style:</strong> {', '.join(artist_style)}</p>" if artist_style else ""}
          
          {f"<h3 style='margin-top:20px;'>📖 Artist Biography</h3>" if artist_bio else ""}
          {f"<p style='max-width:600px;'>{artist_bio}</p>" if artist_bio else ""}
          
          {f"<h3 style='margin-top:20px;'>📖 Track Description</h3>" if plot else ""}
          {f"<p style='max-width:600px;'>{plot}</p>" if plot else ""}
          
          {f"<h3 style='margin-top:20px;'>🎵 Track Details</h3>" if song_comment or song_lyrics or song_disc or song_bpm or song_samplerate or song_bitrate or song_channels or song_release_date or song_original_date else ""}
          {f"<p><strong>Comment:</strong> {song_comment}</p>" if song_comment else ""}
          {f"<p><strong>Disc:</strong> {song_disc}</p>" if song_disc > 0 else ""}
          {f"<p><strong>BPM:</strong> {song_bpm}</p>" if song_bpm > 0 else ""}
          {f"<p><strong>Sample Rate:</strong> {song_samplerate} Hz</p>" if song_samplerate > 0 else ""}
          {f"<p><strong>Bitrate:</strong> {song_bitrate} kbps</p>" if song_bitrate > 0 else ""}
          {f"<p><strong>Channels:</strong> {song_channels}</p>" if song_channels > 0 else ""}
          {f"<p><strong>Release Date:</strong> {song_release_date}</p>" if song_release_date else ""}
          {f"<p><strong>Original Date:</strong> {song_original_date}</p>" if song_original_date else ""}
          {f"<p><strong>User Rating:</strong> ⭐ {song_user_rating}/10</p>" if song_user_rating > 0 else ""}
          {f"<p><strong>Votes:</strong> {song_votes}</p>" if song_votes > 0 else ""}
          <div class="badges">
            {rating_html}
            <span class="badge">{resolution}</span>
            <span class="badge">{audio_codec} {channels}ch</span>
            <span class="badge">Audio: {audio_languages}</span>
            {"".join(f"<span class='badge'>{g}</span>" for g in genre_badges)}
          </div>
          <div class="progress">
            <div class="bar"></div>
          </div>
          <p class="small">
            <span id="elapsed">{elapsed//60}:{elapsed%60:02}</span> / {duration//60}:{duration%60:02}
          </p>
        </div>
      </div>
    </body>
    </html>
    """
    return html
