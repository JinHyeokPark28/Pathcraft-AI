const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const net = require('net');

// Configuration
const CONFIG = {
    IPC_PORT: 47851,
    MEMORY_CHECK_INTERVAL: 30000,  // 30 seconds
    MEMORY_THRESHOLD_MB: 800,
    IDLE_TIMEOUT_MS: 5 * 60 * 1000,  // 5 minutes
    CACHE_CLEANUP_INTERVAL: 60000    // 1 minute
};

// State
let mainWindow = null;
let ipcServer = null;
let lastActivityTime = Date.now();
let idleCheckInterval = null;
let memoryCheckInterval = null;

// Cache system (3-tier: Hot/Warm/Cold)
const cache = {
    hot: new Map(),    // Recent, frequently accessed (< 1 min)
    warm: new Map(),   // Medium access (1-5 min)
    cold: new Map()    // Rarely accessed (5+ min)
};

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        show: false,  // Hidden by default (lazy loading)
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: 'PathcraftAI Trade'
    });

    // Load POE Trade
    mainWindow.loadURL('https://www.pathofexile.com/trade');

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Update activity on any window interaction
    mainWindow.webContents.on('did-finish-load', () => {
        updateActivity();
    });

    return mainWindow;
}

function updateActivity() {
    lastActivityTime = Date.now();
}

function checkIdleTimeout() {
    const idleTime = Date.now() - lastActivityTime;
    if (idleTime >= CONFIG.IDLE_TIMEOUT_MS) {
        console.log(`Idle timeout reached (${Math.floor(idleTime / 1000)}s). Shutting down...`);
        gracefulShutdown();
    }
}

function checkMemoryUsage() {
    const memoryUsage = process.memoryUsage();
    const heapUsedMB = Math.round(memoryUsage.heapUsed / 1024 / 1024);
    const totalMB = Math.round((memoryUsage.heapUsed + memoryUsage.external) / 1024 / 1024);

    console.log(`Memory usage: ${totalMB}MB (heap: ${heapUsedMB}MB)`);

    if (totalMB >= CONFIG.MEMORY_THRESHOLD_MB) {
        console.warn(`Memory threshold exceeded (${totalMB}MB >= ${CONFIG.MEMORY_THRESHOLD_MB}MB)`);

        // Clear caches
        cache.cold.clear();
        cache.warm.clear();

        // Force garbage collection if available
        if (global.gc) {
            global.gc();
        }

        // If still over threshold, shutdown
        const afterGC = process.memoryUsage();
        const afterTotalMB = Math.round((afterGC.heapUsed + afterGC.external) / 1024 / 1024);

        if (afterTotalMB >= CONFIG.MEMORY_THRESHOLD_MB) {
            console.error(`Memory still high after cleanup (${afterTotalMB}MB). Shutting down...`);
            gracefulShutdown();
        }
    }
}

function cleanupCache() {
    const now = Date.now();

    // Move hot -> warm (items older than 1 min)
    for (const [key, value] of cache.hot) {
        if (now - value.timestamp > 60000) {
            cache.warm.set(key, value);
            cache.hot.delete(key);
        }
    }

    // Move warm -> cold (items older than 5 min)
    for (const [key, value] of cache.warm) {
        if (now - value.timestamp > 300000) {
            cache.cold.set(key, value);
            cache.warm.delete(key);
        }
    }

    // Remove cold items older than 30 min
    for (const [key, value] of cache.cold) {
        if (now - value.timestamp > 1800000) {
            cache.cold.delete(key);
        }
    }
}

function startIPCServer() {
    ipcServer = net.createServer((socket) => {
        console.log('IPC client connected');
        updateActivity();

        let buffer = '';

        socket.on('data', (data) => {
            buffer += data.toString();

            // Process complete JSON-RPC messages
            let newlineIndex;
            while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
                const message = buffer.substring(0, newlineIndex);
                buffer = buffer.substring(newlineIndex + 1);

                try {
                    const request = JSON.parse(message);
                    handleIPCRequest(request, socket);
                } catch (err) {
                    sendIPCError(socket, null, -32700, 'Parse error');
                }
            }
        });

        socket.on('close', () => {
            console.log('IPC client disconnected');
        });

        socket.on('error', (err) => {
            console.error('Socket error:', err);
        });
    });

    ipcServer.listen(CONFIG.IPC_PORT, '127.0.0.1', () => {
        console.log(`IPC server listening on port ${CONFIG.IPC_PORT}`);
    });

    ipcServer.on('error', (err) => {
        console.error('IPC server error:', err);
    });
}

async function handleIPCRequest(request, socket) {
    updateActivity();

    const { id, method, params } = request;

    try {
        let result;

        switch (method) {
            case 'ping':
                result = { status: 'alive', timestamp: Date.now() };
                break;

            case 'show':
                if (mainWindow) {
                    mainWindow.show();
                    result = { success: true };
                } else {
                    createWindow();
                    mainWindow.show();
                    result = { success: true, created: true };
                }
                break;

            case 'hide':
                if (mainWindow) {
                    mainWindow.hide();
                    result = { success: true };
                } else {
                    result = { success: false, error: 'No window' };
                }
                break;

            case 'navigate':
                if (!mainWindow) {
                    createWindow();
                }
                mainWindow.loadURL(params.url);
                mainWindow.show();
                result = { success: true, url: params.url };
                break;

            case 'search':
                if (!mainWindow) {
                    createWindow();
                }
                const searchUrl = buildSearchUrl(params);
                mainWindow.loadURL(searchUrl);
                mainWindow.show();
                result = { success: true, url: searchUrl };
                break;

            case 'getMemory':
                const mem = process.memoryUsage();
                result = {
                    heapUsed: Math.round(mem.heapUsed / 1024 / 1024),
                    external: Math.round(mem.external / 1024 / 1024),
                    total: Math.round((mem.heapUsed + mem.external) / 1024 / 1024)
                };
                break;

            case 'getCache':
                result = {
                    hot: cache.hot.size,
                    warm: cache.warm.size,
                    cold: cache.cold.size
                };
                break;

            case 'clearCache':
                cache.hot.clear();
                cache.warm.clear();
                cache.cold.clear();
                result = { success: true };
                break;

            case 'setCache':
                cache.hot.set(params.key, {
                    data: params.value,
                    timestamp: Date.now()
                });
                result = { success: true };
                break;

            case 'getCacheItem':
                let cacheResult = cache.hot.get(params.key)
                    || cache.warm.get(params.key)
                    || cache.cold.get(params.key);
                result = cacheResult ? cacheResult.data : null;
                break;

            case 'shutdown':
                sendIPCResponse(socket, id, { success: true, message: 'Shutting down...' });
                gracefulShutdown();
                return;

            case 'setLeague':
                // Store league setting
                result = { success: true, league: params.league };
                break;

            default:
                sendIPCError(socket, id, -32601, `Method not found: ${method}`);
                return;
        }

        sendIPCResponse(socket, id, result);
    } catch (err) {
        sendIPCError(socket, id, -32603, err.message);
    }
}

function buildSearchUrl(params) {
    const { league = 'Keepers', itemName, itemType, links, influence, corrupted, keystone, foulborn } = params;

    // Basic search URL
    let url = `https://www.pathofexile.com/trade/search/${league}`;

    // For complex queries, we'd need to use the trade API
    // For now, return basic URL - C# side should handle query building
    if (params.queryId) {
        url += `/${params.queryId}`;
    }

    return url;
}

function sendIPCResponse(socket, id, result) {
    const response = JSON.stringify({
        jsonrpc: '2.0',
        id,
        result
    });
    socket.write(response + '\n');
}

function sendIPCError(socket, id, code, message) {
    const response = JSON.stringify({
        jsonrpc: '2.0',
        id,
        error: { code, message }
    });
    socket.write(response + '\n');
}

function gracefulShutdown() {
    console.log('Graceful shutdown initiated...');

    // Stop intervals
    if (idleCheckInterval) clearInterval(idleCheckInterval);
    if (memoryCheckInterval) clearInterval(memoryCheckInterval);

    // Close IPC server
    if (ipcServer) {
        ipcServer.close();
    }

    // Close window
    if (mainWindow) {
        mainWindow.close();
    }

    app.quit();
}

// App lifecycle
app.whenReady().then(() => {
    // Don't create window immediately (lazy loading)
    // Window will be created when requested via IPC

    startIPCServer();

    // Start monitoring
    idleCheckInterval = setInterval(checkIdleTimeout, 30000);
    memoryCheckInterval = setInterval(checkMemoryUsage, CONFIG.MEMORY_CHECK_INTERVAL);
    setInterval(cleanupCache, CONFIG.CACHE_CLEANUP_INTERVAL);

    console.log('PathcraftAI Electron module started');
    console.log(`IPC Port: ${CONFIG.IPC_PORT}`);
    console.log(`Memory Threshold: ${CONFIG.MEMORY_THRESHOLD_MB}MB`);
    console.log(`Idle Timeout: ${CONFIG.IDLE_TIMEOUT_MS / 1000}s`);
});

app.on('window-all-closed', () => {
    // Don't quit when all windows are closed (headless mode)
    // Only quit via IPC command or idle timeout
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

// Handle process signals
process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// Export for testing
module.exports = { CONFIG, cache };
