import Redis from 'ioredis';
import logger from '../utils/logger.js';
import dotenv from 'dotenv';

dotenv.config();

const redisUri = process.env.REDIS_URI;

if (!redisUri) {
  logger.warn('REDIS_URI is not defined, attempting default localhost Redis connection');
}

export const redisClient = new Redis(redisUri || 'redis://localhost:6379', {
  retryStrategy(times) {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
});

redisClient.on('connect', () => {
  logger.info('Redis connection established successfully');
});

redisClient.on('error', (err) => {
  logger.error('Redis connection error:', err.message);
});
