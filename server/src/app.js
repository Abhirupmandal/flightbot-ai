import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import logger from './utils/logger.js';
import dotenv from 'dotenv';
// Load environment variables
dotenv.config();

const app = express();

// Security middlewares
app.use(helmet());
app.use(cors({ origin: process.env.VITE_API_URL || 'http://localhost:5173' }));

// Request parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Global Rate limiter
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per `window`
  message: { success: false, error: { code: 'RATE_LIMIT_EXCEEDED', message: 'Too many requests' } },
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api', limiter);

// Request logger middleware
app.use((req, res, next) => {
  req.startTime = Date.now();
  logger.info(`Incoming ${req.method} ${req.originalUrl}`);
  
  res.on('finish', () => {
    const latency = Date.now() - req.startTime;
    logger.info(`Completed ${req.method} ${req.originalUrl} - ${res.statusCode} in ${latency}ms`);
  });
  next();
});

// Basic Health Check Route
app.get('/health', (req, res) => {
  res.status(200).json({ 
    success: true, 
    data: { status: 'ok', timestamp: new Date() },
    error: null,
    meta: { latency_ms: Date.now() - req.startTime }
  });
});

// Placeholder for real routes (auth, chat, admin, etc.)
// app.use('/api/auth', authRoutes);
// app.use('/api/chat', chatRoutes);

// Global Error Handler
app.use((err, req, res, next) => {
  logger.error(err.stack);
  res.status(err.status || 500).json({
    success: false,
    data: null,
    error: {
      code: err.code || 'INTERNAL_ERROR',
      message: err.message || 'An unexpected error occurred'
    },
    meta: {
      requestId: req.headers['x-request-id'],
      timestamp: new Date(),
      latency_ms: Date.now() - req.startTime
    }
  });
});

export default app;
