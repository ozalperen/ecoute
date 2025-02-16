import re
from typing import Dict, Tuple

class MarkdownRenderer:
    def __init__(self, textbox):
        self.textbox = textbox
        self.setup_tags()
        
    def setup_tags(self):
        """Configure text tags for different markdown elements"""
        try:
            # Headers
            self.textbox.tag_config("h1", font=("Arial", 24, "bold"))
            self.textbox.tag_config("h2", font=("Arial", 20, "bold"))
            self.textbox.tag_config("h3", font=("Arial", 16, "bold"))
            
            # Inline styles
            self.textbox.tag_config("bold", font=("Arial", 13, "bold"))
            self.textbox.tag_config("italic", font=("Arial", 13, "italic"))
            self.textbox.tag_config("code", font=("Courier", 12), background="#2d2d2d")
            
            # Code blocks
            self.textbox.tag_config("codeblock", font=("Courier", 12), background="#2d2d2d", spacing1=10, spacing3=10)
            
            # Lists
            self.textbox.tag_config("bullet", lmargin1=20, lmargin2=40)
            self.textbox.tag_config("numbered", lmargin1=20, lmargin2=40)
            
        except Exception as e:
            print(f"Error configuring tags: {e}")

    def render_markdown(self, markdown_text: str):
        """Convert markdown text to formatted text with tags"""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        
        # Split text into blocks (paragraphs, code blocks, etc.)
        blocks = re.split(r'\n\n+', markdown_text)
        
        for block in blocks:
            if block.strip():
                # Code blocks
                if block.startswith('```'):
                    self._insert_code_block(block)
                    continue
                
                # Headers
                if block.startswith('#'):
                    self._insert_header(block)
                    continue
                
                # Lists
                if re.match(r'^[-*]\s', block) or re.match(r'^\d+\.\s', block):
                    self._insert_list(block)
                    continue
                
                # Regular paragraph with inline formatting
                self._insert_paragraph(block)
            
            self.textbox.insert("end", "\n\n")
        
        self.textbox.configure(state="disabled")
    
    def _insert_code_block(self, block: str):
        """Handle code block formatting"""
        lines = block.split('\n')
        if len(lines) >= 2:  # Ensure there's content between the backticks
            code_content = '\n'.join(lines[1:-1])
            self.textbox.insert("end", code_content + "\n", "codeblock")
    
    def _insert_header(self, block: str):
        """Handle header formatting"""
        level = len(re.match(r'^#+', block).group())
        text = block.lstrip('#').strip()
        tag = f"h{min(level, 3)}"
        self.textbox.insert("end", text + "\n", tag)
    
    def _insert_list(self, block: str):
        """Handle list formatting"""
        lines = block.split('\n')
        for line in lines:
            if re.match(r'^[-*]\s', line):
                text = line[2:].strip()
                self.textbox.insert("end", f"• {text}\n", "bullet")
            elif re.match(r'^\d+\.\s', line):
                text = re.sub(r'^\d+\.\s', '', line).strip()
                self.textbox.insert("end", f"• {text}\n", "numbered")
    
    def _insert_paragraph(self, block: str):
        """Handle paragraph with inline formatting"""
        # Process inline code
        parts = re.split(r'(`[^`]+`)', block)
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                self.textbox.insert("end", part[1:-1], "code")
            else:
                # Process bold and italic
                segments = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', part)
                for segment in segments:
                    if segment.startswith('**') and segment.endswith('**'):
                        self.textbox.insert("end", segment[2:-2], "bold")
                    elif segment.startswith('*') and segment.endswith('*'):
                        self.textbox.insert("end", segment[1:-1], "italic")
                    else:
                        self.textbox.insert("end", segment)