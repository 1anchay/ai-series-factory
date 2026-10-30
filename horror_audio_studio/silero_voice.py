"""Reliable OFFLINE Silero v5.6 Aidar for episode production.
Use "tts_text" in an episode scene to correct phonetics without editing captions.
The '+' character must be inserted before the stressed vowel, e.g. "зам+ок".
"""
from pathlib import Path
import numpy as np
import torch

SR=48000
MODEL=Path("/tmp/v5_6_ru.pt")
URL="https://models.silero.ai/models/tts/ru/v5_6_ru.pt"

class AidarVoice:
    def __init__(self):
        torch.set_num_threads(3)
        if not MODEL.exists():
            torch.hub.download_url_to_file(URL,str(MODEL),progress=False)
        if MODEL.stat().st_size<15_000_000:
            raise RuntimeError("Official Silero Aidar model download incomplete")
        self.model=torch.package.PackageImporter(str(MODEL)).load_pickle("tts_models","model")
        self.model.to(torch.device("cpu"))
        self.model.eval() if hasattr(self.model,"eval") else None

    def speak(self,scene,output_rate=24000):
        text=scene.get("tts_text") or scene["text"]
        # Silence/pauses should be driven through punctuation or explicit
        # sentence boundaries, not by distorting pitch after synthesis.
        with torch.inference_mode():
            if scene.get("ssml_text"):
                a=self.model.apply_tts(ssml_text=scene["ssml_text"],speaker="aidar",sample_rate=SR)
            else:
                a=self.model.apply_tts(text=text,speaker="aidar",sample_rate=SR)
        x=np.asarray(a.detach().cpu().numpy() if hasattr(a,"detach") else a,dtype=np.float32)
        if len(x)<SR//3 or not np.all(np.isfinite(x)):
            raise RuntimeError("Aidar returned empty or corrupt audio")
        if output_rate==SR:return x
        from scipy.signal import resample_poly
        return resample_poly(x,output_rate,SR).astype(np.float32)
