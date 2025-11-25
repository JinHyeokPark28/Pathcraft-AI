const { contextBridge, ipcRenderer } = require('electron');

// Expose safe APIs to renderer
contextBridge.exposeInMainWorld('pathcraftai', {
    // Send message to main process
    send: (channel, data) => {
        const validChannels = ['whisper-copy', 'item-select', 'search-complete'];
        if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, data);
        }
    },

    // Receive message from main process
    receive: (channel, func) => {
        const validChannels = ['navigation-update', 'search-result'];
        if (validChannels.includes(channel)) {
            ipcRenderer.on(channel, (event, ...args) => func(...args));
        }
    },

    // Get current URL
    getCurrentUrl: () => window.location.href,

    // Copy whisper message
    copyWhisper: () => {
        const whisperBtn = document.querySelector('.whisper-btn');
        if (whisperBtn) {
            whisperBtn.click();
            return true;
        }
        return false;
    }
});
