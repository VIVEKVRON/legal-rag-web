import { DOM_ELEMENTS } from './config.js';

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
export let recognition = null;
export let isRecording = false;

export function setupSpeechRecognition() {
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            if (DOM_ELEMENTS.micBtn) DOM_ELEMENTS.micBtn.classList.add('recording');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (DOM_ELEMENTS.inputField) {
                DOM_ELEMENTS.inputField.value = DOM_ELEMENTS.inputField.value ? DOM_ELEMENTS.inputField.value + ' ' + transcript : transcript;
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            isRecording = false;
            if (DOM_ELEMENTS.micBtn) DOM_ELEMENTS.micBtn.classList.remove('recording');
        };

        recognition.onend = () => {
            isRecording = false;
            if (DOM_ELEMENTS.micBtn) DOM_ELEMENTS.micBtn.classList.remove('recording');
        };

    } else {
        if (DOM_ELEMENTS.micBtn) DOM_ELEMENTS.micBtn.style.display = 'none';
    }
}

export function toggleRecording() {
    if (!recognition) return;
    if (isRecording) {
        recognition.stop();
    } else {
        recognition.lang = DOM_ELEMENTS.langSelect.value;
        recognition.start();
    }
}

export function speakText(text, lang, btnElement) {
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel();

    // Clean markdown symbols to make speech sound natural
    const cleanText = text.replace(/[*_#`\[\]]/g, '').trim();
    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = lang;
    
    utterance.onstart = () => btnElement.classList.add('playing');
    utterance.onend = () => btnElement.classList.remove('playing');
    utterance.onerror = () => btnElement.classList.remove('playing');

    window.speechSynthesis.speak(utterance);
}
