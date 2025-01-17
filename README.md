# Media Generation Script

This repository contains Python scripts for automating Instagram media handling and generating AI-based multimedia content. The scripts leverage APIs for functionality such as downloading/uploading Instagram videos, generating images based on text prompts, and creating audio narrations from text.

---

## Features

### Instagram Media Automation
1. **Video Download**: Automates downloading videos from Instagram using Playwright.
2. **Video Generation**: Uses Gemini AI for creating custom videos with provided inputs.

### AI-Based Multimedia Generation
1. **Generate Storyline Prompts**: Uses Gemini API to generate realistic, relatable image prompts and audio narrations based on a user-provided topic.
2. **AI-Generated Images**: Downloads AI-generated images for the prompts using Pollinations AI.
3. **Text-to-Speech Audio**: Generates MP3 audio files for narrations using Eleven Labs API.
4. **Save Media Locally**: Saves generated media files (images and audio) in the `local_media` folder.

---

## Requirements

- Python 3.7 or higher
- Libraries:
  - `re`
  - `os`
  - `requests`
  - `datetime`
  - `google.generativeai` (for Gemini API)
  - `playwright` (for Instagram automation)
- API Keys:
  - Gemini API Key
  - Eleven Labs API Key

---

## How It Works

### Instagram Automation
1. Configure your Instagram credentials in the script.
2. Use Playwright to automate logging in, downloading videos, and uploading content.
3. Generate or edit videos using Gemini AI.

### AI Multimedia Generation
1. Input a topic (e.g., "A journey of self-discovery") when prompted.
2. The Gemini API generates:
   - Five image prompts describing a storyline.
   - A combined audio prompt for narration.
3. Pollinations AI generates and downloads images for each prompt.
4. Eleven Labs API converts the audio prompt into MP3 audio files.

---

## Usage

1. **Set Up API Keys**:
   - Update `API_KEY` in the script with your Eleven Labs API key.
   - Configure the Gemini API key using `genai.configure(api_key="your_gemini_api_key")`.

2. **Run the Script**:
   ```bash
   python insta_script.py  # For Instagram automation
   python ai_script.py     # For multimedia generation
   ```

3. **Provide Input**:
   - Instagram Automation: Configure settings for downloading/uploading.
   - Multimedia Generation: Enter a topic for media creation.

4. **Check Outputs**:
   - Instagram videos will be downloaded/uploaded as configured.
   - Generated images and audio files will be saved in the `local_media` folder.

---

## Example Outputs

### Instagram Automation
- **Downloaded Videos**:
  Videos from Instagram saved locally.
- **Uploaded Content**:
  Videos uploaded to Instagram with customizable captions and tags.

### AI Multimedia Generation
- **Image Prompts**:
  ```
  ["A serene sunrise over a mountain valley", "A lone traveler walking along a forest trail", ...]
  ```
- **Audio Prompt**:
  ```
  "Imagine the calm of a mountain sunrise, the first light gently illuminating a peaceful valley..."
  ```
- **Generated Media**:
  - Images saved as PNG files.
  - Audio saved as MP3 files.

---

## Functionality Overview

### Instagram Automation
- **Download Videos**: Automates downloading videos from Instagram accounts or hashtags.
- **Upload Videos**: Automates uploading videos with captions and tags.

### AI Multimedia Generation
- **generate_image_and_audio_prompts(prompt)**:
  Generates image and audio prompts using Gemini's GenerativeModel API.

- **download_and_save_image(prompt, filename, width=1280, height=720, model='flux', seed=None)**:
  Downloads and saves an image based on a textual prompt.

- **generate_audio_from_text(text)**:
  Generates audio narration from the text using Eleven Labs API.

- **process_and_generate_media()**:
  Combines all steps:
  1. Takes user input.
  2. Generates and downloads media.
  3. Saves all outputs in the local directory.

---

## Folder Structure
```
.
├── main.py          # Instagram automation script
├── combined.py             # AI multimedia generation script
├── local_media/             # Folder for generated media
├── README.md                # Project documentation
├── requirement.txt          # dependecies    
└── multiimage.py            # for Ffmpeg
```

---

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Aditya25328/video_bot.git
   cd video_bot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright:
   ```bash
   playwright install
   ```

---


