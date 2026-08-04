let currentActiveDocument = null;

document.getElementById('query-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const inputField = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const sourcesBox = document.getElementById('sources-box');
    const query = inputField.value.trim();

    if (!query) return;

    // 1. Display User Question
    chatBox.innerHTML += `<div class="message user-message"><strong>You:</strong> ${query}</div>`;
    inputField.value = '';
    
    // Add loading indicator
    const loadingId = 'loading-' + Date.now();
    chatBox.innerHTML += `<div id="${loadingId}" class="message ai-message"><em>Searching legal database and generating answer...</em></div>`;
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to bottom

    try {
        // 2. Call the FastAPI Backend
        const requestBody = { query: query };
        if (currentActiveDocument) {
            requestBody.target_doc_id = currentActiveDocument;
        }

        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        
        // Remove loading indicator
        document.getElementById(loadingId).remove();

        if (!response.ok) throw new Error(data.detail || "Server Error");

        // 3. Display AI Answer
        chatBox.innerHTML += `<div class="message ai-message"><strong>AI:</strong> ${data.answer}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

        // 4. Display Retrieved Sources (UPDATED)
        sourcesBox.innerHTML = '';
        if (data.sources && data.sources.length > 0) {
            data.sources.forEach((source, index) => {
                // Convert underscores in doc_id to clean spaces for display
                const cleanDocTitle = source.doc_id.replace(/_/g, ' ');

                sourcesBox.innerHTML += `
                    <div class="source-card">
                        <div class="source-header">Rank ${index + 1} | Score: ${source.score.toFixed(2)}</div>
                        <div class="source-id" style="font-weight: bold; color: #0066cc; margin: 6px 0; font-size: 14px;">
                            📜 Act / Source: ${cleanDocTitle}
                        </div>
                        <div class="source-text">${source.text}</div>
                    </div>
                `;
            });
        } else {
            sourcesBox.innerHTML = '<p class="empty-state">No sources retrieved.</p>';
        }

    } catch (error) {
        document.getElementById(loadingId).remove();
        chatBox.innerHTML += `<div class="message error-message"><strong>Error:</strong> Failed to get response. (${error.message})</div>`;
    }
});

document.getElementById('pdf-upload').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const statusText = document.getElementById('upload-status');
    statusText.innerText = "Uploading and analyzing...";

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            statusText.innerText = "✅ " + data.message;
            currentActiveDocument = data.doc_id;
            statusText.innerText += ` (Now querying: ${currentActiveDocument})`;
        } else {
            statusText.innerText = "❌ " + data.detail;
        }
    } catch (error) {
        statusText.innerText = "❌ Upload failed.";
    }
});