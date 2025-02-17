#
# INSPECTION ONLY
# DO NOT RUN THIS !
#
from google.generativeai.generative_models import ChatSession, GenerativeModel
from google.generativeai.protos import Content, GenerateContentResponse

# Response
GenerateContentResponse(
    done=True,
    iterator=None,
    result=GenerateContentResponse(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Hey there!  ... What's up?\n"}],
                        "role": "model",
                    },
                    "finish_reason": "STOP",
                    "avg_logprobs": -0.2533897202590416,
                }
            ],
            "usage_metadata": {
                "prompt_token_count": 66,
                "candidates_token_count": 58,
                "total_token_count": 124,
            },
            "model_version": "gemini-1.5-flash",
        }
    ),
)

# Session
ChatSession(
    model=GenerativeModel(
        model_name="models/gemini-1.5-flash",
        generation_config={},
        safety_settings={},
        tools=None,
        system_instruction="u're 'activa' an ai bot that acts as real discord server member.",
        cached_content=None,
    ),
    history=[
        Content({"parts": [{"text": "Context of c...: i luv u too"}], "role": "user"}),
        Content({"parts": [{"text": "what's ur name?"}], "role": "user"}),
        Content({"parts": [{"text": "Hey there!  ... What's up?\n"}], "role": "model"}),
        Content({"parts": [{"text": "what does ur name means?"}], "role": "user"}),
        Content({"parts": [{"text": '"Activa" is ... your name?\n'}], "role": "model"}),
    ],
)
