import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { db } from './db.js';
import canvasRoutes from './routes/canvases.js';
import nodeRoutes from './routes/nodes.js';
import connectionRoutes from './routes/connections.js';
import snapshotRoutes from './routes/snapshots.js';
import chatProxyRoutes from './routes/chatProxy.js';
import aiFeaturesRoutes from './routes/aiFeatures.js';
import autoActionsRoutes from './routes/autoActions.js';
import agentsRoutes from './routes/agents.js';

dotenv.config({ path: '../.env' });

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors({
    origin: 'http://localhost:5173', // Frontend URL
    credentials: true,
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging middleware
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// Routes
app.use('/api/canvases', canvasRoutes);
app.use('/api/nodes', nodeRoutes);
app.use('/api/connections', connectionRoutes);
app.use('/api/snapshots', snapshotRoutes);
app.use('/api/chat', chatProxyRoutes);
app.use('/api/ai', aiFeaturesRoutes);
app.use('/api/canvas', autoActionsRoutes);
app.use('/api/agents', agentsRoutes);

// Health check endpoint
app.get('/health', async (req, res) => {
    try {
        await db.query('SELECT 1');
        res.json({
            status: 'ok',
            database: 'connected',
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Health check failed:', error);
        res.status(500).json({
            status: 'error',
            database: 'disconnected',
            error: error instanceof Error ? error.message : 'Unknown error'
        });
    }
});

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        name: 'Via Canvas API',
        version: '1.0.0',
        status: 'running',
        endpoints: {
            health: '/health',
            canvases: '/api/canvases',
            nodes: '/api/nodes',
            connections: '/api/connections',
            snapshots: '/api/snapshots',
            chat: '/api/chat',
            ai: '/api/ai',
            canvas: '/api/canvas',
            agents: '/api/agents',
        }
    });
});

// Error handling middleware
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
    console.error('Error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({ error: 'Not found' });
});

// Start server
app.listen(PORT, () => {
    console.log(`\n🚀 Via Canvas API Server`);
    console.log(`   Running on: http://localhost:${PORT}`);
    console.log(`   Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log(`   Database: ${process.env.DB_NAME}@${process.env.DB_HOST}:${process.env.DB_PORT}\n`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('SIGTERM received, closing server...');
    await db.end();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('\nSIGINT received, closing server...');
    await db.end();
    process.exit(0);
});
