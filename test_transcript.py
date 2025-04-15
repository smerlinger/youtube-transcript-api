import os
import json
import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

# Load environment variables from .env file
print("Starting script...")
load_dotenv()
print("Loaded .env file")

# Get video ID from command line or use default
video_id = "8vXoI7lUroQ"

# Get WebShare proxy credentials from environment variables
webshare_username = os.getenv('WEBSHARE_USERNAME')
webshare_password = os.getenv('WEBSHARE_PASSWORD')

print(f"Testing transcript retrieval for video ID: {video_id}")
print(f"Using WebShare credentials: Username={webshare_username}, Password={'*' * len(webshare_password) if webshare_password else 'None'}")

if not webshare_username or not webshare_password:
    print("WARNING: WebShare credentials are missing or empty!")

# Setup proxy configuration - updated to use proxy.webshare.io instead of p.webshare.io
proxies = {
    'http': f'http://{webshare_username}:{webshare_password}@proxy.webshare.io:80/',
    'https': f'http://{webshare_username}:{webshare_password}@proxy.webshare.io:80/'
}
print(f"Proxy configuration: {proxies}")

# Test the proxy connection first
print("Testing proxy connection...")
try:
    response = requests.get('https://api.ipify.org?format=json', proxies=proxies, timeout=10)
    print(f"Proxy connection successful. Your IP address through proxy: {response.json()['ip']}")
except Exception as e:
    print(f"Proxy connection test failed: {str(e)}")
    print("Trying alternative proxy formats...")
    
    # Try alternative proxy format with different port
    try:
        alt_proxies = {
            'http': f'http://{webshare_username}:{webshare_password}@proxy.webshare.io:10000/',
            'https': f'http://{webshare_username}:{webshare_password}@proxy.webshare.io:10000/'
        }
        print(f"Trying alternative proxies: {alt_proxies}")
        response = requests.get('https://api.ipify.org?format=json', proxies=alt_proxies, timeout=10)
        print(f"Alternative proxy connection successful. IP: {response.json()['ip']}")
        proxies = alt_proxies
    except Exception as e2:
        print(f"Alternative proxy also failed: {str(e2)}")
        print("Will try without proxy as fallback")
        proxies = None

try:
    print("Attempting to list transcripts...")
    # List available transcripts with proxy
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxies)
    print("Successfully listed transcripts")
    
    # Try to find English transcript first
    languages_to_try = ['en', 'en-US', 'en-GB']
    print(f"Looking for transcripts in languages: {languages_to_try}")
    
    try:
        transcript = transcript_list.find_transcript(languages_to_try)
        print(f"Found transcript in language: {transcript.language}")
    except Exception as e:
        print(f"Could not find transcript in preferred languages: {str(e)}")
        print("Trying any available...")
        # Get first available transcript
        transcript = next(iter(transcript_list))
        print(f"Using transcript in language: {transcript.language}")
    
    print("Fetching transcript data...")
    # Fetch the transcript data
    transcript_data = transcript.fetch()
    print(f"Got transcript data with {len(transcript_data)} entries")
    
    # Format transcript data
    formatter = TextFormatter()
    transcript_text = formatter.format_transcript(transcript_data)
    
    # Print sample of transcript
    print("\nTranscript sample (first 300 characters):")
    print(transcript_text[:300] + "...\n")
    print("Full transcript length:", len(transcript_text))
    
    # Save to file
    with open('transcript_result.txt', 'w') as f:
        f.write(transcript_text)
    
    print("Success! Full transcript saved to transcript_result.txt")
    
except Exception as e:
    print(f"ERROR retrieving transcript: {str(e)}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc() 