import { DOM_ELEMENTS } from './config.js';
import { setupViewToggles } from './view.js';
import { setupSpeechRecognition, toggleRecording } from './speech.js';
import { fetchAnswer } from './api.js';
import { llmContext, pushChatEntry, pushContext } from './state.js';
import { renderUserMessage, renderAIMessage, renderSourcesUI, addLoadingIndicator, removeElementById, renderError } from './render.js';

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize View Routing
    setupViewToggles();

    // 2. Initialize Speech Recognition
    setupSpeechRecognition();
    if (DOM_ELEMENTS.micBtn) {
        DOM_ELEMENTS.micBtn.addEventListener('click', toggleRecording);
    }

    // 3. Bind Form Submission
    if (DOM_ELEMENTS.queryForm) {
        DOM_ELEMENTS.queryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const query = DOM_ELEMENTS.inputField.value.trim();
            if (!query) return;

            // Display User Question instantly
            renderUserMessage(query);
            DOM_ELEMENTS.inputField.value = '';
            DOM_ELEMENTS.submitBtn.disabled = true;
            DOM_ELEMENTS.submitBtn.innerText = '...';
            
            const loadingId = addLoadingIndicator();
            const selectedLang = DOM_ELEMENTS.langSelect ? DOM_ELEMENTS.langSelect.value : 'en-IN';

            try {
                const data = await fetchAnswer(query, selectedLang, llmContext);
                
                removeElementById(loadingId);

                // Parse AI answer
                const rawAnswer = data.answer;
                const formattedAnswer = typeof marked !== 'undefined' ? marked.parse(rawAnswer) : rawAnswer;
                
                // Update State
                const entryId = Date.now();
                pushChatEntry({
                    id: entryId,
                    query: query,
                    rawAnswer: rawAnswer,
                    htmlAnswer: formattedAnswer,
                    sources: data.sources || []
                });
                pushContext(query, rawAnswer);

                // Render newly added AI Answer and Sources
                renderAIMessage(entryId, formattedAnswer, rawAnswer);
                renderSourcesUI(data.sources || []);

            } catch (error) {
                removeElementById(loadingId);
                renderError(`Failed to fetch response. (${error.message})`);
            } finally {
                DOM_ELEMENTS.submitBtn.disabled = false;
                DOM_ELEMENTS.submitBtn.innerText = 'Ask';
                DOM_ELEMENTS.inputField.focus();
            }
        });
    }
});
