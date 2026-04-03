import { Server } from 'socket.io';
import logger from '../utils/logger.js';
import axios from 'axios';

let io;

export const initSocket = (server) => {
  io = new Server(server, {
    cors: {
      origin: process.env.VITE_API_URL || "http://localhost:5173",
      methods: ["GET", "POST"]
    }
  });

  io.on('connection', (socket) => {
    logger.info(`New client connected: ${socket.id}`);
    
    // Authenticate and join personal room
    socket.on('authenticate', (data) => {
      const { sessionId, userId } = data;
      if (sessionId) {
        socket.join(sessionId);
        logger.info(`Socket ${socket.id} joined personal room: ${sessionId}`);
      }
    });

    socket.on('chat:message', async (data) => {
      const { sessionId, message, language = 'en' } = data;
      logger.info(`Received chat:message from ${sessionId}: ${message}`);
      
      try {
        // Here we simulate the parallel pipeline logic before proxying to the AI-Engine
        // Real implementation hits the FastAPI POST /chat endpoint which returns SSE
        // For demonstration, we'll emit 'chat:token' back
        
        socket.emit('chat:token', { token: "I'm " });
        socket.emit('chat:token', { token: "checking " });
        socket.emit('chat:token', { token: "that " });
        socket.emit('chat:token', { token: "for " });
        socket.emit('chat:token', { token: "you. " });
        
        // Final completion event
        setTimeout(() => {
           socket.emit('chat:complete', { status: 'success' });
        }, 500);

      } catch (err) {
        logger.error(`Error processing chat message: ${err.message}`);
        socket.emit('chat:error', { message: 'Sorry, I am having trouble connecting.' });
      }
    });

    socket.on('disconnect', () => {
      logger.info(`Client disconnected: ${socket.id}`);
    });
  });

  return io;
};

export const getIO = () => {
  if (!io) {
    throw new Error("Socket.io not initialized!");
  }
  return io;
};
