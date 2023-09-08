# PrintWatchAI_Backend
Backend component for PrintWatchAI Plugin for Duet This backend monitors the webcam stream on any RepRapFirmware printer for spaghetti type defects. It can work with any camera that is accessible via an IP address/HTTP endpoint.

## Installation
This Backend component can be installed on any Linux device. Please follow the steps below for your device:

### Raspberry Pi
1. SSH into the Raspberry Pi and navigate to the root directory of the user
```
cd /home/pi
```
2. Download this repository's release for Raspberry Pi
```
wget https://github.com/printpal-io/PrintWatchAI_Backend/archive/refs/tags/raspberrypi.zip
```
3. Unzip the file
```
unzip raspberrypi.zip && rm raspberrypi.zip
```
4.Change directories
```
cd PrintWatchAI_Backend-raspberrypi
```
5. Reload the systemctl daemo
```
sudo systemctl daemon-reload
```
5. Enable the systemctl process for PrintWatch
```
sudo systemctl enable /home/pi/PrintWatchAI_Backend-raspberry/printwatch.service
```
6. Start the systemctl process for PrintWatch
```
sudo systemctl start printwatch.service
```
7. Validate the printwatch process is running
```
sudo journalctl -u printwatch
```
Outputs:
```
Sep 08 23:35:24 pi systemd[1]: Started PrintWatch AI.
Sep 08 23:35:28 pi python3[2237]: INFO:     Started server process [2237]
Sep 08 23:35:28 pi python3[2237]: INFO:     Waiting for application startup.
Sep 08 23:35:28 pi python3[2237]: INFO:     Application startup complete.
Sep 08 23:35:28 pi python3[2237]: INFO:     Uvicorn running on http://0.0.0.0:8989 (Press CTRL+C to quit)
```

### Orange Pi
1. SSH into the Orange Pi and navigate to the root directory of the user
```
cd /home/orangepi
```
2. Download this repository's release for Orange Pi
```
wget https://github.com/printpal-io/PrintWatchAI_Backend/archive/refs/tags/orangepi.zip
```
3. Unzip the file
```
unzip orangepi.zip && rm orangepi.zip
```
4.Change directories
```
cd PrintWatchAI_Backend-orangepi
```
5. Reload the systemctl daemo
```
sudo systemctl daemon-reload
```
5. Enable the systemctl process for PrintWatch
```
sudo systemctl enable /home/orangepi/PrintWatchAI_Backend-orangepi/printwatch.service
```
6. Start the systemctl process for PrintWatch
```
sudo systemctl start printwatch.service
```
7. Validate the printwatch process is running
```
sudo journalctl -u printwatch
```
Outputs:
```
Sep 08 23:35:24 orangepi systemd[1]: Started PrintWatch AI.
Sep 08 23:35:28 orangepi python3[2237]: INFO:     Started server process [2237]
Sep 08 23:35:28 orangepi python3[2237]: INFO:     Waiting for application startup.
Sep 08 23:35:28 orangepi python3[2237]: INFO:     Application startup complete.
Sep 08 23:35:28 orangepi python3[2237]: INFO:     Uvicorn running on http://0.0.0.0:8989 (Press CTRL+C to quit)
```

## Usage
**Getting started with the plugin.**
  1. Go to the plugin tab by navigating the side panel **Plugins -> PrintWatch AI**
  2. Enable the plugin by clicking the **Enable Monitoring** button
  3. In the PrintWatch AI plugin page, navigate to the **Settings** tab.
  4. Obtain your API key and enter it into the **API key** field. Navigate to the [WebApp](https://app.printpal.io) and create a Free account:
      1. Click 'Sign Up'
      2. Enter desired credentials
      3. Verify account with code sent via email
      4. Log into the WebApp and navigate to **Account -> Settings** and copy the **API key** value. Paste this value into the **API key** field in the Duet plugin
  5. For the Webcam URL input, enter the HTTP url at which the static image of the IP camera can be found. If using [Motion](https://plugins.duet3d.com/plugins/MotionWebcamServerPlugin.html) to handle the webcam streaming, this value will be: `http://<ip_address>:<port>/<camera_number>/current`. If configured using default settings with the Motion Plugin, this will be:  `http://localhost:8081/0/current`
