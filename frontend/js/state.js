export let chatData = JSON.parse(sessionStorage.getItem('statutiq_chat')) || [];
export let llmContext = JSON.parse(sessionStorage.getItem('statutiq_context')) || [];

export function saveSession() {
    sessionStorage.setItem('statutiq_chat', JSON.stringify(chatData));
    sessionStorage.setItem('statutiq_context', JSON.stringify(llmContext));
}

export function pushChatEntry(entry) {
    chatData.push(entry);
    saveSession();
}

export function pushContext(userQuery, aiAnswer) {
    llmContext.push({ user: userQuery, ai: aiAnswer });
    if (llmContext.length > 2) {
        llmContext.shift(); // Keep only last 2 Q&A pairs
    }
    saveSession();
}
