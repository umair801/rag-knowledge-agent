import os
from dotenv import load_dotenv
from openai import OpenAI
from langdetect import detect, LangDetectException
from app.models.schemas import TranslationRequest, TranslationResult

load_dotenv()

SUPPORTED_LANGUAGES = [
    "English", "French", "Spanish", "German", "Italian", "Portuguese",
    "Dutch", "Russian", "Chinese (Simplified)", "Chinese (Traditional)",
    "Japanese", "Korean", "Arabic", "Turkish", "Polish", "Swedish",
    "Norwegian", "Danish", "Finnish", "Hindi", "Urdu", "Persian",
    "Hebrew", "Indonesian", "Malay", "Thai", "Vietnamese", "Greek",
    "Czech", "Romanian", "Hungarian", "Ukrainian"
]

STYLE_INSTRUCTIONS = {
    "literary": (
        "Translate with a literary, expressive style. Preserve the author's voice, "
        "tone, and narrative rhythm. Prioritize naturalness and readability over "
        "word-for-word accuracy."
    ),
    "formal": (
        "Translate with a formal, professional style. Use precise vocabulary and "
        "maintain a neutral, authoritative tone throughout."
    ),
    "casual": (
        "Translate with a casual, conversational style. Use natural, everyday language "
        "as if speaking to a friend. Keep it light and readable."
    ),
}

QUALITY_THRESHOLD_RATIO = 0.3  # Flag if output is less than 30% length of input


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def translate_text(request: TranslationRequest) -> TranslationResult:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    style_instruction = STYLE_INSTRUCTIONS.get(
        request.style, STYLE_INSTRUCTIONS["literary"]
    )

    detected_language = detect_language(request.source_text)

    source_lang = request.source_language or detected_language

    system_prompt = (
        f"You are an expert literary translator. "
        f"{style_instruction} "
        f"Translate the following text from {source_lang} to {request.target_language}. "
        f"Return only the translated text. Do not include any explanations, "
        f"notes, or commentary."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.source_text},
        ],
        temperature=0.3,
    )

    translated_text = response.choices[0].message.content.strip()
    token_usage = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    # Quality flag: output suspiciously short relative to input
    input_len = len(request.source_text)
    output_len = len(translated_text)
    quality_flag = output_len < (input_len * QUALITY_THRESHOLD_RATIO)

    return TranslationResult(
        translated_text=translated_text,
        detected_source_language=detected_language,
        token_usage=token_usage,
        quality_flag=quality_flag,
    )