from pytube import YouTube, Playlist
from youtubesearchpython import VideosSearch, PlaylistsSearch
from moviepy.editor import AudioFileClip
import io
import sounddevice as sd
import numpy as np
import soundfile as sf

# Use moviepy to convert an mp4 to an mp3 with metadata support. Delete mp4 afterwards
#audio_clip = AudioFileClip(file_path)

#filelike = io.BytesIO()
#audio_clip.write_audiofile(filelike)


filelike = io.BytesIO()
yt = YouTube(url='https://www.youtube.com/watch?v=2jCjNv1bscw&pp=ygUHY2Fuem9uaQ%3D%3D')
#stream = yt.streams.get_audio_only()
video = yt.streams.filter(only_audio=True).get_audio_only()
video.stream_to_buffer(filelike)
filelike.seek(0)

#print(filelike.read())
