Make sure Kodi has web control enabled

Kodi Nowplaying Credentials - in the .env file replace with your credentials and Kodi IP and port no
``
KODI_HOST=http://KodiDeviceIP:port
KODI_USERNAME=YoutUsername
KODI_PASSWORD=YourPassword
``

OPTIONAL: Create fallback and edit the kodi-nowplaying.py file and enter Kodi IP and user/pass there:
# Kodi connection details
``
KODI_HOST = os.getenv("KODI_HOST", "http://your_Kodi_IP:port")
KODI_USER = os.getenv("KODI_USER", "your_Kodi_username")
KODI_PASS = os.getenv("KODI_PASS", "your_Kodi_password")
``
Build and start container:
docker compose build --no-cache kodi-nowplaying
docker compose up -d

Start playing media on your Kodi device

Test locally by visiting http://localhost:5001/nowplaying <- or replace localhost with the IP of the container host


Mount it as a custom Homarr iframe tile pointing to http://localhost:5001/nowplaying 

