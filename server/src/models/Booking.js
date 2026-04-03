import mongoose from 'mongoose';

const passengerSchema = new mongoose.Schema({
  name: { type: String, required: true },
  passportNumber: { type: String },
  seatNumber: { type: String }
});

const bookingSchema = new mongoose.Schema({
  bookingId: { type: String, required: true, unique: true, index: true },
  pnr: { type: String, required: true, index: true, uppercase: true, match: /^[A-Z0-9]{6}$/ },
  userId: { type: String, required: true, index: true },
  flightNumber: { type: String, required: true },
  origin: { type: String, required: true, uppercase: true },
  destination: { type: String, required: true, uppercase: true },
  departureTime: { type: Date, required: true },
  arrivalTime: { type: Date, required: true },
  cabinClass: { type: String, enum: ['Economy', 'Premium', 'Business', 'First'], default: 'Economy' },
  passengers: [passengerSchema],
  status: { type: String, enum: ['Confirmed', 'Cancelled', 'Completed'], default: 'Confirmed' },
  totalFare: { type: Number, required: true },
  currency: { type: String, default: 'USD' },
  baggageAllowance: { type: String },
  cancelledAt: { type: Date },
  refundStatus: { type: String, enum: ['None', 'Pending', 'Processed'], default: 'None' },
  refundAmount: { type: Number, default: 0 }
}, { timestamps: true });

export const Booking = mongoose.model('Booking', bookingSchema);
