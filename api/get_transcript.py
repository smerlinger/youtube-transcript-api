from http.server import BaseHTTPRequestHandler
import json
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_POST(self):
        # Set CORS headers for the response
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Get request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data)
        except json.JSONDecodeError:
            self.wfile.write(json.dumps({'error': 'Invalid JSON in request body'}).encode())
            return

        video_id = body.get('video_id')

        if not video_id:
            self.wfile.write(json.dumps({'error': 'Missing video_id in request body'}).encode())
            return

        print(f"Attempting to fetch transcript for video_id: {video_id}")

        transcript_text = None
        languages_to_try = ['en', 'en-US', 'en-GB']  # Prioritize English

        try:
            # List available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try finding the preferred languages first
            transcript = None
            try:
                transcript = transcript_list.find_transcript(languages_to_try)
                print(f"Found transcript in preferred languages: {transcript.language}")
            except NoTranscriptFound:
                print(f"No transcript found in preferred languages ({languages_to_try}). Trying any available...")
                # Fallback: iterate through all available and take the first one
                for available_transcript in transcript_list:
                    transcript = available_transcript
                    print(f"Using first available transcript: {transcript.language}")
                    break
                if not transcript:
                    # This case should ideally be caught by list_transcripts if empty,
                    # but added for robustness.
                    raise NoTranscriptFound(video_id, languages_to_try, "No transcripts available at all.")

            # Fetch the actual transcript data
            transcript_data = transcript.fetch()

            # Combine cues into a single string
            transcript_text = ' '.join([item['text'] for item in transcript_data]).strip()

            if not transcript_text:
                # Handle case where transcript exists but is empty
                raise ValueError("Fetched transcript text is empty.")

            print(f"Successfully fetched and formatted transcript for video_id: {video_id}")
            self.wfile.write(json.dumps({'transcript': transcript_text}).encode())

        except TranscriptsDisabled:
            error_message = "Transcripts are disabled for this video."
            print(f"Error for {video_id}: {error_message}")
            self.wfile.write(json.dumps({'error': error_message, 'details': f'Video ID: {video_id}'}).encode())
        except NoTranscriptFound as e:
            error_message = "Could not find a suitable transcript in any available language."
            print(f"Error for {video_id}: {error_message}")
            self.wfile.write(json.dumps({'error': error_message, 'details': f'Video ID: {video_id}'}).encode())
        except Exception as e:
            error_message = f"An unexpected error occurred fetching transcript: {e}"
            print(f"Error for {video_id}: {error_message}")
            self.wfile.write(json.dumps({'error': 'Failed to fetch transcript', 'details': error_message}).encode())