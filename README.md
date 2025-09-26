Make sure Kodi has web control enabled

Unzip script.kodi-nowplaying.zip 

Edit the .env file and input the ip to your Kodi device, HTTP port and user/pass.

_________________________
OPTIONAL: Create fallback and edit the kodi-nowplaying.py file and enter Kodi IP and user/pass there:
# Kodi connection details
```
KODI_HOST = os.getenv("KODI_HOST", "http://insert_ip:insert_port")

KODI_USER = os.getenv("KODI_USER", "insert_user")

KODI_PASS = os.getenv("KODI_PASS", "insert_pass")
```
_________________________

Build and start container:
```docker compose up -d```

Start playing media on your Kodi device

Test locally by visiting http://localhost:5001/nowplaying <- or replace localhost with the IP of the container host

Mount it as a custom Homarr iframe tile pointing to http://localhost:5001/nowplaying 


<img width="1277" height="707" alt="image" src="https://github.com/user-attachments/assets/5c01b5b1-9077-42f8-9017-07d235210719" />









