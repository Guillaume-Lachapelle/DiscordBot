import os
import openai
from dotenv import load_dotenv

#region Constants

# Load environment variables
load_dotenv()

# Currently expired. Openai free trial is over...
openai.api_key = os.getenv('OPENAI_API_KEY')

#endregion


#region Commands

# Use the GPT-3 API to generate a response to a message
async def generate_response(message):
    try:
        model_engine = "davinci"
        prompt = (f"{message}\n")
        completions = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )
        message = completions.choices[0].text
        return message
    except Exception as e:
        return "Could not generate response. Please try again."

# Use the openai API to generate an image
async def generate_image(message):
    try:
        # Use DALL-E to generate the image
        response = openai.Image.create(
        model="image-alpha-001",
        prompt=message,
        )
        return response.data[0]['url']
    except Exception as e:
        return "Could not generate image. Please try again."
    
#endregion