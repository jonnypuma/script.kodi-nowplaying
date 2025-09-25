"""
TV Episode-specific HTML generation for Kodi Now Playing application.
Handles TV episode display with show poster, season poster, and episode information.
"""

def generate_html(item, session_id, downloaded_art, progress_data, details):
    """
    Generate HTML for TV episode display.
    
    Args:
        item (dict): Media item from Kodi API
        session_id (str): Session ID for file naming
        downloaded_art (dict): Downloaded artwork files
        progress_data (dict): Playback progress information
        details (dict): Detailed media information
        
    Returns:
        str: HTML content for TV episode display
    """
    # Extract URLs for artwork
    # For TV episodes, 'poster' is typically the show poster, and we need to get season poster separately
    show_poster_url = f"/media/{downloaded_art.get('poster')}" if downloaded_art.get("poster") else ""
    season_poster_url = f"/media/{downloaded_art.get('season.poster')}" if downloaded_art.get("season.poster") else ""
    fanart_url = f"/media/{downloaded_art.get('fanart')}" if downloaded_art.get("fanart") else ""
    banner_url = f"/media/{downloaded_art.get('banner')}" if downloaded_art.get("banner") else ""
    clearlogo_url = f"/media/{downloaded_art.get('clearlogo')}" if downloaded_art.get("clearlogo") else ""
    clearart_url = f"/media/{downloaded_art.get('clearart')}" if downloaded_art.get("clearart") else ""
    
    # Extract TV episode information
    title = item.get("title", "Untitled Episode")
    show = item.get("showtitle", "")
    season = item.get("season", 0)
    episode = item.get("episode", 0)
    plot = item.get("plot", item.get("description", ""))
    
    # Create episode subtitle components for badges
    season_badge = f"Season {season}" if season > 0 else ""
    episode_badge = f"Episode {episode}" if episode > 0 else ""
    title_badge = title if title else ""
    
    # Extract IMDb ID and construct URL - ensure details is a dict
    if not isinstance(details, dict):
        details = {}
    imdb_id = details.get("uniqueid", {}).get("imdb", "")
    imdb_url = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else ""
    
    # Get rating from details or fallback
    rating = round(details.get("rating", 0.0), 1)
    rating_html = f"<strong>⭐ {rating}</strong>" if rating > 0 else ""
    
    # Initialize defaults
    director_names = "N/A"
    cast_names = "N/A"
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
    
    # HDR type
    hdr_type = video_info.get("hdrtype", "").upper() or "SDR"
    
    # Audio languages
    audio_languages = ", ".join(sorted(set(
        a.get("language", "")[:3].upper() for a in audio_info if a.get("language")
    ))) or "N/A"
    
    # Subtitle languages
    subtitle_languages = ", ".join(sorted(set(
        s.get("language", "")[:3].upper() for s in subtitle_info if s.get("language")
    ))) or "N/A"
    
    # Director - ensure details is a dict
    if not isinstance(details, dict):
        details = {}
    if "director" in details:
        director_list = details.get("director", [])
        if isinstance(director_list, list):
            director_names = ", ".join(director_list) or "N/A"
    
    # Cast - limit to top 10 actors
    cast_list = details.get("cast", [])
    if isinstance(cast_list, list) and cast_list:
        cast_names = ", ".join([c.get("name") for c in cast_list[:10] if isinstance(c, dict) and c.get("name")]) or "N/A"
    
    # Genre and formatting
    genre_list = details.get("genre", [])
    if not isinstance(genre_list, list):
        genre_list = []
    genres = [g.capitalize() for g in genre_list]
    genre_badges = genres[:3]
    
    # Format media info
    resolution = "Unknown"
    height = video_info.get("height", 0)
    if height >= 2160:
        resolution = "4K"
    elif height >= 1080:
        resolution = "1080p"
    elif height >= 720:
        resolution = "720p"
    
    video_codec = video_info.get("codec", "Unknown").upper()
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
          padding: 40px;
          backdrop-filter: blur(5px);
          box-shadow: 0 8px 32px rgba(0,0,0,0.8);
          display: flex;
          gap: 40px;
          color: white;
        }}
        .left-section {{
          display: flex;
          gap: 40px;
        }}
        .right-section {{
          display: flex;
          align-items: center;
          justify-content: center;
        }}
        .poster-container {{
          display: flex;
          flex-direction: column;
          gap: 20px;
          align-items: flex-start;
        }}
        .show-poster {{
          height: 300px;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.6);
          position: relative;
          z-index: 2;
        }}
        .season-poster {{
          height: 300px;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.6);
          position: relative;
          z-index: 2;
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
        .episode-badges {{
          display: flex;
          gap: 10px;
          margin: 10px 0;
          flex-wrap: wrap;
        }}
        .episode-badge {{
          background: #4caf50;
          color: white;
          padding: 8px 15px;
          border-radius: 25px;
          font-size: 1.0em;
          font-weight: bold;
          box-shadow: 0 3px 8px rgba(0,0,0,0.4);
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
          max-height: 400px;
          max-width: 300px;
        }}
        .episode-info {{
          margin-bottom: 20px;
        }}
        .episode-title {{
          font-size: 1.2em;
          font-weight: bold;
          margin-bottom: 5px;
        }}
        .show-title {{
          font-size: 1.5em;
          font-weight: bold;
          margin-bottom: 10px;
          color: #4caf50;
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
        <div class="left-section">
          <div class="poster-container">
            {f"<img class='show-poster' src='{show_poster_url}' />" if show_poster_url else ""}
            {f"<img class='season-poster' src='{season_poster_url}' />" if season_poster_url else ""}
          </div>
          <div>
            {f"<img class='logo' src='{clearlogo_url}' />" if clearlogo_url else (f"<img class='banner' src='{banner_url}' />" if banner_url else f"<h2 style='margin-bottom: 4px;'>📺 {show}</h2>")}
            
            <div class="episode-info">
              {f"<div class='show-title'>{show}</div>" if not clearlogo_url and not banner_url else ""}
              <div class="episode-badges">
                {f"<span class='badge episode-badge'>{season_badge}</span>" if season_badge else ""}
                {f"<span class='badge episode-badge'>{episode_badge}</span>" if episode_badge else ""}
                {f"<span class='badge episode-badge'>{title_badge}</span>" if title_badge else ""}
              </div>
            </div>
            
            {f"<p><strong>Director:</strong> {director_names}</p>" if director_names and director_names != "N/A" else ""}
            {f"<p><strong>Cast:</strong> {cast_names}</p>" if cast_names and cast_names != "N/A" else ""}
            {f"<h3 style='margin-top:20px;'>Plot</h3><p style='max-width:600px;'>{plot}</p>" if plot and plot.strip() else ""}
            <div class="badges">
              {rating_html}
              <a href="{imdb_url}" target="_blank" class="badge-imdb">
                <span>IMDb</span>
              </a>
              <span class="badge">{resolution}</span>
              <span class="badge">{video_codec}</span>
              <span class="badge">{audio_codec} {channels}ch</span>
              <span class="badge">HDR: {hdr_type}</span>
              <span class="badge">Audio: {audio_languages}</span>
              <span class="badge">Subs: {subtitle_languages}</span>
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
        <!-- Clearart removed as requested -->
      </div>
    </body>
    </html>
    """
    return html
