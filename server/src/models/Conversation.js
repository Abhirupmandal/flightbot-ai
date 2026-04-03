import mongoose from 'mongoose';

const turnSchema = new mongoose.Schema({
  turnId: { type: String, required: true },
  timestamp: { type: Date, default: Date.now },
  userMessage: { type: String, required: true },
  botResponse: { type: String, required: true },
  intent: { type: String },
  confidence: { type: Number },
  entities: { type: mongoose.Schema.Types.Mixed, default: {} },
  sentimentScore: { type: Number },
  responseLatency: { type: Number }, // ms
  ragChunksUsed: { type: Number, default: 0 }
});

const conversationSchema = new mongoose.Schema({
  conversationId: { type: String, required: true, unique: true, index: true },
  userId: { type: String, index: true }, // Optional if guest
  channel: { type: String, default: 'web' },
  language: { type: String, default: 'en' },
  startedAt: { type: Date, default: Date.now },
  endedAt: { type: Date },
  totalTurns: { type: Number, default: 0 },
  resolutionStatus: { 
    type: String, 
    enum: ['resolved', 'escalated', 'abandoned', 'active'],
    default: 'active'
  },
  csatScore: { type: Number, min: 1, max: 5 },
  turns: [turnSchema]
});

export const Conversation = mongoose.model('Conversation', conversationSchema);
