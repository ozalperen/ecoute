import threading
from AudioTranscriber import AudioTranscriber
from GPTResponder import GPTResponder
import customtkinter as ctk
import AudioRecorder 
import queue
import time
import torch
import sys
import TranscriberModels
import subprocess
from datetime import datetime

class ResponseManager:
    def __init__(self):
        self.responses = []
        self.last_response = ""
    
    def add_response(self, text):
        if text != self.last_response and text.strip():
            self.responses.append(text)
            self.last_response = text
    
    def get_formatted_responses(self):
        return "\n\n".join(self.responses)
    
    def clear_responses(self):
        self.responses.clear()
        self.last_response = ""

def update_transcript_UI(transcriber, textbox):
    transcript_string = transcriber.get_transcript()
    
    # Configure tags for different speakers
    try:
        textbox.tag_config("siz", foreground='#FFFCF2')     # User messages
        textbox.tag_config("musteri", foreground='#FF9500') # Speaker messages
    except Exception:
        # Tags might already be configured
        pass
    
    # Clear the textbox
    textbox.delete("0.0", "end")
    
    # Insert transcript lines
    lines = transcript_string.split('\n\n')
    for line in lines:
        if not line.strip():
            continue
            
        if line.startswith("Siz:"):
            textbox.insert("end", line + "\n\n", "siz")
        elif line.startswith("Musteri:"):
            textbox.insert("end", line + "\n\n", "musteri")
        else:
            # Fallback for any other text
            textbox.insert("end", line + "\n\n")
    
    textbox.see("end")  # Scroll to the end
    textbox.after(300, update_transcript_UI, transcriber, textbox)

def update_response_UI(responder, response_manager, textbox, update_interval_slider_label, update_interval_slider, freeze_state):
    if not freeze_state[0]:
        # Add new response if it changed
        response_manager.add_response(responder.response)
        
        # Update textbox with all responses
        textbox.configure(state="normal")
        textbox.delete("0.0", "end")
        textbox.insert("0.0", response_manager.get_formatted_responses())
        textbox.configure(state="disabled")
        
        update_interval = int(update_interval_slider.get())
        responder.update_response_interval(update_interval)
        update_interval_slider_label.configure(text=f"Update interval: {update_interval} seconds")
        
    # Scroll to the end
    textbox.see("end")
    
    textbox.after(300, update_response_UI, responder, response_manager, textbox, 
                 update_interval_slider_label, update_interval_slider, freeze_state)

def create_ui_components(root):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root.title("Cere Insight")
    root.configure(bg='#252422')
    root.geometry("1000x600")

    font_size = 20
    title_font_size = 24

    # Create a frame for transcript section
    transcript_frame = ctk.CTkFrame(root, fg_color="transparent")
    transcript_frame.grid(row=0, column=0, padx=10, pady=(5,20), sticky="nsew")
    
    # Transcript title
    transcript_title = ctk.CTkLabel(transcript_frame, 
                                  text="Transcript", 
                                  font=("Arial", title_font_size, "bold"),
                                  text_color='#FFFCF2')
    transcript_title.grid(row=0, column=0, padx=10, pady=(5,10), sticky="w")
    
    # Transcript textbox
    transcript_textbox = ctk.CTkTextbox(transcript_frame, 
                                      width=300, 
                                      font=("Arial", font_size), 
                                      text_color='#FFFCF2', 
                                      wrap="word")
    transcript_textbox.grid(row=1, column=0, sticky="nsew")

    # Create a frame for suggestions section
    suggestions_frame = ctk.CTkFrame(root, fg_color="transparent")
    suggestions_frame.grid(row=0, column=1, padx=10, pady=(5,20), sticky="nsew")
    
    # Suggestions title
    suggestions_title = ctk.CTkLabel(suggestions_frame, 
                                   text="Suggestions", 
                                   font=("Arial", title_font_size, "bold"),
                                   text_color='#FFFCF2')
    suggestions_title.grid(row=0, column=0, padx=10, pady=(5,10), sticky="w")
    
    # Suggestions textbox
    response_textbox = ctk.CTkTextbox(suggestions_frame, 
                                    width=300, 
                                    font=("Arial", font_size), 
                                    text_color='#639cdc', 
                                    wrap="word")
    response_textbox.grid(row=1, column=0, sticky="nsew")

    freeze_button = ctk.CTkButton(root, text="Durdur", command=None)
    freeze_button.grid(row=1, column=1, padx=10, pady=3, sticky="nsew")

    update_interval_slider_label = ctk.CTkLabel(root, text=f"", font=("Arial", 12), text_color="#FFFCF2")
    update_interval_slider_label.grid(row=2, column=1, padx=10, pady=3, sticky="nsew")

    update_interval_slider = ctk.CTkSlider(root, from_=1, to=10, width=300, height=20, number_of_steps=9)
    update_interval_slider.set(2)
    update_interval_slider.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

    # Configure frame grid weights
    transcript_frame.grid_rowconfigure(1, weight=1)
    transcript_frame.grid_columnconfigure(0, weight=1)
    suggestions_frame.grid_rowconfigure(1, weight=1)
    suggestions_frame.grid_columnconfigure(0, weight=1)

    return transcript_textbox, response_textbox, update_interval_slider, update_interval_slider_label, freeze_button

def clear_context(transcriber, audio_queue, response_manager):
    transcriber.clear_transcript()
    with audio_queue.mutex:
        audio_queue.queue.clear()
    response_manager.clear_responses()

def main():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.")
        return

    root = ctk.CTk()
    transcript_textbox, response_textbox, update_interval_slider, update_interval_slider_label, freeze_button = create_ui_components(root)

    audio_queue = queue.Queue()
    response_manager = ResponseManager()

    user_audio_recorder = AudioRecorder.DefaultMicRecorder()
    user_audio_recorder.record_into_queue(audio_queue)

    time.sleep(2)

    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
    speaker_audio_recorder.record_into_queue(audio_queue)

    model = TranscriberModels.get_model('--local' in sys.argv)

    transcriber = AudioTranscriber(user_audio_recorder.source, speaker_audio_recorder.source, model)
    transcribe = threading.Thread(target=transcriber.transcribe_audio_queue, args=(audio_queue,))
    transcribe.daemon = True
    transcribe.start()

    responder = GPTResponder()
    respond = threading.Thread(target=responder.respond_to_transcriber, args=(transcriber,))
    respond.daemon = True
    respond.start()

    print("READY")

    root.grid_rowconfigure(0, weight=100)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=1)
    root.grid_rowconfigure(3, weight=1)
    root.grid_columnconfigure(0, weight=2)
    root.grid_columnconfigure(1, weight=1)

    # Add the clear transcript button to the UI
    clear_transcript_button = ctk.CTkButton(root, text="Yeni Konuşma", 
                                          command=lambda: clear_context(transcriber, audio_queue, response_manager))
    clear_transcript_button.grid(row=1, column=0, padx=10, pady=3, sticky="nsew")

    freeze_state = [False]  # Using list to be able to change its content inside inner functions
    def freeze_unfreeze():
        freeze_state[0] = not freeze_state[0]  # Invert the freeze state
        freeze_button.configure(text="Devam Et" if freeze_state[0] else "Duraklat")

    freeze_button.configure(command=freeze_unfreeze)

    update_interval_slider_label.configure(text=f"Update interval: {update_interval_slider.get()} seconds")

    update_transcript_UI(transcriber, transcript_textbox)
    update_response_UI(responder, response_manager, response_textbox, 
                       update_interval_slider_label, update_interval_slider, freeze_state)
 
    root.mainloop()

if __name__ == "__main__":
    main()