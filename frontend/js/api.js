import { API_URL } from './config.js';

export async function fetchAnswer(query, selectedLang, llmContext) {
    let stringifiedHistory = llmContext.length > 0 
        ? llmContext.map(c => `User: ${c.user} | AI: ${c.ai}`).join(' || ') 
        : "None";

    let finalQuery = query + `\n\n(SYSTEM: Previous context for this conversation: ${stringifiedHistory} | Output language: ${selectedLang})`;

    const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: finalQuery })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Server Error");
    return data;
}
