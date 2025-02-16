import openai
from keys import OPENAI_API_KEY
from prompts import create_prompt, INITIAL_RESPONSE
import time
import requests
API_URL = "https://tofaslive.cereinsight.com/api/teams/chat"
API_KEY = "sk-xx6bvjpmx8inzdhfmy8spf518izga9obtdq7y6vcr"
openai.api_key = OPENAI_API_KEY
def generate_response_from_transcript(transcript):
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    data = {
        'question': transcript
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        response_data = response.json()
        
        # Extract the content from the response structure
        if (response_data and 
            'text' in response_data and 
            'choices' in response_data['text'] and 
            len(response_data['text']['choices']) > 0 and 
            'message' in response_data['text']['choices'][0] and 
            'content' in response_data['text']['choices'][0]['message']):
            
            return response_data['text']['choices'][0]['message']['content']
            
    except Exception as e:
        print(f"Error making API request: {e}")
        return ''
        
    return ''
    
class GPTResponder:
    def __init__(self):
        self.response = "Konuşmaya başlayın..."  
        self.response_interval = 2

    def respond_to_transcriber(self, transcriber):
        while True:
            if transcriber.transcript_changed_event.is_set():
                start_time = time.time()

                transcriber.transcript_changed_event.clear() 
                transcript_string = transcriber.get_transcript()
                response = generate_response_from_transcript(transcript_string)
                
                end_time = time.time()
                execution_time = end_time - start_time
                
                if response != '':
                    self.response = response

                remaining_time = self.response_interval - execution_time
                if remaining_time > 0:
                    time.sleep(remaining_time)
            else:
                time.sleep(0.3)

    def update_response_interval(self, interval):
        self.response_interval = interval