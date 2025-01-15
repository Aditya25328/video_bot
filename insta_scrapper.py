import logging
import asyncio
import aiohttp
from playwright.async_api import async_playwright
from instaloader import Instaloader, Post
from dotenv import load_dotenv
import google.generativeai as genai
import os
import sys
import shutil
import json
import re
import subprocess

# Load environment variables
load_dotenv()
FLIC_TOKEN = os.getenv('FLIC_TOKEN')

if not FLIC_TOKEN:
    raise Exception("FLIC_TOKEN is not set in the environment. Check your .env file or environment variables.")

# Configure logging
logging.basicConfig(filename='relevant_urls.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Function to log in to Instagram
async def login_to_instagram(page):
    """
    Log in to Instagram using the provided credentials.
    """
    await page.goto("https://www.instagram.com/accounts/login/")
    await page.fill('input[name="username"]', "your_username")  # Replace with your username
    await page.fill('input[name="password"]', "your_password")  # Replace with your password
    await page.click("button[type='submit']")
    await page.wait_for_load_state("networkidle")
    print("Logged in successfully.")

# Function to scroll down the page
async def scroll_down(page):
    """
    Scroll down the page to load more posts.
    """
    for _ in range(5):  # Scroll 5 times to load content
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

async def fetch_instagram_post_urls(hashtag: str):
    """
    Fetch posts from Instagram for a specific hashtag and save their URLs.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await login_to_instagram(page)

        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        await page.goto(url)
        await scroll_down(page)
        await page.wait_for_selector('a[href*="/p/"]', timeout=60000)

        posts = await page.query_selector_all('a[href*="/p/"]')
        saved_urls = []

        for post in posts[:20]:  # Limit to 20 posts
            try:
                link = await post.get_attribute('href')
                if not link:
                    continue

                # Open the post in popup mode
                await post.click()
                await asyncio.sleep(2)

                # Save the post URL
                full_url = f"https://www.instagram.com{link}"
                saved_urls.append(full_url)
                logging.info(f"Saved URL: {full_url}")
                print(f"Saved URL: {full_url}")

                # Close the post dialog
                close_button = await page.query_selector('div[role="dialog"] button[aria-label="Close"]')
                if close_button:
                    await close_button.click()

            except Exception as e:
                print(f"Error processing post: {e}")
                continue

        await browser.close()
        return saved_urls

def generate_hashtag_from_prompt(prompt: str) -> str:
    """
    Generate a hashtag based on the provided prompt using the Gemini model.
    """
    genai.configure(api_key="gemini_api_key")  # Provide your Gemini API key
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Generate content
    response = model.generate_content(f"Create one most relevant Instagram hashtag for the following prompt: '{prompt}' which cheers me up or motivate or calm me down which is only one word")
    hashtag = response.text.strip()
    return hashtag

def extract_shortcode(url: str) -> str:
    """
    Extract the shortcode from an Instagram URL (whether it's a post or reel).
    """
    try:
        if 'reel/' in url:
            shortcode = url.split('reel/')[1].split('/')[0]
        elif 'reels/' in url:
            shortcode = url.split('reels/')[1].split('/')[0]
        elif '/p/' in url:
            shortcode = url.split('/p/')[1].split('/')[0]
        else:
            raise ValueError("Invalid Instagram URL format.")
        return shortcode
    except IndexError:
        raise ValueError("Unable to extract shortcode. Check the URL format.")

async def download_from_instagram(url: str) -> None:
    """
    Download an Instagram post (image or video) given its URL and save it to the 'media' directory.
    """
    il = Instaloader()
    shortcode = extract_shortcode(url)
    post = Post.from_shortcode(il.context, shortcode)

    os.makedirs('media', exist_ok=True)

    if post.is_video:
        il.download_post(post, target='media')
    else:
        post_url = post.url
        async with aiohttp.ClientSession() as session:
            async with session.get(post_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    with open(f"media/{shortcode}.jpg", "wb") as f:
                        f.write(image_data)

    title = post.caption if post.caption else "Untitled Post"

    with open(f"media/{shortcode}.txt", 'w', encoding='utf-8') as title_file:
        title_file.write(title)

    for file in os.listdir('media'):
        if not file.endswith('.mp4') and not file.endswith('.jpg') and not file.endswith('.txt'):
            os.remove(os.path.join('media', file))

async def generate_upload_url() -> dict:
    """
    Generate a pre-signed upload URL from the API.
    """
    endpoint = 'https://api.socialverseapp.com/posts/generate-upload-url'
    headers = {
        'Flic-Token': FLIC_TOKEN,
        'Content-Type': 'application/json'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to generate upload URL: {response.status}, {await response.text()}")

async def upload_media_to_url(upload_url: str, file_path: str) -> None:
    """
    Upload the media file to the server using the pre-signed URL.
    """
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as file:
            async with session.put(upload_url, data=file) as response:
                if response.status != 200:
                    raise Exception(f"Failed to upload media: {response.status}, {await response.text()}")

async def create_post(hash_value: str, title: str, category_id: int = 69) -> None:
    """
    Create a post on the Socialverse platform using the media hash.
    """
    endpoint = 'https://api.socialverseapp.com/posts'
    headers = {
        'Flic-Token': FLIC_TOKEN,
        'Content-Type': 'application/json'
    }
    body = {
        "title": title,
        "hash": hash_value,
        "is_available_in_public_feed": False,
        "category_id": category_id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, headers=headers, json=body) as response:
            if response.status != 200:
                raise Exception(f"Failed to create post: {response.status}, {await response.text()}")

async def process_media_url(url: str) -> None:
    """
    End-to-end process: download, upload, and create a post for an Instagram post.
    """
    print(f"Processing URL: {url}")
    await download_from_instagram(url)

    media_files = [file for file in os.listdir('media') if file.endswith('.mp4') or file.endswith('.jpg')]
    if not media_files:
        raise Exception("No media file found in 'media' directory.")
    media_file_path = os.path.join('media', media_files[0])

    upload_data = await generate_upload_url()
    upload_url = upload_data['url']
    hash_value = upload_data['hash']

    await upload_media_to_url(upload_url, media_file_path)

    title_file = [file for file in os.listdir('media') if file.endswith('.txt')]
    if not title_file:
        raise Exception("No title file found in 'media' directory.")
    
    with open(os.path.join('media', title_file[0]), 'r', encoding='utf-8') as f:
        title = f.read()

    await create_post(hash_value, title)
    print(f"Process completed successfully for {url}: Media uploaded and post created.")

async def process_post(url: str) -> None:
    """
    Process the Instagram post by downloading it and saving the media and metadata locally.
    """
    await download_from_instagram(url)

    media_files = [file for file in os.listdir('media') if file.endswith('.mp4') or file.endswith('.jpg')]
    if not media_files:
        raise Exception("No media file found in 'media' directory.")
    media_file_path = os.path.join('media', media_files[0])

    title_file = [file for file in os.listdir('media') if file.endswith('.txt')]
    if not title_file:
        raise Exception("No title file found in 'media' directory.")
    with open(os.path.join('media', title_file[0]), 'r', encoding='utf-8') as f:
        title = f.read().strip()

    save_directory = "local_media"
    os.makedirs(save_directory, exist_ok=True)

    saved_media_path = os.path.join(save_directory, os.path.basename(media_file_path))
    shutil.move(media_file_path, saved_media_path)

    metadata = {
        "title": title,
        "media_file": saved_media_path,
        "source_url": url
    }
    metadata_file = os.path.join(save_directory, "metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as meta_file:
        json.dump(metadata, meta_file, indent=4)

    print(f"Media and metadata saved locally:\n- Media: {saved_media_path}\n- Metadata: {metadata_file}")
    shutil.rmtree('media')

def create_videos_with_audio():
    """
    Create videos from images with audio.
    """
    image_dir = 'local_media'
    audio_file = 'audio.mp3'
    output_dir = 'output_videos'
    
    os.makedirs(output_dir, exist_ok=True)
    
    for image_file in os.listdir(image_dir):
        if image_file.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(image_dir, image_file)
            output_video_path = os.path.join(output_dir, f'{os.path.splitext(image_file)[0]}_video.mp4')
            
            command = [
                'ffmpeg',
                '-y',
                '-loop', '1',
                '-i', image_path,
                '-i', audio_file,
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-c:a', 'copy',
                '-pix_fmt', 'yuv420p',
                '-shortest',
                output_video_path
            ]
            
            subprocess.run(command)
            print(f"Created video for {image_file}")

async def main():
    # Get user input for the prompt
    prompt = input("Enter your prompt to generate a relevant hashtag: ")

    # Generate the hashtag from the prompt using Gemini model
    generated_hashtag = generate_hashtag_from_prompt(prompt)
    hashtag = generated_hashtag.replace('#', '').strip()
    print(f"Generated hashtag: #{hashtag}")

    try:
        # Fetch Instagram posts
        urls = await fetch_instagram_post_urls(hashtag)
        if urls:
            print(f"Saved {len(urls)} post URLs for #{hashtag}:")
            for i, url in enumerate(urls, start=1):
                print(f"{i}. {url}")
                
            # Ask user whether to upload to Empowerverse
            a = input("Do you want to upload it to the Empowerverse app? (y/n): ")
            
            for url in urls:
                try:
                    if a.lower() == 'y':
                        await process_media_url(url)
                    else:
                        await process_post(url)
                except Exception as e:
                    print(f"Error processing {url}: {e}", file=sys.stderr)
                finally:
                    if os.path.exists('media'):
                        shutil.rmtree('media')
            
            # After processing all URLs, create videos if audio file exists
            if os.path.exists('audio.mp3'):
                create_videos_with_audio()
            
        else:
            print(f"No posts found for #{hashtag}.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())