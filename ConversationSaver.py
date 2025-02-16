import os
from datetime import datetime

class ConversationSaver:
    def __init__(self, save_dir="conversations"):
        self.save_dir = save_dir
        self._ensure_save_directory_exists()
        
    def _ensure_save_directory_exists(self):
        """Create the save directory if it doesn't exist"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
    def _generate_filename(self):
        """Generate a unique filename based on timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"conversation_{timestamp}.txt"
        
    def save_conversation(self, transcript, suggestions):
        """Save the transcript and suggestions to a file"""
        filename = self._generate_filename()
        filepath = os.path.join(self.save_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 50 + "\n")
            f.write("CONVERSATION TRANSCRIPT\n")
            f.write("=" * 50 + "\n\n")
            
            # Write transcript
            f.write(transcript)
            
            # Write separator
            f.write("\n\n" + "=" * 50 + "\n")
            f.write("AI SUGGESTIONS\n")
            f.write("=" * 50 + "\n\n")
            
            # Write suggestions
            f.write(suggestions)
            
        return filepath