Make sure Kodi has web control enabled

Edit the docker compose with your Kodi device's IP and HTTP port
Edit Kodi HTTP access username and password

Build and start container:
docker compose up -d

Start playing media on your Kodi device

Test locally by visiting http://localhost:5001/nowplaying <- or replace localhost with the IP of the container host

Mount it as a custom Homarr iframe tile pointing to http://localhost:5001/nowplaying 


