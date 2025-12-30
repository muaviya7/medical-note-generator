# This module generates structured medical notes from text
from llama_cpp import Llama
import logging
import os
import sys
import json
import time
from prompts import note_generator_prompt
from config import (
    MODEL_PATH, CPU_THREADS, CONTEXT_SIZE, GPU_LAYERS,
    MAX_TOKENS_NOTE_GEN, TEMPERATURE, TOP_P, REPEAT_PENALTY
)

# Configure logging
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'note_generator.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    # Initialize Mistral model
    model = Llama(
        model_path=MODEL_PATH,
        n_ctx=CONTEXT_SIZE,
        n_threads=CPU_THREADS,
        n_gpu_layers=GPU_LAYERS,
        verbose=False
    )
    logger.info(f"Mistral model loaded (threads={CPU_THREADS})")
    
except Exception as e:
    logger.error(f"Failed to load Mistral model: {str(e)}", exc_info=True)
    model = None
    sys.exit(1)


def load_template(template_name):
    """Load a JSON template from the templates directory"""
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", template_name)
    try:
        with open(template_path, 'r') as f:
            template_data = json.load(f)
            
        # If template has a 'fields' list, convert it to a dict structure
        if 'fields' in template_data and isinstance(template_data['fields'], list):
            template_dict = {}
            for field in template_data['fields']:
                # Convert field names to lowercase with underscores
                key = field.lower().replace(' / ', '_').replace(' ', '_').replace('(', '').replace(')', '')
                template_dict[key] = ""
            return template_dict
        
        return template_data
    except Exception as e:
        logger.error(f"Failed to load template {template_name}: {str(e)}")
        return None


def generate_note_from_text(cleaned_text, template_json):
    """
    Generate structured medical note from cleaned text using template
    
    Args:
        cleaned_text: The cleaned medical conversation text
        template_json: JSON template (dict or path to file)
    
    Returns:
        dict: Generated medical note following template structure
    """
    if model is None:
        logger.error("Model not loaded, cannot generate note")
        return {"error": "Model not available"}
    
    # Load template if it's a filename
    if isinstance(template_json, str):
        template_json = load_template(template_json)
        if template_json is None:
            return {"error": "Failed to load template"}
    
    try:
        # Get the prompt
        prompt = note_generator_prompt(cleaned_text, template_json)
        
        logger.info("Generating medical note...")
        logger.info(f"Prompt length: {len(prompt)} characters")
        
        start_time = time.time()
        
        # Generate response
        response = model(
            prompt,
            max_tokens=MAX_TOKENS_NOTE_GEN,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            repeat_penalty=REPEAT_PENALTY,
            echo=False
        )
        
        elapsed = time.time() - start_time
        
        generated_text = response['choices'][0]['text'].strip()
        logger.info(f"Generated text length: {len(generated_text)} characters")
        logger.info(f"Generation took {elapsed:.2f} seconds")
        
        if not generated_text:
            logger.error("Model returned empty response!")
            return {"error": "Model generated empty output"}
        
        logger.info(f"Response preview: {generated_text[:200]}...")
        
        # Minimal cleanup - just find JSON boundaries if model adds anything
        if '{' in generated_text:
            start = generated_text.find('{')
            end = generated_text.rfind('}') + 1
            json_text = generated_text[start:end]
        else:
            json_text = generated_text
        
        # Parse JSON
        try:
            note_json = json.loads(json_text)
            logger.info("Successfully parsed JSON response")
            note_json['_generation_time'] = f"{elapsed:.2f}s"
            return note_json
            
        except json.JSONDecodeError as je:
            logger.error(f"JSON parse failed: {str(je)}")
            logger.error(f"Raw output: {generated_text[:500]}")
            return {
                "error": "Model did not return valid JSON", 
                "raw_output": generated_text,
                "parse_error": str(je),
                "_generation_time": f"{elapsed:.2f}s"
            }
            
    except Exception as e:
        logger.error(f"Error during note generation: {str(e)}")
        return {"error": str(e)}


# Test case
if __name__ == "__main__":
    # Test data
    test_text = """A 45-year-old male presented with a three-day history of fever, cough, body aches, and a mild headache. The fever reached approximately 101-102°F (38.3-38.9°C), mostly in the evenings. He denied chest pain, shortness of breath, nausea, vomiting, or diarrhea. The patient reported taking paracetamol 500 mg twice daily for temporary relief. He denied known allergies, diabetes, or hypertension.

Vital signs:
- Temperature: 101.4°F (38.6°C)
- Blood pressure: 130/85 mmHg
- Pulse: 92 bpm
- Respiratory rate: 18 breaths per minute
- Oxygen saturation: 98% on room air

Physical examination:
- Lungs: Clear
- Heart: Normal
- Abdomen: Soft, non-tender

Plan:
- Initiate azithromycin 500 mg once daily for three days
- Advise fluids and rest
- Schedule follow-up in three days if symptoms persist or worsen."""
    
    print("="*60)
    print("MEDICAL NOTE GENERATOR - TEST CASE")
    print("="*60)
    print("\nLoading general template...")
    
    # Load general template
    template = load_template("general.json")
    if template:
        print(f"Template structure: {json.dumps(template, indent=2)}")
        print(f"\nGenerating note from test text...")
        print("-"*60)
        
        result = generate_note_from_text(test_text, template)
        
        print("\n" + "="*60)
        print("GENERATED NOTE:")
        print("="*60)
        print(json.dumps(result, indent=2))
    else:
        print("Failed to load template")
