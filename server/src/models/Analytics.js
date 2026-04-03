import mongoose from 'mongoose';

const analyticsSchema = new mongoose.Schema({
  date: { type: Date, required: true, unique: true, index: true },
  totalConversations: { type: Number, default: 0 },
  resolvedCount: { type: Number, default: 0 },
  escalatedCount: { type: Number, default: 0 },
  avgTurnsToResolution: { type: Number, default: 0 },
  avgResponseLatency: { type: Number, default: 0 },
  intentDistribution: { type: Map, of: Number, default: {} },
  languageDistribution: { type: Map, of: Number, default: {} },
  csatAvg: { type: Number, default: 0 },
  topFailedIntents: [{
    intent: String,
    count: Number,
    avgConfidence: Number
  }]
});

export const Analytics = mongoose.model('Analytics', analyticsSchema);
