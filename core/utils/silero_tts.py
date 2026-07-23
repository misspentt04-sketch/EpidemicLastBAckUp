from pydub import AudioSegment

import torchaudio
import torch
import os
import io


class SileroTTS:
    def __init__(self):
        self.local_file = 'model.pt'
        self.device = torch.device('cpu')
        torch.set_num_threads(4)
        self.model = self.load_model()
        self.sample_rate = 48000
        self.speaker = 'baya'

    def load_model(self):
        if not os.path.isfile(self.local_file):
            torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt',
                                         self.local_file)
        model = torch.package.PackageImporter(self.local_file).load_pickle("tts_models", "model")
        model.to(self.device)
        return model

    def convert_ogg_to_opus(self, audio_buffer: io.BytesIO) -> io.BytesIO:
        audio_buffer.seek(0)
        audio = AudioSegment.from_file(audio_buffer, format='ogg')
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format='ogg', codec='libopus')
        output_buffer.seek(0)
        return output_buffer

    def generate_audio(self, text: str, speaker: str | None = 'baya') -> io.BytesIO:
        if not speaker:
            speaker = 'baya'
        
        audio = self.model.apply_tts(
            text=text,
            speaker=speaker,
            sample_rate=self.sample_rate
        )
        
        if audio.dim() == 1:
            audio = audio.unsqueeze(0).repeat(2, 1)
        
        buffer = io.BytesIO()
        torchaudio.save(buffer, audio, self.sample_rate, format='ogg', backend='soundfile')
        buffer.seek(0)
        
        final_buffer = self.convert_ogg_to_opus(buffer)
        return final_buffer
    
    def names_converter_to_model(self, name: str) -> str:
        names = {
            'мия': 'baya',
            'ксю': 'kseniya',
            'ксена': 'xenia',
            'миша': 'aidar',
            'гена': 'eugene',
            'женя': 'eugene',
        }
        return names.get(name.lower(), 'baya')

silero = SileroTTS()