---
title: Video Call
emoji: "📹"
colorFrom: red
colorTo: orange
tags:
- streamlit
- webrtc
- video-call
pinned: false
short_description: A lightweight Streamlit video and audio calling prototype
---

# Video Call

A lightweight video and audio calling prototype built with **Streamlit**, **WebRTC**, and `aiortc`.
The app captures media from the browser, assigns each session a unique room ID, and uses shared file
storage to exchange the latest video frame and short audio clips between participants.

> This is a prototype for experimentation and local or shared-storage deployments. It is not intended
> to provide production-grade signaling, authentication, encryption, persistence, or call management.

## Features

- Browser camera and microphone access through `streamlit-webrtc`
- Automatic UUID generation for each session
- Room-style connection using a pasted participant ID
- Live frame display controlled by a toggle
- Approximately one-second audio chunks encoded as WAV

## How It Works

1. Open the app in a browser and allow camera and microphone access.
2. Copy the room ID shown in the left column.
3. Share that ID with the other participant.
4. The other participant pastes the ID into **Add room id**.
5. Select **Toggle Frame Display** to begin writing and displaying media.

Each session writes files named after its UUID into `image_saver_folder`:

```text
<room-id>.txt          latest video frame as Base64 PNG
<room-id>_audio.txt    latest audio chunk as Base64 WAV
```

For two users to exchange media, both app sessions must be able to read and write the same
`image_saver_folder`. A shared filesystem is therefore required when the app is deployed across
multiple containers or machines.

## Run Locally

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start Streamlit

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Browser and Network Requirements

- Camera and microphone permissions must be granted to the browser.
- WebRTC generally requires HTTPS outside `localhost`.
- The app uses Google’s public STUN server at `stun:stun.l.google.com:19302`.
- Restrictive networks may require a TURN server; update the ICE configuration in `app.py` for that
	scenario.
- The deployed environment must provide writable storage for `image_saver_folder`.

## Project Structure

```text
.
├── app.py                  Streamlit UI and WebRTC media processors
├── requirements.txt        Python dependencies
└── image_saver_folder/     Runtime media exchange files
```

## Limitations and Security Notes

- Room IDs are UUIDs, but there is no authentication or access control.
- Media is stored as Base64 text files and should be treated as sensitive temporary data.
- Files are not automatically expired or deleted.
- The current implementation exchanges the latest available frame and audio chunk rather than a
	synchronized, continuous media stream.
- Do not expose this prototype publicly without adding authenticated signaling, secure storage,
	cleanup policies, and appropriate WebRTC infrastructure.

## License

No license has been specified for this project.
