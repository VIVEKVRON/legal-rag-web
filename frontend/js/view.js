import { DOM_ELEMENTS } from './config.js';
import { renderChat } from './render.js';

export function setupViewToggles() {
    if (DOM_ELEMENTS.enterTerminalBtn) {
        DOM_ELEMENTS.enterTerminalBtn.addEventListener('click', () => {
            if(DOM_ELEMENTS.homeView) DOM_ELEMENTS.homeView.style.display = 'none';
            if(DOM_ELEMENTS.chatView) DOM_ELEMENTS.chatView.style.display = 'flex';
            renderChat(); // Load session memory
        });
    }

    if (DOM_ELEMENTS.homeLogo) {
        DOM_ELEMENTS.homeLogo.addEventListener('click', () => {
            if(DOM_ELEMENTS.chatView) DOM_ELEMENTS.chatView.style.display = 'none';
            if(DOM_ELEMENTS.homeView) DOM_ELEMENTS.homeView.style.display = 'flex';
        });
    }
}
