// Use relative URL since frontend is served by the same backend server
const API_URL = window.location.origin;

let audioFile = null;
let transcriptionText = '';
let currentStep = 'upload';
let availableTemplates = [];
let currentTemplateName = '';
let currentTemplateFields = {};
let currentNoteData = {};
let currentNoteTemplateName = '';

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
    const dropdownItems = document.getElementById('dropdown-items');
    dropdownItems.innerHTML = '';
    
    if (availableTemplates.length === 0) {
        dropdownItems.innerHTML = '<div style="padding: 1rem; text-align: center; color: #9ca3af;">No templates available</div>';
        return;
    }
    
    availableTemplates.forEach(template => {
        const item = document.createElement('div');
        item.className = 'dropdown-item';
        item.textContent = template.name;
        item.onclick = () => selectTemplate(template.name);
        dropdownItems.appendChild(item);
    });
}

// Toggle dropdown visibility
function toggleDropdown() {
    const dropdown = document.getElementById('custom-dropdown');
    const menu = document.getElementById('dropdown-menu');
    
    if (menu.style.display === 'none') {
        menu.style.display = 'block';
        dropdown.classList.add('active');
    } else {
        menu.style.display = 'none';
        dropdown.classList.remove('active');
    }
}

// Select template from dropdown
function selectTemplate(templateName) {
    document.getElementById('template-search').value = templateName;
    document.getElementById('dropdown-menu').style.display = 'none';
    document.getElementById('custom-dropdown').classList.remove('active');
}

// Filter templates based on search
function filterTemplates() {
    const menu = document.getElementById('dropdown-menu');
    const searchTerm = document.getElementById('template-search').value.toLowerCase();
    const items = document.querySelectorAll('.dropdown-item');
    
    // Show dropdown when typing
    if (searchTerm && menu.style.display === 'none') {
        menu.style.display = 'block';
        document.getElementById('custom-dropdown').classList.add('active');
    }
    
    // Filter items
    let hasVisible = false;
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = 'flex';
            hasVisible = true;
        } else {
            item.style.display = 'none';
        }
    });
    
    // Hide if no results and no search term
    if (!hasVisible && !searchTerm) {
        menu.style.display = 'none';
        document.getElementById('custom-dropdown').classList.remove('active');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('custom-dropdown');
    if (dropdown && !dropdown.contains(e.target)) {
        document.getElementById('dropdown-menu').style.display = 'none';
        dropdown.classList.remove('active');
    }
});

// Mode switching
function setMode(mode) {
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    if (mode === 'generate') {
        document.getElementById('generate-mode').style.display = 'block';
        document.getElementById('template-mode').style.display = 'none';
        document.getElementById('empty-state').style.display = 'block';
        document.getElementById('template-empty-state').style.display = 'none';
        document.getElementById('template-result-section').style.display = 'none';
        document.querySelector('.progress-bar').style.display = 'flex';
        resetProgress();
    } else {
        document.getElementById('generate-mode').style.display = 'none';
        document.getElementById('template-mode').style.display = 'block';
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('template-empty-state').style.display = 'block';
        document.getElementById('template-result-section').style.display = 'none';
        document.querySelector('.progress-bar').style.display = 'none';
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
        // Store note data for download
        currentNoteData = data.medical_note;
        currentNoteTemplateName = templateName;
        
        // Display formatted HTML from backend
        const noteOutput = document.getElementById('medical-note');
        noteOutput.innerHTML = data.formatted_html || '<p>No formatted output available</p>';
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
            
            // Hide empty states
            document.getElementById('template-empty-state').style.display = 'none';
            document.getElementById('empty-state').style.display = 'none';
            
            // Store template data for download
            currentTemplateName = templateName;
            currentTemplateFields = data.fields;
            
            // Display formatted HTML from backend
            const templateOutput = document.getElementById('template-fields');
            templateOutput.innerHTML = data.formatted_html || '<p>No formatted output available</p>';

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

// Download template as Word document
async function downloadTemplate() {
    if (!currentTemplateName) {
        showPopup('Error', 'No template to download');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/download-template`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                template_name: currentTemplateName,
                fields: currentTemplateFields
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentTemplateName.replace(/\s+/g, '_')}.docx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showPopup('Success', 'Template downloaded successfully!');
        } else {
            throw new Error('Download failed');
        }
    } catch (error) {
        showPopup('Error', error.message);
    }
}

async function downloadNote() {
    if (!currentNoteData || Object.keys(currentNoteData).length === 0) {
        showPopup('Error', 'No medical note to download');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/download-note`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                template_name: currentNoteTemplateName || 'Medical Note',
                note_data: currentNoteData
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Medical_Note_${Date.now()}.docx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showPopup('Success', 'Medical note downloaded successfully!');
        } else {
            throw new Error('Download failed');
        }
    } catch (error) {
        showPopup('Error', error.message);
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
