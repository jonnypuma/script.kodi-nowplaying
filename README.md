Make sure Kodi has web control enabled

Create a folder kodi-nowplaying and put the doccker-compose.yml file and .env file (see below) in it.

Inside kodi-nowplaying, create another folder called nowplaying and place the rest of the files inside it, i.e. Dockerfile, favicon.ico, kodi-nowplaying.py, parser.py, episode_nowplaying.py, movie_nowplaying.py, music_nowplaying.py

Create an .env file and add this to it:
``xml
Kodi Nowplaying Credentials - replace with your credentials and Kodi IP and port no
KODI_HOST=http://KodiDeviceIP:port
KODI_USERNAME=YoutUsername
KODI_PASSWORD=YourPassword
``

_________________________
OPTIONAL: Create fallback and edit the kodi-nowplaying.py file and enter Kodi IP and user/pass there:
# Kodi connection details
KODI_HOST = os.getenv("KODI_HOST", "http://insert_ip:insert_port")

KODI_USER = os.getenv("KODI_USER", "insert_user")

KODI_PASS = os.getenv("KODI_PASS", "insert_pass")
_________________________

Build and start container:
docker compose up -d

Start playing media on your Kodi device

Test locally by visiting http://localhost:5001/nowplaying <- or replace localhost with the IP of the container host

Mount it as a custom Homarr iframe tile pointing to http://localhost:5001/nowplaying 






