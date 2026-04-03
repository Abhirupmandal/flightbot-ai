import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  userId: { type: String, required: true, unique: true, index: true },
  email: { type: String, required: true, unique: true, lowercase: true, trim: true },
  passwordHash: { type: String, required: true },
  fullName: { type: String, required: true, trim: true },
  phone: { type: String, trim: true },
  preferredLanguage: { type: String, default: 'en' },
  loyaltyTier: { 
    type: String, 
    enum: ['Bronze', 'Silver', 'Gold', 'Platinum'], 
    default: 'Bronze' 
  },
  milesBalance: { type: Number, default: 0 },
  totalFlights: { type: Number, default: 0 },
  lastLogin: { type: Date, default: null },
  preferences: {
    seatPreference: { type: String, enum: ['aisle', 'window', 'middle', 'any'], default: 'any' },
    mealPreference: { type: String, default: 'standard' },
    notificationEnabled: { type: Boolean, default: true }
  }
}, { timestamps: true });

export const User = mongoose.model('User', userSchema);
