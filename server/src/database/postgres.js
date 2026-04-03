import pg from 'pg';
import logger from '../utils/logger.js';
import dotenv from 'dotenv';

dotenv.config();

const { Pool } = pg;

const postgresUri = process.env.POSTGRES_URI;

export const pgPool = new Pool({
  connectionString: postgresUri || 'postgresql://postgres:postgres@localhost:5432/flightbot',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pgPool.on('connect', () => {
  logger.info('PostgreSQL connected successfully');
});

pgPool.on('error', (err) => {
  logger.error('Unexpected error on idle PostgreSQL client', err);
  process.exit(-1);
});

export const initPostgres = async () => {
  const client = await pgPool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS flights (
        flight_number VARCHAR(10) PRIMARY KEY,
        origin VARCHAR(3) NOT NULL,
        destination VARCHAR(3) NOT NULL,
        departure TIMESTAMPTZ NOT NULL,
        arrival TIMESTAMPTZ NOT NULL,
        aircraft VARCHAR(50),
        status VARCHAR(20) CHECK (status IN ('scheduled','delayed','cancelled','landed')),
        gate VARCHAR(10),
        terminal VARCHAR(10)
      );
      CREATE INDEX IF NOT EXISTS idx_flights_route ON flights(origin, destination, departure);

      CREATE TABLE IF NOT EXISTS loyalty_accounts (
        account_id SERIAL PRIMARY KEY,
        user_id VARCHAR(50) NOT NULL UNIQUE,
        tier VARCHAR(20) NOT NULL,
        miles_balance INTEGER DEFAULT 0,
        tier_expiry TIMESTAMPTZ,
        lifetime_miles INTEGER DEFAULT 0,
        last_activity TIMESTAMPTZ
      );
      CREATE INDEX IF NOT EXISTS idx_loyalty_user ON loyalty_accounts(user_id);

      CREATE TABLE IF NOT EXISTS upgrade_bids (
        bid_id SERIAL PRIMARY KEY,
        booking_id VARCHAR(50) NOT NULL,
        user_id VARCHAR(50) NOT NULL,
        bid_amount INTEGER NOT NULL,
        currency VARCHAR(3) DEFAULT 'USD',
        probability_score NUMERIC(4,3),
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT NOW()
      );
      CREATE INDEX IF NOT EXISTS idx_upgrade_bids ON upgrade_bids(booking_id, status);

      CREATE TABLE IF NOT EXISTS baggage_rules (
        rule_id SERIAL PRIMARY KEY,
        airline_code VARCHAR(3) NOT NULL,
        cabin_class VARCHAR(20) NOT NULL,
        checked_bags INTEGER NOT NULL,
        max_weight_kg INTEGER NOT NULL,
        carry_on_weight_kg INTEGER NOT NULL,
        excess_fee_per_kg INTEGER NOT NULL,
        UNIQUE (airline_code, cabin_class)
      );
    `);
    logger.info('PostgreSQL schemas initialized');
  } catch (error) {
    logger.error('Failed to initialize PostgreSQL schema:', error);
  } finally {
    client.release();
  }
};
