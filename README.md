# Video Conferencing App

A lightweight video and audio conferencing prototype built with [Streamlit](https://streamlit.io/)
and [`streamlit-webrtc`](https://github.com/whitphx/streamlit-webrtc). Each browser session receives
a UUID that acts as its room identifier. The app captures camera frames and microphone audio, then
uses files in `image_saver_folder` to exchange the latest available media with another session.

This project is intended for learning and local experimentation. It is not a production-ready
conferencing service.

## Features

- Camera and microphone capture in the browser
- Automatic UUID generation for each session
- Participant connection by pasting a session ID
- Toggle-controlled frame and audio publishing
- Video frames saved as Base64-encoded PNG data
- Audio saved as approximately one-second Base64-encoded WAV chunks

## Requirements

- Python 3.9 or newer
- A browser with camera and microphone support
- Camera and microphone permissions for the app
- A writable `image_saver_folder` directory

## Installation

Create a virtual environment and install the dependencies:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the App

From the project directory, start Streamlit:

```bash
streamlit run app.py
```

Open the URL printed in the terminal, usually `http://localhost:8501`.

## Connect Two Sessions

1. Open the app in two browser tabs or on two devices.
2. Allow camera and microphone access when prompted.
3. In the first session, copy the UUID shown in the left column.
4. In the second session, paste that UUID into **Add room id**.
5. Start the WebRTC stream in both sessions.
6. Click **Toggle Frame Display** in the session that should publish and display media.

The receiving session reads the sender's latest files from the shared storage directory. Both
sessions must use the same `image_saver_folder`; this works automatically for local tabs, but a
multi-machine deployment needs shared storage accessible to every app instance.

## Data Exchange

For a session ID such as `<session-id>`, the app writes:

```text
image_saver_folder/<session-id>.txt
image_saver_folder/<session-id>_audio.txt
```

The first file contains the latest video frame as Base64 PNG data. The second contains the latest
audio chunk as Base64 WAV data. Files are overwritten as new media arrives.

## Project Structure

```text
.
├── app.py                  Streamlit UI and WebRTC processors
├── requirements.txt        Python dependencies
├── README.md               Project documentation
└── image_saver_folder/     Runtime media exchange files
```

## Troubleshooting

**The camera or microphone does not start**

- Check browser permissions for the app URL.
- Confirm that another application is not using the camera or microphone.
- Restart the WebRTC stream after changing permissions.

**No remote media appears**

- Confirm that the pasted ID is complete and matches the other session's displayed UUID.
- Make sure both sessions can read and write the same `image_saver_folder`.
- Click **Toggle Frame Display** after the WebRTC stream is active.

**WebRTC fails outside localhost**

Use HTTPS when hosting the app remotely. The app currently uses Google's public STUN server;
networks with restrictive NAT or firewalls may also require a TURN server configuration in `app.py`.

## Limitations and Security

- UUIDs are identifiers, not authentication or access control.
- Media is stored as readable Base64 text files and should be treated as sensitive.
- Files are not automatically expired or deleted.
- The implementation exchanges the latest frame and audio chunk, not a synchronized continuous call.
- The current storage approach is not suitable for public or multi-tenant production use.

Before deploying publicly, add authenticated signaling, encrypted and managed media storage, cleanup
policies, TURN infrastructure, and a proper room lifecycle.

## License

No license has been specified for this project.
