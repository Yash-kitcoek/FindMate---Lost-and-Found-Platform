const mongoose = require('mongoose');
const User = require('./user');

const reunitedItemSchema = new mongoose.Schema({
  itemName: { 
    type: String, 
    required: true 
  },
  description: String,
  category: String,
  photoUrl: String,
  user: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'User' 
  },
  finder: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'User' 
  },
  lostLocation: String,
  foundLocation: String,
  lostDate: Date,
  foundDate: Date,
  reunitedAt: { 
    type: Date, 
    default: Date.now 
  },
  // ML Matching Tracking Fields
  wasMLMatched: {
    type: Boolean,
    default: false
  },
  mlMatchId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'MLMatch',
    default: null
  },
  mlConfidenceScore: {
    type: Number,
    min: 0,
    max: 1,
    default: null
  },
  verifiedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    default: null
  },
  originalLostItemId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'LostItem',
    default: null
  },
  originalFoundItemId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'FoundItem',
    default: null
  },
  adminNotes: {
    type: String,
    default: null
  }
});

// Indexes for analytics
reunitedItemSchema.index({ wasMLMatched: 1, reunitedAt: -1 });
reunitedItemSchema.index({ verifiedBy: 1 });

module.exports = mongoose.model('ReunitedItem', reunitedItemSchema);
