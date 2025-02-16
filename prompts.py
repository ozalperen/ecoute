INITIAL_RESPONSE = "Tavsiye almak için konuşmayı başlatın."
def create_prompt(transcript):
        return f"""Verilen transkrip doğrultusunda müşteri temsilcisine yardım et: 
        
{transcript}.

Müşteri temsilcisi ne demeli?
"""