from calendar import c
from nextcord import AudioSource, ClientException
from nextcord.opus import Encoder
import subprocess
import shlex
import io

from utils.system import logger

class BytesIOFFmpegPCMAudio(AudioSource):
    def __init__(self, source, *, executable='ffmpeg', pipe=False, stderr=None, before_options : str = None, options : str = None):
        stdin = None if not pipe else source
        command = shlex.split(before_options) + [
            '-i',
            '-' if pipe else source, 
            '-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning',
        ]
        command.insert(0, executable)
        if options is not None: command.extend(shlex.split(options))
        command.append('pipe:1')

        logger.debug(f"FFmpeg command: {command}")

        self._process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
        self._stdout = io.BytesIO(self._process.communicate(input=stdin)[0])
    
    def read(self):
        ret = self._stdout.read(Encoder.FRAME_SIZE)
        return b'' if len(ret) != Encoder.FRAME_SIZE else ret
    
    def cleanup(self):
        proc = self._process
        
        if proc is None: return
        
        proc.kill()
       
        if proc.poll() is None: proc.communicate()

        self._process = None