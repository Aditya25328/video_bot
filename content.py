import re
import os
import requests
from datetime import datetime
import google.generativeai as genai  # Gemini import

# Configure the Gemini API key
genai.configure(api_key="gemini_api")

# Replace with your Eleven Labs API key
API_KEY = ""  # Enter your Eleven Labs API key here

# Endpoint for text-to-speech synthesis
url = "https://api.elevenlabs.io/v1/text-to-speech"

# Default voice ID for free-tier users
default_voice_id = "IKne3meq5aSn9XLyUdCD"  # Example voice ID; may vary

# Create the local_media directory if it doesn't exist
os.makedirs('local_media', exist_ok=True)

def generate_image_and_audio_prompts(prompt):
    """Generate image and audio prompts using the Gemini model."""
    try:
        # Request to the Gemini API
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(
            f"""will tell you : create 5 prompts for the image according the topic i give you and it should be in a storyline
            next create 5 prompts for the audio voice over for each image which is one liner with emotions the topic is "{prompt}" which motivates , cheers me up or calms me. The storyline should be realistic and user relatable. Store it in a python list format ["1,2,3"]. The audio prompt should be one long text for all combined related images, no need to mention the image no. in front of audio prompt. Just a simple long text combined for all the audio prompts. The text should not include anything in brackets or pauses, just a smooth narration that fits with the images you generated."""
        )

        # Debug: Print the raw response
        print("Raw API Response:", response.text)

        # Adjusting the regex to handle the string format better
        image_prompts_match = re.search(r'image_prompts\s*=\s*\[(.*?)\]', response.text, re.DOTALL)
        audio_prompt_match = re.search(r'audio_prompt\s*=\s*"(.*?)"', response.text, re.DOTALL)

        if image_prompts_match and audio_prompt_match:
            # Extract image prompts
            image_prompts_str = image_prompts_match.group(1).strip()
            image_prompts = eval(f"[{image_prompts_str}]")

            # Extract audio prompt
            audio_prompt = audio_prompt_match.group(1).strip()

            return image_prompts, audio_prompt
        else:
            raise ValueError("Image prompts or audio prompts not found in the response.")

    except Exception as e:
        print("Error in generate_image_and_audio_prompts:", e)
        return [], ""

def download_and_save_image(prompt, filename, width=1280, height=720, model='flux', seed=None):
    """Download and save an image from Pollinations AI."""
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&model={model}&seed={seed}"
        response = requests.get(url)
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                file.write(response.content)
            print(f"Image downloaded and saved as {filename}")
            return filename
        else:
            print(f"Failed to download image for prompt: {prompt} (Status Code: {response.status_code})")
    except Exception as e:
        print(f"Error downloading image for prompt '{prompt}': {e}")
        return None

def generate_audio_from_text(text):
    """Generate audio from text using Eleven Labs API."""
    try:
        # Function to split text into smaller chunks for Eleven Labs API
        def split_text(text, max_length=600):
            return [text[i:i + max_length] for i in range(0, len(text), max_length)]
        
        # Split the long audio text into smaller chunks
        chunks = split_text(text)

        # Headers for API request
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": API_KEY,
        }

        # Process each chunk and create audio files
        for i, text_chunk in enumerate(chunks, start=1):
            payload = {
                "text": text_chunk,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            # Send the POST request to Eleven Labs
            response = requests.post(f"{url}/{default_voice_id}", headers=headers, json=payload)
            
            if response.status_code == 200:
                # Save the audio to a file with a unique name for each chunk
                filename = f"local_media/output_audio_{i}.mp3"
                with open(filename, "wb") as file:
                    file.write(response.content)
                print(f"Audio file saved as {filename}")
            else:
                print(f"Error for chunk {i}: {response.status_code}, {response.text}")

    except Exception as e:
        print(f"Error generating audio: {e}")

# Main execution flow
if __name__ == "__main__":
    # Step 1: Get user input and generate image and audio prompts
    prompt_input = input("Enter a topic to generate prompts: ")
    image_prompts, audio_prompt = generate_image_and_audio_prompts(prompt_input)

    if image_prompts and audio_prompt:
        print(f"Generated Image Prompts: {image_prompts}")
        print(f"Generated Audio Prompt: {audio_prompt}")

        # Step 2: Use the generated image prompts to download and save images
        for i, prompt in enumerate(image_prompts):
            print(f"Processing prompt {i+1}: {prompt}")

            # Create a filename using timestamp and prompt
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_prompt = "".join(x for x in prompt[:30] if x.isalnum() or x in (' ', '-', '_')).strip()
            new_filename = f"local_media/{timestamp}_{clean_prompt}.png"

            download_and_save_image(prompt, new_filename, width=1280, height=720, model='flux', seed=42)

        # Step 3: Generate the audio from the combined audio prompt
        generate_audio_from_text(audio_prompt)

    else:
        print("No image or audio prompts were generated.")
