import gradio as gr
import torch
from audiocraft.models import MusicGen, AudioGen
import os
import numpy as np
import soundfile as sf
import tempfile
import zipfile
from typing import List


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# По умолчанию: музыка (MusicGen small); для эффектов используем AudioGen medium
MUSIC_MODEL_ID = "facebook/musicgen-small"
SFX_MODEL_ID = "facebook/audiogen-medium"


def load_music_model(model_id: str = MUSIC_MODEL_ID):
    model = MusicGen.get_pretrained(model_id)
    if DEVICE == "cuda":
        model = model.to(DEVICE)
    model.set_generation_params(duration=8, top_k=250, top_p=0.0, temperature=1.0, cfg_coef=3.0)
    return model


def load_sfx_model(model_id: str = SFX_MODEL_ID):
    model = AudioGen.get_pretrained(model_id)
    if DEVICE == "cuda":
        model = model.to(DEVICE)
    model.set_generation_params(duration=8, top_k=250, top_p=0.0, temperature=1.0, cfg_coef=3.0)
    return model


music_model = load_music_model()
_sfx_model = None  # лениво загрузим при первом вызове


def _tensor_to_wav_path(audio_tensor: torch.Tensor, sample_rate: int) -> str:
    audio = audio_tensor.detach().cpu().float().numpy()
    if audio.ndim == 2:
        if audio.shape[0] <= 4 and audio.shape[1] > audio.shape[0]:
            audio = audio.T
    elif audio.ndim > 2:
        audio = np.squeeze(audio)
        if audio.ndim == 2 and audio.shape[0] <= 4:
            audio = audio.T
    max_abs = np.max(np.abs(audio)) if np.size(audio) else 1.0
    if max_abs > 1.0:
        audio = audio / max_abs
    audio = np.clip(audio, -1.0, 1.0)
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(path, audio, sample_rate, subtype="PCM_16")
    return path


def generate_audio(prompt: str, duration: float, seed: int, model_size: str, task: str, layers: int):
    # task: "music" | "sfx"
    torch.manual_seed(int(seed))

    if task == "sfx":
        global _sfx_model
        if _sfx_model is None:
            _sfx_model = load_sfx_model()
        _sfx_model.set_generation_params(duration=float(duration))
        paths: List[str] = []
        for i in range(max(1, int(layers))):
            torch.manual_seed(int(seed) + i)
            with torch.no_grad():
                wav = _sfx_model.generate(descriptions=[prompt], progress=False)
            paths.append(_tensor_to_wav_path(wav[0], _sfx_model.sample_rate))
        # упаковка в ZIP
        zfd, zpath = tempfile.mkstemp(suffix=".zip")
        os.close(zfd)
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for idx, p in enumerate(paths, 1):
                zf.write(p, arcname=f"layer_{idx}.wav")
        return zpath

    # music
    target_model = music_model
    if model_size == "medium":
        target_model = load_music_model("facebook/musicgen-medium")
    elif model_size == "small":
        target_model = load_music_model("facebook/musicgen-small")

    target_model.set_generation_params(duration=float(duration))
    with torch.no_grad():
        wav = target_model.generate(descriptions=[prompt], progress=False)
    return _tensor_to_wav_path(wav[0], target_model.sample_rate)


iface = gr.Interface(
    fn=generate_audio,
    inputs=[
        gr.Textbox(label="Промпт", value="Create a realistic ambient soundscape of an office."),
        gr.Slider(2, 20, value=8, step=1, label="Длительность (сек)"),
        gr.Number(value=0, precision=0, label="Seed"),
        gr.Dropdown(choices=["small", "medium"], value="small", label="Размер модели (Music)"),
        gr.Dropdown(choices=["music", "sfx"], value="music", label="Тип задачи"),
        gr.Slider(1, 6, value=4, step=1, label="Число слоёв (для SFX)"),
    ],
    outputs=gr.File(label="Результат: WAV или ZIP"),
    title="AudioCraft demo: MusicGen & AudioGen",
    description=(
        "MusicGen генерирует музыкальные треки. AudioGen генерирует звуковые эффекты.\n"
        "Для SFX возвращается ZIP с 3–4 слоями."
    ),
)


if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)), share=True, show_api=False)


