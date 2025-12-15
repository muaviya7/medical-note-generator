from transformers import WhisperForConditionalGeneration
import ctranslate2
# 1️⃣ Load your Hugging Face model (medical fine-tuned)
model_name = "mahwizzzz/medwhishper"
hf_model = WhisperForConditionalGeneration.from_pretrained(model_name)

# 2️⃣ Export to ONNX (optional, recommended for big models)
# You can skip this for small/medium models and go directly to CTranslate2
# But CTranslate2 can convert from PyTorch directly

# 3️⃣ Convert to CTranslate2 format
ctranslate2.converters.convert_whisper(
    hf_model,
    output_dir="./medwhishper_ctranslate2",
    quantization="int8"  # optional: int8 for smaller size and faster inference
)

print("Conversion done! Model is ready for Faster-Whisper.")