const express = require('express');
const { createProxyMiddleware, fixRequestBody } = require('http-proxy-middleware'); // Import fixRequestBody
const cors = require('cors');
const http = require('http'); // For manual proxying
const { URL } = require('url'); // For parsing target URL

const app = express();

const ADK_SERVER_URL_STR = 'http://localhost:8000'; // Your ADK server
const ADK_SERVER_URL = new URL(ADK_SERVER_URL_STR);
const PROXY_PORT = 3000; // Port for this proxy server

// Enable CORS for requests from your Flask app's origin
const allowedOrigins = ['http://localhost:5000', 'http://127.0.0.1:5000'];
app.use(cors({
    origin: function (origin, callback) {
        // allow requests with no origin (like mobile apps or curl requests)
        if (!origin) return callback(null, true);
        if (allowedOrigins.indexOf(origin) === -1) {
            const msg = 'The CORS policy for this site does not allow access from the specified Origin.';
            return callback(new Error(msg), false);
        }
        return callback(null, true);
    }
}));

// Middleware to parse JSON bodies (if any) - good practice to have
app.use(express.json());

// Middleware to log all incoming requests to the proxy server
app.use((req, res, next) => {
    console.log(`[Global Request Logger] Received ${req.method} request for ${req.originalUrl} from origin ${req.headers.origin}`);
    console.log(`[Global Request Logger] Headers:`, JSON.stringify(req.headers, null, 2));
    // fixRequestBody middleware is needed if http-proxy-middleware is used after body-parsing middleware (like express.json())
    // and the proxy target expects a stream. However, we are sending Content-Length: 0.
    // For the manual proxy below, we handle the body (or lack thereof) directly.
    next();
});

// Manual Proxy for /apps/**
app.use('/apps', (clientReq, clientRes) => {
    console.log(`[Manual Proxy /apps] Received ${clientReq.method} for ${clientReq.originalUrl}`);

    const options = {
        hostname: ADK_SERVER_URL.hostname,
        port: ADK_SERVER_URL.port,
        path: clientReq.originalUrl, // Use the originalUrl which includes the full path and query
        method: clientReq.method,
        headers: { ...clientReq.headers } // Clone headers
    };

    // Remove host header as it's set by the http.request itself based on hostname
    delete options.headers.host;
    // Content-Length is also tricky with empty bodies, ensure it's correct or absent if truly empty
    // If clientReq.headers['content-length'] is '0', it's fine.
    // If it was something else and we are not piping body, it needs adjustment.
    // For our specific case (POST with Content-Length: 0), this should be okay.

    console.log(`[Manual Proxy /apps] Options for ADK server:`, JSON.stringify(options, null, 2));

    const proxyReq = http.request(options, (targetRes) => {
        console.log(`[Manual Proxy /apps] Received response from ADK: ${targetRes.statusCode}`);
        clientRes.writeHead(targetRes.statusCode, targetRes.headers);
        targetRes.pipe(clientRes, { end: true });
    });

    proxyReq.on('error', (err) => {
        console.error(`[Manual Proxy /apps] Error connecting to ADK server:`, err);
        if (!clientRes.headersSent) {
            clientRes.writeHead(502, { 'Content-Type': 'text/plain' });
        }
        if (!clientRes.writableEnded) {
            clientRes.end('Proxy error: Could not connect to target server.');
        }
    });

    // For POST/PUT with bodies, you would pipe clientReq to proxyReq
    // if (clientReq.method === 'POST' || clientReq.method === 'PUT') {
    //    clientReq.pipe(proxyReq, { end: true });
    // } else {
    //    proxyReq.end();
    // }
    // Since we know our problematic POST has Content-Length: 0, we just end the request.
    proxyReq.end();
});


// WebSocket proxying using http-proxy-middleware for /run_live
const wsProxy = createProxyMiddleware({
    target: ADK_SERVER_URL_STR, // Target for WebSocket
    ws: true, // Enable WebSocket proxying
    logLevel: 'debug',
    changeOrigin: true,
    onProxyReqWs: (proxyReq, req, socket, options, head) => {
        console.log('[PROXY_DEBUG] [onProxyReqWs] Client Request URL:', req.url);
        console.log('[PROXY_DEBUG] [onProxyReqWs] Client Request Headers:', JSON.stringify(req.headers, null, 2));
        console.log('[PROXY_DEBUG] [onProxyReqWs] Proxy Request Path:', proxyReq.path);
        console.log('[PROXY_DEBUG] [onProxyReqWs] Proxy Request Headers:', JSON.stringify(proxyReq.getHeaders(), null, 2));
    },
    onOpen: (proxySocket) => {
        console.log('[PROXY_DEBUG] [onOpen] WebSocket connection established to target ADK server.');
        proxySocket.on('data', (data) => {
            // Note: This logs raw buffer data. For actual message content, further processing might be needed.
            // console.log('[PROXY_DEBUG] [onOpen - data from ADK] Data chunk length:', data.length);
        });
    },
    onClose: (res, socket, head) => {
        // res is the incoming message (client request), socket is the client socket
        console.log('[PROXY_DEBUG] [onClose] WebSocket connection closed. Client socket readyState:', socket.readyState);
    },
    onError: (err, req, res, target) => {
        console.error('[PROXY_DEBUG] [WS Proxy Error] Error:', err);
        console.error('[PROXY_DEBUG] [WS Proxy Error] Client Request URL:', req.url);
        console.error('[PROXY_DEBUG] [WS Proxy Error] Target URL:', target);
        if (res.writeHead && !res.headersSent) { // For HTTP error before upgrade
            res.writeHead(500, {
                'Content-Type': 'text/plain',
            });
            res.end('WebSocket proxy error.');
        } else if (res.socket && res.socket.writable) { // For WS error after upgrade
             // Attempt to close the client socket if it's still open and writable
            if (res.socket.readyState === 'open') {
                 console.log('[PROXY_DEBUG] [WS Proxy Error] Attempting to close client WebSocket connection.');
                 res.socket.end(); // Or res.socket.destroy();
            }
        }
    }
});
app.use('/run_live', wsProxy);
// New proxy for FastAPI streaming server (ws://localhost:8001)
const fastApiWsProxy = createProxyMiddleware({
    target: 'http://localhost:8001', // Target FastAPI server
    ws: true,
    pathRewrite: {
        '^/ws_stream': '/ws', // Rewrite /ws_stream to /ws on the target
    },
    changeOrigin: true, // Add this
    headers: { // Optionally be explicit, though changeOrigin might be enough
        connection: 'keep-alive', // Important for WebSocket
    },
    logLevel: 'debug',
    onError: (err, req, res, target) => {
        console.error('[PROXY_DEBUG] [/ws_stream] Error:', err);
        console.error('[PROXY_DEBUG] [/ws_stream] Client Request URL:', req.url);
        if (target) {
            console.error('[PROXY_DEBUG] [/ws_stream] Target URL:', typeof target === 'string' ? target : (target.href || target));
        }
        if (res.writeHead && !res.headersSent) {
            res.writeHead(500, {'Content-Type': 'text/plain'});
            res.end('WebSocket proxy error for /ws_stream.');
        } else if (res.socket && res.socket.writable && res.socket.readyState === 'open') {
            console.log('[PROXY_DEBUG] [/ws_stream] Attempting to close client WebSocket connection due to error.');
            res.socket.end();
        }
    },
    onProxyReqWs: (proxyReq, req, socket, options, head) => {
        // Log the origin header being sent to the target
        console.log(`[PROXY_DEBUG] /ws_stream: Proxying WebSocket request for: ${req.url}`);
        console.log(`[PROXY_DEBUG] /ws_stream: Original client Origin header: ${req.headers['origin']}`);
        // http-proxy-middleware should set the Origin header on proxyReq based on the client's req.headers.origin
        // If changeOrigin is true, it might also alter the Host header to match the target.
        // Let's also log what proxyReq has for Origin if possible, though it's a ClientRequest object.
        console.log(`[PROXY_DEBUG] /ws_stream: Outgoing proxyReq Host header: ${proxyReq.getHeader('Host')}`);
        console.log(`[PROXY_DEBUG] /ws_stream: Outgoing proxyReq Origin header: ${proxyReq.getHeader('Origin')}`); // May not be set yet or directly accessible this way
    },
    onOpen: (proxySocket) => {
        console.log('[PROXY_DEBUG] [/ws_stream] WebSocket connection opened to target (FastAPI)');
        proxySocket.on('data', (data) => { // Data from FastAPI (Python Backend)
            // DIAGNOSTIC LOG: Log chunks from Python backend to proxy
            console.log('[PROXY_DEBUG] [/ws_stream] CHUNK FROM FastAPI (Python Backend) TO PROXY:', data.toString('utf-8'));
        });
        proxySocket.on('error', (err) => {
            console.error('[PROXY_DEBUG] [/ws_stream] Error on proxySocket (connection to FastAPI target):', err);
        });
    },
    onClose: (res, socket, head) => {
        console.log('[PROXY_DEBUG] [/ws_stream] WebSocket connection closed. Client socket readyState:', socket.readyState);
    }
});
app.use('/ws_stream', fastApiWsProxy);


const server = app.listen(PROXY_PORT, () => {
    console.log(`ADK Proxy server listening on port ${PROXY_PORT}`);
    console.log(`Manually proxying HTTP requests for /apps/** to ${ADK_SERVER_URL_STR}`);
    console.log(`Proxying WebSocket requests for /run_live to ${ADK_SERVER_URL_STR} using http-proxy-middleware`);
    console.log(`Proxying WebSocket requests for /ws_stream/** to http://localhost:8001 using http-proxy-middleware`);
});

// http-proxy-middleware can also handle upgrades on the main server instance
// if wsProxy is applied to the app instance before server.listen
server.on('upgrade', (req, socket, head) => {
    // Log the upgrade attempt before passing to wsProxy
    console.log(`[Server Upgrade Event] Attempting to upgrade ${req.url}`);
    // Only let wsProxy handle upgrades for its designated path
    if (req.url.startsWith('/run_live')) {
        console.log(`[Server Upgrade Event] Routing ${req.url} to ADK wsProxy.`);
        wsProxy.upgrade(req, socket, head);
    } else if (req.url.startsWith('/ws_stream')) {
        console.log(`[Server Upgrade Event] Routing ${req.url} to FastAPI fastApiWsProxy.`);
        fastApiWsProxy.upgrade(req, socket, head);
    } else {
        // If the upgrade is not for any known WS proxy, destroy the socket
        console.log(`[Server Upgrade Event] URL ${req.url} not for any WS proxy. Destroying socket.`);
        socket.destroy();
    }
});

// To handle WebSockets explicitly if needed (though http-proxy-middleware often handles it)
// const server = app.listen(PROXY_PORT, () => { ... });
// server.on('upgrade', (req, socket, head) => {
//   console.log('Attempting to proxy WebSocket upgrade request for:', req.url);
//   // Manually proxy to ADK_SERVER_URL/run_live if req.url matches /run_live
//   // This is more complex; let's rely on http-proxy-middleware's default ws handling first.
// });
