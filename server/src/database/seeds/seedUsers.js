import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';
import dotenv from 'dotenv';
import { User } from '../../models/User.js';
import { connectMongo } from '../mongoose.js';

dotenv.config();

const seedUsers = async () => {
  try {
    await connectMongo();
    await User.deleteMany({});
    
    const passwordHash = await bcrypt.hash('password123', 12);
    
    const users = [
      {
        userId: 'usr_mock_1',
        email: 'john.doe@example.com',
        passwordHash,
        fullName: 'John Doe',
        phone: '+1234567890',
        loyaltyTier: 'Gold',
        milesBalance: 45000,
        totalFlights: 12,
        preferences: {
          seatPreference: 'window',
          mealPreference: 'vegetarian',
          notificationEnabled: true
        }
      },
      {
        userId: 'usr_mock_2',
        email: 'jane.smith@example.com',
        passwordHash,
        fullName: 'Jane Smith',
        phone: '+0987654321',
        loyaltyTier: 'Platinum',
        milesBalance: 120000,
        totalFlights: 45,
        preferences: {
          seatPreference: 'aisle',
          mealPreference: 'standard',
          notificationEnabled: true
        }
      }
    ];

    await User.insertMany(users);
    console.log('Successfully seeded users!');
    process.exit(0);
  } catch (error) {
    console.error('Error seeding users:', error);
    process.exit(1);
  }
};

seedUsers();
