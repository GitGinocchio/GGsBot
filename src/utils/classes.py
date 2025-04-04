from nextcord import AudioSource, ClientException
from nextcord.opus import Encoder
import subprocess
import shlex
import io

class BytesIOFFmpegPCMAudio(AudioSource):
    def __init__(self, source, *, executable='ffmpeg', pipe=False, stderr=None, before_options=None, options=None):
        stdin = None if not pipe else source
        args = [
            executable, 
            before_options if before_options else '', 
            '-i', 
            '-' if pipe else source, 
            '-f', 's16le', '-ar', '48000', '-ac', '2', '-loglevel', 'warning',
            options if options else ''
            'pipe:1'
        ]
        self._process = None
        
        try:
            self._process = subprocess.Popen(' '.join(args), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
            self._stdout = io.BytesIO(self._process.communicate(input=stdin)[0])
        except FileNotFoundError:
            raise ClientException(executable + ' was not found.') from None
        except subprocess.SubprocessError as exc:
            raise ClientException('Popen failed: {0.__class__.__name__}: {0}'.format(exc)) from exc
    
    def read(self):
        ret = self._stdout.read(Encoder.FRAME_SIZE)
        return b'' if len(ret) != Encoder.FRAME_SIZE else ret
    
    def cleanup(self):
        proc = self._process
        
        if proc is None: return
        
        proc.kill()
       
        if proc.poll() is None: proc.communicate()

        self._process = None