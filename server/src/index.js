import http from 'http';
import app from './app.js';
import { connectMongo } from './database/mongoose.js';
import { initPostgres } from './database/postgres.js';
import { initSocket } from './socket/socketManager.js';
import logger from './utils/logger.js';
import dotenv from 'dotenv';

dotenv.config();

const PORT = process.env.PORT || 3000;

// Set up server
const server = http.createServer(app);

// Initialize Websockets
initSocket(server);

// Boot sequence
const startServer = async () => {
  try {
    logger.info('Starting FlightBot AI Gateway Server...');
    
    // Connect to databases
    await connectMongo();
    await initPostgres();
    // Redis connects automatically on import

    server.listen(PORT, () => {
      logger.info(`Server is running on port ${PORT}`);
    });
    
  } catch (err) {
    logger.error(`Critical Failure during startup: ${err.message}`);
    process.exit(1);
  }
};

startServer();
