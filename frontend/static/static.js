// Use relative URL since frontend is served by the same backend server
const API_URL = window.location.origin;

let audioFile = null;
let transcriptionText = '';
let currentStep = 'upload';
let availableTemplates = [];

// Load templates on page load
async function loadTemplates() {
    try {
        const response = await fetch(`${API_URL}/templates`);
        const data = await response.json();
        
        if (data.success && data.templates) {
            availableTemplates = data.templates;
            updateTemplateDropdown();
        }
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

// Update template dropdown with fetched templates
function updateTemplateDropdown() {
    const datalist = document.getElementById('template-list');
    datalist.innerHTML = '';
    
    availableTemplates.forEach(template => {
        const option = document.createElement('option');
        option.value = template.name;
        datalist.appendChild(option);
    });
}

// Mode switching
function setMode(mode) {
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    if (mode === 'generate') {
        document.getElementById('generate-mode').style.display = 'block';
        document.getElementById('template-mode').style.display = 'none';
        resetProgress();
    } else {
        document.getElementById('generate-mode').style.display = 'none';
        document.getElementById('template-mode').style.display = 'block';
        hideAllResults();
    }
}

// File uploads
document.getElementById('audio-file').addEventListener('change', (e) => {
    audioFile = e.target.files[0];
    if (audioFile) {
        document.getElementById('file-name').textContent = `📎 ${audioFile.name}`;
        document.getElementById('start-btn').disabled = false;
    }
});

document.getElementById('document-file').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('doc-file-name').textContent = `📎 ${file.name}`;
        checkCreateTemplateReady();
    }
});

// Check if template name field has input
document.getElementById('new-template-name').addEventListener('input', () => {
    checkCreateTemplateReady();
});

// Enable/disable Create Template button based on form completion
function checkCreateTemplateReady() {
    const templateName = document.getElementById('new-template-name').value.trim();
    const documentFile = document.getElementById('document-file').files[0];
    const createBtn = document.getElementById('create-template-btn');
    
    if (templateName && documentFile) {
        createBtn.disabled = false;
    } else {
        createBtn.disabled = true;
    }
}

// Progress management
function setProgressStep(step) {
    currentStep = step;
    const steps = ['upload', 'transcribe', 'generate', 'complete'];
    const currentIndex = steps.indexOf(step);

    steps.forEach((s, index) => {
        const element = document.getElementById(`step-${s}`);
        element.classList.remove('active', 'completed');
        
        if (index < currentIndex) {
            element.classList.add('completed');
        } else if (index === currentIndex) {
            element.classList.add('active');
        }
    });
}

function resetProgress() {
    setProgressStep('upload');
    hideAllResults();
    document.getElementById('empty-state').style.display = 'block';
}

function hideAllResults() {
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('transcription-section').style.display = 'none';
    document.getElementById('note-section').style.display = 'none';
    document.getElementById('template-result-section').style.display = 'none';
}

// Section toggle
function toggleSection(section) {
    const header = event.currentTarget;
    const content = document.getElementById(`${section}-content`);
    
    header.classList.toggle('collapsed');
    if (content.style.display === 'none') {
        content.style.display = 'block';
    } else {
        content.style.display = 'none';
    }
}

// Main process
async function startProcess() {
    if (!audioFile) {
        showPopup('Error', 'Please select an audio file');
        return;
    }

    const templateName = document.getElementById('template-search').value.trim();
    if (!templateName) {
        showPopup('Error', 'Please select or enter a template name');
        return;
    }

    const startBtn = document.getElementById('start-btn');
    startBtn.disabled = true;
    startBtn.textContent = 'Processing...';

    hideAllResults();

    try {
        // Step 1: Transcribe & Clean
        setProgressStep('transcribe');
        await transcribeAudio();

        // Step 2: Auto-generate note
        setProgressStep('generate');
        await generateNote(templateName);

        // Step 3: Complete
        setProgressStep('complete');
        startBtn.textContent = 'Start Processing';
        startBtn.disabled = false;

    } catch (error) {
        showPopup('Error', error.message);
        startBtn.textContent = 'Start Processing';
        startBtn.disabled = false;
    }
}

async function transcribeAudio() {
    const formData = new FormData();
    formData.append('audio', audioFile);

    const response = await fetch(`${API_URL}/transcribe-and-clean`, {
        method: 'POST',
        body: formData
    });

    const data = await response.json();

    if (data.success) {
        transcriptionText = data.transcription;
        
        // Show transcription section
        document.getElementById('transcription-text').textContent = transcriptionText;
        document.getElementById('transcription-section').style.display = 'block';
        
        return data;
    } else {
        throw new Error(data.error || 'Failed to transcribe audio');
    }
}

async function generateNote(templateName) {
    const response = await fetch(`${API_URL}/generate-note`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            cleaned_text: transcriptionText,
            template_name: templateName
        })
    });

    const data = await response.json();

    if (data.success) {
        // Display medical note
        const noteOutput = document.getElementById('medical-note');
        noteOutput.innerHTML = '';

        Object.entries(data.medical_note).forEach(([key, value]) => {
            const field = document.createElement('div');
            field.className = 'note-field';
            
            const label = document.createElement('strong');
            label.textContent = key.replace(/_/g, ' ');
            
            const content = document.createElement('span');
            if (typeof value === 'object' && value !== null) {
                content.textContent = JSON.stringify(value, null, 2);
                content.style.whiteSpace = 'pre-wrap';
            } else {
                content.textContent = value || 'N/A';
            }
            
            field.appendChild(label);
            field.appendChild(content);
            noteOutput.appendChild(field);
        });

        document.getElementById('note-section').style.display = 'block';
        
        return data;
    } else {
        throw new Error(data.error || 'Failed to generate note');
    }
}

// Create Template
async function createTemplate() {
    const fileInput = document.getElementById('document-file');
    const file = fileInput.files[0];
    const templateName = document.getElementById('new-template-name').value.trim();

    if (!file || !templateName) {
        showPopup('Error', 'Please provide both template name and document');
        return;
    }

    const btn = document.getElementById('create-template-btn');
    btn.disabled = true;
    btn.textContent = 'Creating...';

    try {
        const formData = new FormData();
        formData.append('document', file);
        formData.append('template_name', templateName);

        const response = await fetch(`${API_URL}/create-template`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            hideAllResults();
            
            const templateOutput = document.getElementById('template-fields');
            templateOutput.innerHTML = '';

            Object.entries(data.fields).forEach(([key, value]) => {
                const field = document.createElement('div');
                field.className = 'note-field';
                
                const label = document.createElement('strong');
                label.textContent = key;
                
                const content = document.createElement('span');
                content.textContent = value.description || 'No description';
                
                field.appendChild(label);
                field.appendChild(content);
                templateOutput.appendChild(field);
            });

            document.getElementById('template-result-section').style.display = 'block';
            
            // Reload templates list
            await loadTemplates();
            
            if (data.message) {
                showPopup('✅ Success!', data.message);
            }
            
            // Reset form
            document.getElementById('new-template-name').value = '';
            document.getElementById('document-file').value = '';
            document.getElementById('doc-file-name').textContent = '';
            
        } else {
            showPopup('Error', data.error || 'Failed to create template');
        }
    } catch (error) {
        showPopup('Error', error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Template';
    }
}

// Popup
function showPopup(title, message) {
    document.getElementById('popup-title').textContent = title;
    document.getElementById('popup-message').textContent = message;
    document.getElementById('popup-overlay').style.display = 'flex';
}

function closePopup() {
    document.getElementById('popup-overlay').style.display = 'none';
}

// Close popup on overlay click
document.getElementById('popup-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'popup-overlay') {
        closePopup();
    }
});

// Load templates on page load
loadTemplates();
