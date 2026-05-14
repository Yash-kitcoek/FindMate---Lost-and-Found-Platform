const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const mlMatchSchema = new Schema({
  // Source item (the one that triggered the match search)
  sourceItemId: {
    type: Schema.Types.ObjectId,
    required: true,
    refPath: 'sourceType'
  },
  sourceType: {
    type: String,
    required: true,
    enum: ['LostItem', 'FoundItem']
  },
  
  // Matched item (the potential match found by ML)
  matchedItemId: {
    type: Schema.Types.ObjectId,
    required: true,
    refPath: 'matchedType'
  },
  matchedType: {
    type: String,
    required: true,
    enum: ['LostItem', 'FoundItem']
  },
  
  // ML matching score and factors
  confidenceScore: {
    type: Number,
    required: true,
    min: 0,
    max: 1
  },
  matchingFactors: {
    categoryMatch: {
      type: Number,
      min: 0,
      max: 1,
      required: true
    },
    descriptionSimilarity: {
      type: Number,
      min: 0,
      max: 1,
      required: true
    },
    locationProximity: {
      type: Number,
      min: 0,
      max: 1,
      required: true
    },
    dateProximity: {
      type: Number,
      min: 0,
      max: 1,
      required: true
    },
    itemNameSimilarity: {
      type: Number,
      min: 0,
      max: 1,
      default: 0
    },
    attributeMatch: {
      type: Number,
      min: 0,
      max: 1,
      default: 0
    },
    objectTypeMatch: {
      type: Number,
      min: 0,
      max: 1,
      default: 0.5
    },
    colorMatch: {
      type: Number,
      min: 0,
      max: 1,
      default: 0.5
    },
    brandMatch: {
      type: Number,
      min: 0,
      max: 1,
      default: 0.5
    },
    modelTokenMatch: {
      type: Number,
      min: 0,
      max: 1,
      default: 0.5
    },
    tokenOverlap: {
      type: Number,
      min: 0,
      max: 1,
      default: 0
    }
  },
  
  // Admin review workflow
  status: {
    type: String,
    enum: ['pending_review', 'verified', 'rejected', 'resolved'],
    default: 'pending_review'
  },
  reviewedBy: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    default: null
  },
  reviewedAt: {
    type: Date,
    default: null
  },
  rejectionReason: {
    type: String,
    default: null
  },
  
  // Contact initiation tracking
  contactInitiated: {
    type: Boolean,
    default: false
  },
  contactInitiatedAt: {
    type: Date,
    default: null
  },
  
  // Link to reunited item if match was successful
  reunitedItemId: {
    type: Schema.Types.ObjectId,
    ref: 'ReunitedItem',
    default: null
  }
}, {
  timestamps: true
});

// Indexes for admin dashboard queries
mlMatchSchema.index({ status: 1, confidenceScore: -1, createdAt: -1 });
mlMatchSchema.index({ sourceItemId: 1 });
mlMatchSchema.index({ matchedItemId: 1 });
mlMatchSchema.index({ reviewedBy: 1, reviewedAt: -1 });
mlMatchSchema.index({ sourceItemId: 1, matchedItemId: 1 });

// Virtual: Get match age in hours
mlMatchSchema.virtual('ageInHours').get(function() {
  return Math.floor((Date.now() - this.createdAt) / (1000 * 60 * 60));
});

// Method: Check if match is high confidence
mlMatchSchema.methods.isHighConfidence = function() {
  return this.confidenceScore >= 0.85;
};

// Method: Check if match is stale (older than 7 days)
mlMatchSchema.methods.isStale = function() {
  const daysSinceCreation = (Date.now() - this.createdAt) / (1000 * 60 * 60 * 24);
  return daysSinceCreation > 7;
};

const MLMatch = mongoose.model('MLMatch', mlMatchSchema);
module.exports = MLMatch;
