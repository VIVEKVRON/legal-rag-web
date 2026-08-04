document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const homeView = document.getElementById('home-view');
    const chatView = document.getElementById('chat-view');
    const enterTerminalBtn = document.getElementById('enter-terminal-btn');
    const homeLogo = document.getElementById('home-logo');

    const langSelect = document.getElementById('language-select');
    const micBtn = document.getElementById('mic-btn');
    const inputField = document.getElementById('user-input');
    const submitBtn = document.getElementById('submit-btn');
    const chatBox = document.getElementById('chat-box');
    const sourcesBox = document.getElementById('sources-box');

    // --- Session State ---
    let chatData = JSON.parse(sessionStorage.getItem('statutiq_chat')) || [];
    let llmContext = JSON.parse(sessionStorage.getItem('statutiq_context')) || [];

    function saveSession() {
        sessionStorage.setItem('statutiq_chat', JSON.stringify(chatData));
        sessionStorage.setItem('statutiq_context', JSON.stringify(llmContext));
    }

    // --- SPA Toggling ---
    if (enterTerminalBtn) {
        enterTerminalBtn.addEventListener('click', () => {
            homeView.style.display = 'none';
            chatView.style.display = 'flex';
            renderChat(); // Load session memory
        });
    }

    if (homeLogo) {
        homeLogo.addEventListener('click', () => {
            chatView.style.display = 'none';
            homeView.style.display = 'flex';
        });
    }

    // --- Speech-to-Text (STT) Setup ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition = null;
    let isRecording = false;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            micBtn.classList.add('recording');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            inputField.value = inputField.value ? inputField.value + ' ' + transcript : transcript;
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            isRecording = false;
            micBtn.classList.remove('recording');
        };

        recognition.onend = () => {
            isRecording = false;
            micBtn.classList.remove('recording');
        };

        if (micBtn) {
            micBtn.addEventListener('click', () => {
                if (isRecording) {
                    recognition.stop();
                } else {
                    recognition.lang = langSelect.value;
                    recognition.start();
                }
            });
        }
    } else {
        if (micBtn) micBtn.style.display = 'none';
    }

    // --- Text-to-Speech (TTS) Setup ---
    function speakText(text, lang, btnElement) {
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

    // --- Rendering UI from State ---
    function renderChat() {
        chatBox.innerHTML = `
            <div class="message ai-message">
                <div class="message-content">
                    <p>Hello. I am <strong>StatutIQ</strong>, your AI legal companion. How can I assist you with statutory research today?</p>
                </div>
            </div>
        `;

        chatData.forEach(item => {
            // User message
            chatBox.innerHTML += `
                <div class="message user-message">
                    <div class="message-content">${item.query}</div>
                </div>
            `;

            // AI message
            const speakerBtnId = 'speaker-' + item.id;
            chatBox.innerHTML += `
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
                if (btn) btn.addEventListener('click', () => speakText(item.rawAnswer, langSelect.value, btn));
            }, 0);
        });

        if (chatData.length > 0) {
            renderSourcesUI(chatData[chatData.length - 1].sources);
        } else {
            renderSourcesUI([]);
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function renderSourcesUI(sources) {
        sourcesBox.innerHTML = '';
        if (sources && sources.length > 0) {
            sources.forEach((source, index) => {
                const rawSourceTitle = source.doc_id || source.source || "Statutory Reference";
                const cleanDocTitle = rawSourceTitle.replace(/_/g, ' ');
                let rankDisplay = source.score !== undefined ? `Rank ${index + 1} (${source.score.toFixed(2)})` : `Rank ${index + 1}`;

                sourcesBox.innerHTML += `
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
            sourcesBox.innerHTML = `
                <div class="empty-state">
                    <p>No matching sources found.</p>
                    <p class="sub-text">Awaiting research query.</p>
                </div>
            `;
        }
    }


    // --- Form Submission & API Fetch ---
    const queryForm = document.getElementById('query-form');
    if (queryForm) {
        queryForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const query = inputField.value.trim();
            if (!query) return;

            // Display User Question instantly
            chatBox.innerHTML += `
                <div class="message user-message">
                    <div class="message-content">
                        ${query}
                    </div>
                </div>
            `;
            inputField.value = '';
            submitBtn.disabled = true;
            submitBtn.innerText = '...';
            
            // Add loading indicator
            const loadingId = 'loading-' + Date.now();
            chatBox.innerHTML += `
                <div id="${loadingId}" class="message ai-message">
                    <div class="message-content">
                        <div class="loading-indicator">
                            <div class="orange-pulse"></div>
                            <div class="loading-text">Synthesizing intelligence...</div>
                        </div>
                    </div>
                </div>
            `;
            chatBox.scrollTop = chatBox.scrollHeight;

            // Backend Workaround: Maintain Context & Language via hidden Prompt Injection
            const selectedLang = langSelect.value;
            let stringifiedHistory = llmContext.length > 0 
                ? llmContext.map(c => `User: ${c.user} | AI: ${c.ai}`).join(' || ') 
                : "None";

            let finalQuery = query + `\n\n(SYSTEM: Previous context for this conversation: ${stringifiedHistory} | Output language: ${selectedLang})`;

            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: finalQuery })
                });

                const data = await response.json();
                
                // Remove loading indicator
                const loadingElement = document.getElementById(loadingId);
                if (loadingElement) loadingElement.remove();

                if (!response.ok) throw new Error(data.detail || "Server Error");

                // Parse AI answer
                const rawAnswer = data.answer;
                const formattedAnswer = typeof marked !== 'undefined' ? marked.parse(rawAnswer) : rawAnswer;
                
                // Update State
                const entryId = Date.now();
                chatData.push({
                    id: entryId,
                    query: query,
                    rawAnswer: rawAnswer,
                    htmlAnswer: formattedAnswer,
                    sources: data.sources || []
                });

                llmContext.push({ user: query, ai: rawAnswer });
                if (llmContext.length > 2) {
                    llmContext.shift(); // Keep only last 2 Q&A pairs
                }
                
                saveSession();

                // Render newly added AI Answer
                const speakerBtnId = 'speaker-' + entryId;
                chatBox.innerHTML += `
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
                chatBox.scrollTop = chatBox.scrollHeight;

                setTimeout(() => {
                    const btn = document.getElementById(speakerBtnId);
                    if (btn) btn.addEventListener('click', () => speakText(rawAnswer, selectedLang, btn));
                }, 0);

                // Display Sources
                renderSourcesUI(data.sources || []);

            } catch (error) {
                const loadingElement = document.getElementById(loadingId);
                if (loadingElement) loadingElement.remove();
                
                chatBox.innerHTML += `
                    <div class="message ai-message">
                        <div class="message-content" style="border-left: 3px solid #ff5722; color: #ff5722;">
                            <strong>Error:</strong> Failed to fetch response. (${error.message})
                        </div>
                    </div>
                `;
                chatBox.scrollTop = chatBox.scrollHeight;
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Ask';
                inputField.focus();
            }
        });
    }
});