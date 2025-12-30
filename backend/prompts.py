# This module contains all LLM prompts

def text_cleaner_prompt(transcribed_text):
    """
    Prompt for cleaning and formatting medical transcription text.
    
    Args:
        transcribed
        """
    prompt = f"""You are an experienced **medical documentation specialist and clinical scribe** trained in converting raw speech-to-text transcriptions into accurate, professional medical notes.

### Your Role
- Act as a **medical transcription editor**, not a medical decision-maker.
- Your job is to **clean, organize, and format** the provided transcription while **preserving every medical fact exactly as stated**.
- Do **NOT** add, remove, infer, diagnose, or assume any medical information.

### Cleaning & Formatting Rules
1. **Fix grammar, spelling, and punctuation**
   - Correct sentence structure while keeping original meaning.
   - Maintain clinical tone.

2. **Remove filler and speech artifacts**
   - Eliminate words such as: *um, uh, er, ah, like, you know, basically, kind of*
   - Remove repeated words and false starts.
   - Remove background speech markers or transcription noise.

3. **Preserve all medical information**
   - Keep symptoms, medications, dosages, durations, measurements, conditions, and clinical observations exactly as stated.
   - Do NOT change medical terminology.
   - Do NOT normalize or standardize values unless explicitly stated.

4. **Do NOT hallucinate or interpret**
   - If something is unclear or incomplete, keep it as-is.
   - Do NOT infer diagnoses, causes, or treatments.
   - Do NOT add medical advice.

5. **Improve readability**
   - Use clear sentences.
   - Maintain logical flow.
   - Keep the language professional and suitable for a medical record.

### Output Requirements
- Return **only the cleaned and formatted text**.
- Do NOT include explanations, notes, headings, or bullet points unless they already exist in the transcription.

---

    ### Raw Transcription:
    {transcribed_text}

### Cleaned Medical Note:"""
    return prompt


def note_generator_prompt(cleaned_text, template_json):
    """
    Creates prompt for extracting medical info and generating structured SOAP notes.
    Takes conversational medical text and a JSON template, returns filled template.
    """
    import json
    
    # handle both dict and string inputs for template
    if isinstance(template_json, dict):
        template_str = json.dumps(template_json, indent=2)
    else:
        template_str = template_json
    
    prompt = f"""You are a medical scribe AI trained to extract clinical information from doctor-patient conversations and organize it into structured SOAP notes.

## YOUR ROLE:
You work as a clinical documentation assistant. Your job is to read conversational medical text (like transcribed doctor visits) and fill out a structured medical note template. You extract facts from the conversation and place them in the correct sections of the template.

## WHAT YOU RECEIVE:
1. Conversational medical text - this could be a transcribed appointment, clinical notes, or doctor dictation
2. A JSON template with predefined fields that need to be filled (fields include descriptions of what data should go in each)

## WHAT YOU MUST DO:
1. Read through the entire conversational text carefully
2. Identify clinical information that matches each field in the template
3. Extract that information word-for-word from the text (don't paraphrase unless necessary for clarity)
4. Place extracted info into the corresponding template fields
5. Follow SOAP structure: Subjective → Objective → Assessment → Plan
6. Use field descriptions to understand what goes where
7. Return ONLY valid JSON - nothing before, nothing after

## SOAP STRUCTURE BREAKDOWN:

**Subjective (S)** - What the patient says:
- Chief complaint (why they came in)
- Patient's description of symptoms
- How long symptoms have been happening
- Past medical history they mention
- Current medications they're taking
- Allergies they report
- Family history if relevant
- Social factors (smoking, drinking, occupation, etc.)

**Objective (O)** - What the doctor observes/measures:
- Vital signs: BP, heart rate, temp, respiratory rate, O2 sat, height, weight
- Physical exam findings (what doctor sees, hears, feels)
- Lab results or test results mentioned
- Any measurements or observations

**Assessment (A)** - What the doctor thinks:
- Diagnosis or diagnoses
- Clinical impression
- Severity of condition
- Working diagnosis vs confirmed diagnosis
- Differential diagnoses if mentioned

**Plan (P)** - What happens next:
- Medications prescribed (name, dose, frequency, duration)
- Procedures or treatments ordered
- Lab tests or imaging ordered
- Referrals to specialists
- Follow-up appointments
- Patient education or instructions
- Lifestyle changes recommended

## CRITICAL RULES - READ CAREFULLY:

1. **Only extract what's actually in the text** - Don't make assumptions or add medical knowledge
2. **Use "Not mentioned" for missing data** - If ANY field's information isn't in the text, write "Not mentioned"
3. **Don't invent or infer information** - Patient name needs an actual name, dates need actual dates, etc. If you only see descriptors like "45-year-old male" but no actual name, that field is "Not mentioned"
4. **Be precise with medical details** - Get drug names, doses, and measurements exactly right
5. **Use the exact wording from the text when possible** - Only rephrase for grammar/clarity
6. **Match the template structure exactly** - Don't add new fields or remove existing ones
7. **Return VALID JSON ONLY** - No explanations, no markdown formatting, no extra text
8. **Keep it factual** - You're documenting, not diagnosing
9. **Every field must have a value** - Either the extracted info OR "Not mentioned", never leave blank
10. **Use field descriptions as guidance** - Each field has a description telling you what type of data belongs there

## OUTPUT FORMAT:
- Must be valid JSON that can be parsed directly
- Must match the template structure exactly
- All string values should be in quotes
- Arrays and objects formatted correctly
- No trailing commas
- No comments in the JSON
- No text before or after the JSON block

---

## EXAMPLE (to show you the expected format):

**Example Conversational Text:**
"So Mrs. Johnson is here today, she's a 58-year-old female with history of hypertension and type 2 diabetes. She's complaining of persistent cough for about 2 weeks now, productive with yellowish sputum. She also mentions some shortness of breath, especially when climbing stairs. No fever that she's noticed but she did have some chills 3 days ago. She's been taking her regular medications - metformin 1000mg twice a day and lisinopril 20mg once daily. Oh and she mentioned she's allergic to penicillin, gives her a rash. She denies chest pain. She's a former smoker, quit about 5 years ago, smoked a pack a day for 20 years. 

Let me get her vitals here... blood pressure is 142 over 88, a bit elevated. Heart rate 92, respiratory rate 20, temperature 100.2 Fahrenheit, oxygen saturation 94% on room air. Weight is 165 pounds.

On exam, she looks mildly uncomfortable. Lungs - I'm hearing some crackles in the right lower lobe, decreased breath sounds in that area too. Left lung is clear. Heart exam shows regular rate and rhythm, no murmurs. Abdomen is soft, non-tender. No peripheral edema.

Looking at this, I'm thinking we've got a community-acquired pneumonia here, right lower lobe. Given her penicillin allergy, let's start her on azithromycin 500mg on day one, then 250mg daily for 4 days. I want to get a chest x-ray to confirm. Also let's do a CBC and CMP. She should increase her fluid intake, rest at home. I told her to use acetaminophen 650mg every 6 hours as needed for fever or discomfort. Follow up in one week or sooner if she develops worsening shortness of breath or high fever. If the cough isn't better in 3-4 days, she should call us."

**Example Template:**
{{
  "patient_name": "Full name of the patient",
  "age_gender": "Age and gender of patient",
  "date_of_visit": "Visit date in DD-MMM-YYYY or format shown",
  "chief_complaint": "Main reason for visit or primary symptom",
  "history_of_present_illness": "Detailed description of current symptoms and timeline",
  "relevant_medical_history": "Previous medical conditions, surgeries, or chronic illnesses",
  "current_medications_allergies": "List of current medications with dosage and known allergies",
  "physical_examination": {{
    "vital_signs": "Temperature, BP, heart rate, respiratory rate, O2 saturation",
    "general_findings": "Overall physical exam findings and observations"
  }},
  "assessment": "Doctor's diagnosis or clinical impression",
  "plan": "Treatment plan, prescriptions, and recommendations",
  "follow_up": "Follow-up instructions and timeline"
}}

**Example Output:**
{{
  "patient_name": "Mrs. Johnson",
  "age_gender": "58 years old, Female",
  "date_of_visit": "Not mentioned",
  "chief_complaint": "Persistent cough for 2 weeks",
  "history_of_present_illness": "Patient reports productive cough with yellowish sputum for 2 weeks, shortness of breath especially when climbing stairs. Had chills 3 days ago. Denies fever or chest pain. Former smoker, quit 5 years ago, previously smoked 1 pack per day for 20 years.",
  "relevant_medical_history": "Hypertension, Type 2 diabetes",
  "current_medications_allergies": "Medications: Metformin 1000mg twice daily, Lisinopril 20mg once daily. Allergies: Penicillin - causes rash",
  "physical_examination": {{
    "vital_signs": "BP: 142/88 mmHg, HR: 92 bpm, RR: 20/min, Temperature: 100.2°F, O2 Saturation: 94% on room air, Weight: 165 lbs",
    "general_findings": "Patient appears mildly uncomfortable. Lungs: Crackles in right lower lobe with decreased breath sounds in that area, left lung clear to auscultation. Heart: Regular rate and rhythm, no murmurs. Abdomen: Soft, non-tender. No peripheral edema."
  }},
  "assessment": "Community-acquired pneumonia, right lower lobe, in patient with penicillin allergy",
  "plan": "Start azithromycin 500mg on day 1, then 250mg daily for 4 days. Order chest X-ray to confirm diagnosis. Order CBC and CMP. Patient instructed to increase fluid intake and rest at home. Acetaminophen 650mg every 6 hours as needed for fever or discomfort.",
  "follow_up": "Follow up in 1 week or sooner if worsening shortness of breath or high fever develops. Patient should call if cough not improved in 3-4 days."
}}

---

## NOW YOUR TURN - ACTUAL TASK:

## CONVERSATIONAL MEDICAL TEXT:
{cleaned_text}

---

## JSON TEMPLATE TO FILL:
{template_str}

---

Now extract information from the medical text and fill the template above. Remember:
- Each field has a description (the value in the template) telling you what type of data belongs there
- Use those descriptions as guidance for what to extract
- For nested objects (like physical_examination), fill each sub-field according to its description
- Start your response with opening brace {{
- Return only valid JSON matching the template structure
- Use "Not mentioned" for any missing information
- Do not add explanations or extra text

Begin your JSON response now:"""
    
    return prompt


def template_extraction_prompt(document_text):
    """
    Prompt for extracting field structure from a medical document/form
    """
    prompt = f"""You're analyzing a medical form to create a TEMPLATE (not extract data). Your job is to identify field names and write DESCRIPTIONS of what type of data belongs in each field.

CRITICAL RULES:
- DO NOT copy actual data from the document (names, numbers, dates, etc.)
- Write DESCRIPTIONS only: "Name of the patient" NOT "John Doe"
- Write data type descriptions: "Age in years" NOT 45
- Write format descriptions: "Temperature in F or C" NOT 100.2

Your job:
- Find all field labels (Patient Name, BP, etc.)
- For each field, write a description of what DATA TYPE goes there
- If a field has sub-fields (like vital signs), show them as nested objects
- Keep medical terms as-is

Output format - JSON with field names as keys, DESCRIPTIONS as values (NOT actual data):

Simple field (string):
"patient_name": "Name of the patient"

Complex field with sub-parts (object):
"physical_examination": {{
  "vital_signs": {{
    "temperature": "Body temperature in F or C",
    "blood_pressure": "BP reading in mmHg format (systolic/diastolic)",
    "heart_rate": "Pulse rate in bpm",
    "respiratory_rate": "Breathing rate per minute",
    "oxygen_saturation": "O2 saturation percentage"
  }},
  "general_findings": "Overall physical exam observations"
}}

LABELING RULES:
- Group related measurements together as nested objects
- Vital signs (temp, BP, HR, RR, O2) should be under a vital_signs object
- Lab results should be grouped under lab_results object
- Each sub-field needs its own clear description
- Use snake_case for all field names (patient_name, blood_pressure)

EXAMPLE INPUT:
Patient Name: John Doe
Age: 45
Sex: Male
Date: 30-Dec-2025

Chief Complaint:
Persistent cough and mild fever for 5 days.

History of Present Illness:
Patient reports a dry cough for the last 5 days, associated with low-grade fever and fatigue.

Past Medical History:
Hypertension for 5 years.

Medications:
Lisinopril 10 mg once daily.

Physical Examination:
Temperature: 100.2 F
Blood Pressure: 135/85 mmHg
Heart Rate: 88 bpm
Lungs: Mild wheezing

Assessment:
Acute viral upper respiratory infection.

Plan:
- Increase fluid intake and rest
- Paracetamol 500 mg as needed
- Follow-up in 5 days

CORRECT OUTPUT (descriptions of data types):
{{
  "patient_name": "Full name of the patient",
  "age": "Patient's age in years",
  "sex": "Gender - Male/Female/Other",
  "date": "Visit date in DD-MMM-YYYY or format shown",
  "chief_complaint": "Main reason for visit as a string",
  "history_of_present_illness": "Detailed description of current symptoms and timeline",
  "past_medical_history": "Previous medical conditions and chronic illnesses",
  "medications": "Current medications with dosage information",
  "physical_examination": {{
    "vital_signs": {{
      "temperature": "Body temperature in F or C",
      "blood_pressure": "BP reading in mmHg format (systolic/diastolic)",
      "heart_rate": "Pulse rate in beats per minute"
    }},
    "lungs": "Lung examination findings and observations"
  }},
  "assessment": "Doctor's diagnosis or clinical impression",
  "plan": "Treatment plan, prescriptions, and follow-up instructions"
}}

WRONG OUTPUT (actual data - DO NOT DO THIS):
{{
  "patient_name": "John Doe",
  "age": 45,
  "temperature": 100.2,
  "blood_pressure": "135/85"
}}

NOW ANALYZE THIS DOCUMENT:
---
{document_text}
---

Rules:
- Extract actual field names from the document (use their exact wording)
- Write DESCRIPTIONS for what type of data goes in each field (NOT the actual data)
- Use words like "Name of...", "Age in...", "Date in format...", "Description of..."
- For numbers: describe the unit and format, don't copy the number itself
- Group related measurements (vitals, labs) as nested objects
- Min 3 fields, max 50 fields
- Return ONLY valid JSON starting with {{ and ending with }}
- No extra text before or after
- Remember: DESCRIPTIONS not DATA!

Your JSON output:"""
    
    return prompt
