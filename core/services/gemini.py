import dotenv, os
dotenv.load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

import google.generativeai as genai

genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

def generate_content(prompt):
    response = model.generate_content(prompt)
    return response.text

# response = model.generate_content("Explain how AI works")
# print(response.text)
