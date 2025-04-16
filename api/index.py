from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.formatters import TextFormatter

# Load environment variables from .env file - Vercel will use project env vars
# load_dotenv() # No need to load .env in production on Vercel

app = Flask(__name__)

@app.route('/api/get-transcript', methods=['GET'])
def get_transcript():
    # Get video_id from query parameters
    video_id = request.args.get('video_id')
    
    if not video_id:
        return jsonify({'error': 'Missing video_id parameter'}), 400
    
    print(f"Attempting to fetch transcript for video_id: {video_id}")
    
    # Get WebShare proxy credentials from environment variables
    webshare_username = os.getenv('WEBSHARE_USERNAME')
    webshare_password = os.getenv('WEBSHARE_PASSWORD')
    
    # Check if we have proxy credentials
    if not webshare_username or not webshare_password:
        print("WARNING: WebShare proxy credentials not set. Using direct connection.")
        use_proxy = False
    else:
        use_proxy = True
        # Avoid printing credentials in logs
        # print("Using WebShare proxy for YouTube request.") 
    
    languages_to_try = ['en', 'en-US', 'en-GB']  # Prioritize English
    
    try:
        # Setup proxy configuration if available
        if use_proxy:
            proxies = {
                'http': f'http://{webshare_username}:{webshare_password}@proxy.webshare.io:80/',
                'https': f'http://{webshare_username}:{webshare_password}@proxy.webshare.io:80/'
            }
            # print("Attempting to use WebShare proxy...") # Avoid verbose logging
        else:
            proxies = None
        
        # First attempt with proxy if configured
        try:
            # List available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxies)
            # print("Successfully connected to YouTube with proxy configuration.")
        except Exception as proxy_error:
            # If proxy fails, try without proxy as fallback
            if use_proxy:
                print(f"Proxy connection failed: {str(proxy_error)}. Trying direct connection...")
                proxies = None
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=None)
                # print("Successfully connected to YouTube with direct connection.")
            else:
                # Re-raise the exception if not using proxy
                print(f"Direct connection failed: {str(proxy_error)}")
                raise
        
        # Try finding the preferred languages first
        try:
            transcript = transcript_list.find_transcript(languages_to_try)
            # print(f"Found transcript in preferred language: {transcript.language}")
        except NoTranscriptFound:
            print(f"No transcript found in preferred languages. Trying any available...")
            # Get first available transcript
            found_any = False
            for available_transcript in transcript_list:
                transcript = available_transcript
                # print(f"Using first available transcript: {transcript.language}")
                found_any = True
                break
            if not found_any:
                return jsonify({
                    'error': 'Could not find any transcript for this video',
                    'details': f'Video ID: {video_id}'
                }), 404
        
        # Fetch the transcript data
        transcript_data = transcript.fetch()
        
        # Format transcript data
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript_data)
        
        if not transcript_text:
            return jsonify({
                'error': 'Empty transcript content',
                'details': f'Video ID: {video_id}'
            }), 404
        
        # print(f"Successfully fetched and formatted transcript for video_id: {video_id}")
        return jsonify({'transcript': transcript_text})
    
    except TranscriptsDisabled:
        error_message = "Transcripts are disabled for this video."
        print(f"Error for {video_id}: {error_message}")
        return jsonify({
            'error': error_message,
            'details': f'Video ID: {video_id}'
        }), 404
    
    except NoTranscriptFound as e:
        error_message = "Could not find a suitable transcript in any available language."
        print(f"Error for {video_id}: {error_message}")
        return jsonify({
            'error': error_message,
            'details': f'Video ID: {video_id}'
        }), 404
    
    except Exception as e:
        error_message = f"An unexpected error occurred fetching transcript: {str(e)}"
        print(f"Error for {video_id}: {error_message}")
        import traceback
        traceback.print_exc() # Print full traceback for server errors
        return jsonify({
            'error': error_message,
            'details': str(e)
        }), 500

# Vercel expects the WSGI app object, often named 'app'
# No need for app.run() here 