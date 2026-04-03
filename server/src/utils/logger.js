import winston from 'winston';

const { combine, timestamp, printf, colorize } = winston.format;

const customFormat = printf(({ level, message, timestamp, requestId, userId, sessionId, latency_ms }) => {
  let log = `${timestamp} [${level}]: ${message}`;
  if (requestId) log += ` | reqId: ${requestId}`;
  if (userId) log += ` | userId: ${userId}`;
  if (sessionId) log += ` | session: ${sessionId}`;
  if (latency_ms) log += ` | latency: ${latency_ms}ms`;
  return log;
});

const logger = winston.createLogger({
  level: process.env.NODE_ENV === 'development' ? 'debug' : 'info',
  format: combine(
    timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.json() // Production format JSON
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// If we're not in production then log to the `console` with the format:
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: combine(
      colorize(),
      timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      customFormat
    )
  }));
}

export default logger;
