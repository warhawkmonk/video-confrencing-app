import streamlit as st
from streamlit_webrtc import (
    webrtc_streamer,
    VideoProcessorBase,
    AudioProcessorBase,
    WebRtcMode,
)
import av
import threading
import numpy as np
from PIL import Image
import time
import base64
from io import BytesIO
import uuid
import wave


def get_new_uuid():
    # Generate a random UUID (UUID4) and convert it to a string
    return str(uuid.uuid4())


def numpy_image_to_base64(img_array, format="PNG"):
    pil_img = Image.fromarray(img_array)
    buff = BytesIO()
    pil_img.save(buff, format=format)
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    return img_str


def base64_to_image(base64_string):
    image_data = base64.b64decode(base64_string)
    image_buffer = BytesIO(image_data)
    img = Image.open(image_buffer)
    return img


def pcm_to_wav_base64(pcm_int16, sample_rate, channels, sample_width=2):
    """Pack an interleaved int16 numpy array into a WAV file and base64-encode it."""
    buff = BytesIO()
    with wave.open(buff, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_int16.astype(np.int16).tobytes())
    return base64.b64encode(buff.getvalue()).decode("utf-8")


def base64_to_wav_bytes(base64_string):
    return base64.b64decode(base64_string)


def get_ice_servers():
    return [{"urls": ["stun:stun.l.google.com:19302"]}]


# Initialize session state keys if not present
if "current_image" not in st.session_state:
    st.session_state["current_image"] = None
if "on" not in st.session_state:
    st.session_state["on"] = False
if "new_id" not in st.session_state:
    st.session_state["new_id"] = get_new_uuid()


class VideoTransformer(VideoProcessorBase):
    def __init__(self, params):
        self.frame_lock = threading.Lock()
        self.params = params
        self.buffer_size = 2
        self.frame_buffer = [None] * self.buffer_size
        self.cv = 0  # Circular buffer index

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        with self.frame_lock:
            self.frame_buffer[self.cv] = img
            self.cv = (self.cv + 1) % self.buffer_size
            self.params["current_image"] = img
        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def get_latest_frame(self) -> np.ndarray:
        with self.frame_lock:
            idx = (self.cv - 1) % self.buffer_size
            return self.frame_buffer[idx]


class AudioTransformer(AudioProcessorBase):
    """
    Buffers incoming mic audio frames in a rolling window and lets the main
    thread pull out ~1 second chunks, the same way VideoTransformer exposes
    the latest video frame. Audio frames from aiortc are int16 PCM, so we
    just concatenate them and periodically flush to a WAV chunk.
    """

    def __init__(self):
        self.audio_lock = threading.Lock()
        self.chunks = []
        self.sample_rate = None
        self.channels = None
        self.samples_collected = 0
        self.target_samples = None  # ~1 second worth, set once sample_rate is known

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray()  # shape (channels, samples) for planar s16

        with self.audio_lock:
            if self.sample_rate is None:
                self.sample_rate = frame.sample_rate
                self.channels = len(frame.layout.channels)
                self.target_samples = self.sample_rate  # flush roughly every 1s

            # Flatten to interleaved int16 regardless of planar/packed shape
            interleaved = pcm.T.reshape(-1) if pcm.ndim == 2 else pcm.reshape(-1)
            self.chunks.append(interleaved.astype(np.int16))
            self.samples_collected += interleaved.shape[0] // max(self.channels, 1)

        return frame

    def get_and_clear_chunk(self):
        """Returns (pcm_int16, sample_rate, channels) once ~1s is buffered, else None."""
        with self.audio_lock:
            if not self.chunks or self.target_samples is None:
                return None
            if self.samples_collected < self.target_samples:
                return None
            pcm = np.concatenate(self.chunks)
            self.chunks = []
            self.samples_collected = 0
            return pcm, self.sample_rate, self.channels


col1, col2 = st.columns(2)

with col1:
    st.code(st.session_state["new_id"])

    ctx = webrtc_streamer(
        key="example",
        video_processor_factory=lambda: VideoTransformer(st.session_state),
        audio_processor_factory=AudioTransformer,
        media_stream_constraints={"video": True, "audio": True},
        async_processing=True,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
    )

with col2:
    text_value = st.text_area(label="Add room id", placeholder="please paste id")
    toggle = st.button("Toggle Frame Display")

    if toggle:
        st.session_state["on"] = not st.session_state["on"]

    image_placeholder = st.empty()
    audio_placeholder = st.empty()
    element = []

    if ctx.video_processor and st.session_state["on"]:

        while True:

            # ---- write our own video frame (unchanged) ----
            frame = ctx.video_processor.get_latest_frame()
            if frame is not None:
                value = numpy_image_to_base64(frame)
                with open("image_saver_folder/" + st.session_state["new_id"] + ".txt", "w") as write:
                    write.write(value)

            # ---- write our own audio chunk ----
            if ctx.audio_processor:
                chunk = ctx.audio_processor.get_and_clear_chunk()
                if chunk is not None:
                    pcm, sample_rate, channels = chunk
                    wav_b64 = pcm_to_wav_base64(pcm, sample_rate, channels)
                    with open("image_saver_folder/" + st.session_state["new_id"] + "_audio.txt", "w") as write:
                        write.write(wav_b64)

            # ---- read + display the remote video ----
            try:
                with open("image_saver_folder/" + text_value + ".txt") as read:
                    temp = str(read.read())
                img = base64_to_image(temp)
                img = np.array(img)
                img = img[:, :, ::-1]
                element.append(img)
                image_placeholder.image(img, channels="RGB")
            except Exception:
                pass

            # ---- read + play the remote audio ----
            try:
                with open("image_saver_folder/" + text_value + "_audio.txt") as read:
                    audio_b64 = str(read.read())
                wav_bytes = base64_to_wav_bytes(audio_b64)
                audio_placeholder.audio(wav_bytes, format="audio/wav")
            except Exception:
                pass

    else:
        image_placeholder.text("Click 'Toggle Frame Display' to start showing frames.")
