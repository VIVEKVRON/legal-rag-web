import { DOM_ELEMENTS } from './config.js';
import { chatData } from './state.js';
import { speakText } from './speech.js';

export function renderSourcesUI(sources) {
    if (!DOM_ELEMENTS.sourcesBox) return;
    DOM_ELEMENTS.sourcesBox.innerHTML = '';
    if (sources && sources.length > 0) {
        sources.forEach((source, index) => {
            const rawSourceTitle = source.doc_id || source.source || "Statutory Reference";
            const cleanDocTitle = rawSourceTitle.replace(/_/g, ' ');
            let rankDisplay = source.score !== undefined ? `Rank ${index + 1} (${source.score.toFixed(2)})` : `Rank ${index + 1}`;

            DOM_ELEMENTS.sourcesBox.innerHTML += `
                <div class="source-card">
                    <div class="source-badge">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                        </svg>
                        ${rankDisplay}
                    </div>
                    <div class="source-title">${cleanDocTitle}</div>
                    <div class="source-snippet">${source.text}</div>
                </div>
            `;
        });
    } else {
        DOM_ELEMENTS.sourcesBox.innerHTML = `
            <div class="empty-state">
                <p>No matching sources found.</p>
                <p class="sub-text">Awaiting research query.</p>
            </div>
        `;
    }
}

export function renderChat() {
    if (!DOM_ELEMENTS.chatBox) return;
    DOM_ELEMENTS.chatBox.innerHTML = `
        <div class="message ai-message">
            <div class="message-content">
                <p>Hello. I am <strong>StatutIQ</strong>, your AI legal companion. How can I assist you with statutory research today?</p>
            </div>
        </div>
    `;

    chatData.forEach(item => {
        // User message
        DOM_ELEMENTS.chatBox.innerHTML += `
            <div class="message user-message">
                <div class="message-content">${item.query}</div>
            </div>
        `;

        // AI message
        const speakerBtnId = 'speaker-' + item.id;
        DOM_ELEMENTS.chatBox.innerHTML += `
            <div class="message ai-message">
                <div class="message-content">
                    <div class="message-header">
                        <button class="speaker-btn" id="${speakerBtnId}" title="Read aloud">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                            </svg>
                            Listen
                        </button>
                    </div>
                    ${item.htmlAnswer}
                </div>
            </div>
        `;
        
        setTimeout(() => {
            const btn = document.getElementById(speakerBtnId);
            if (btn && DOM_ELEMENTS.langSelect) btn.addEventListener('click', () => speakText(item.rawAnswer, DOM_ELEMENTS.langSelect.value, btn));
        }, 0);
    });

    if (chatData.length > 0) {
        renderSourcesUI(chatData[chatData.length - 1].sources);
    } else {
        renderSourcesUI([]);
    }
    DOM_ELEMENTS.chatBox.scrollTop = DOM_ELEMENTS.chatBox.scrollHeight;
}

export function addLoadingIndicator() {
    const loadingId = 'loading-' + Date.now();
    DOM_ELEMENTS.chatBox.innerHTML += `
        <div id="${loadingId}" class="message ai-message">
            <div class="message-content">
                <div class="loading-indicator">
                    <div class="orange-pulse"></div>
                    <div class="loading-text">Synthesizing intelligence...</div>
                </div>
            </div>
        </div>
    `;
    DOM_ELEMENTS.chatBox.scrollTop = DOM_ELEMENTS.chatBox.scrollHeight;
    return loadingId;
}

export function removeElementById(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

export function renderUserMessage(query) {
    DOM_ELEMENTS.chatBox.innerHTML += `
        <div class="message user-message">
            <div class="message-content">${query}</div>
        </div>
    `;
    DOM_ELEMENTS.chatBox.scrollTop = DOM_ELEMENTS.chatBox.scrollHeight;
}

export function renderAIMessage(entryId, formattedAnswer, rawAnswer) {
    const speakerBtnId = 'speaker-' + entryId;
    DOM_ELEMENTS.chatBox.innerHTML += `
        <div class="message ai-message">
            <div class="message-content">
                <div class="message-header">
                    <button class="speaker-btn" id="${speakerBtnId}" title="Read aloud">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                        </svg>
                        Listen
                    </button>
                </div>
                ${formattedAnswer}
            </div>
        </div>
    `;
    DOM_ELEMENTS.chatBox.scrollTop = DOM_ELEMENTS.chatBox.scrollHeight;

    setTimeout(() => {
        const btn = document.getElementById(speakerBtnId);
        if (btn && DOM_ELEMENTS.langSelect) btn.addEventListener('click', () => speakText(rawAnswer, DOM_ELEMENTS.langSelect.value, btn));
    }, 0);
}

export function renderError(message) {
    DOM_ELEMENTS.chatBox.innerHTML += `
        <div class="message ai-message">
            <div class="message-content" style="border-left: 3px solid #ff5722; color: #ff5722;">
                <strong>Error:</strong> ${message}
            </div>
        </div>
    `;
    DOM_ELEMENTS.chatBox.scrollTop = DOM_ELEMENTS.chatBox.scrollHeight;
}
