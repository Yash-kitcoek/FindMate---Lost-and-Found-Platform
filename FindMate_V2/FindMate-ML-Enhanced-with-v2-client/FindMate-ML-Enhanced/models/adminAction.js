const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const adminActionSchema = new Schema({
  adminId: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  actionType: {
    type: String,
    enum: [
      'verify_match',      // Admin verified an ML match as correct
      'reject_match',      // Admin rejected an ML match as incorrect
      'initiate_contact',  // Admin initiated contact between users
      'resolve_match',     // Admin marked match as resolved
      'manual_match',      // Admin manually matched items (without ML)
      'update_status',     // Admin updated item status
      'batch_ml_process'   // Admin ran batch ML matching
    ],
    required: true
  },
  
  // Related entities
  matchId: {
    type: Schema.Types.ObjectId,
    ref: 'MLMatch',
    default: null
  },
  lostItemId: {
    type: Schema.Types.ObjectId,
    ref: 'LostItem',
    default: null
  },
  foundItemId: {
    type: Schema.Types.ObjectId,
    ref: 'FoundItem',
    default: null
  },
  reunitedItemId: {
    type: Schema.Types.ObjectId,
    ref: 'ReunitedItem',
    default: null
  },
  
  // Action details
  notes: {
    type: String,
    default: null
  },
  metadata: {
    type: Schema.Types.Mixed,
    default: {}
  },
  
  // Previous and new values (for status changes)
  previousValue: {
    type: String,
    default: null
  },
  newValue: {
    type: String,
    default: null
  }
}, {
  timestamps: true
});

// Indexes for audit trail queries
adminActionSchema.index({ adminId: 1, createdAt: -1 });
adminActionSchema.index({ actionType: 1, createdAt: -1 });
adminActionSchema.index({ matchId: 1 });
adminActionSchema.index({ lostItemId: 1 });
adminActionSchema.index({ foundItemId: 1 });

// Static Method: Get admin activity summary
adminActionSchema.statics.getAdminSummary = async function(adminId, startDate, endDate) {
  return this.aggregate([
    {
      $match: {
        adminId: mongoose.Types.ObjectId(adminId),
        createdAt: { $gte: startDate, $lte: endDate }
      }
    },
    {
      $group: {
        _id: '$actionType',
        count: { $sum: 1 }
      }
    }
  ]);
};

// Static Method: Get ML matching success rate
adminActionSchema.statics.getMLSuccessRate = async function(startDate, endDate) {
  const verified = await this.countDocuments({
    actionType: 'verify_match',
    createdAt: { $gte: startDate, $lte: endDate }
  });
  
  const rejected = await this.countDocuments({
    actionType: 'reject_match',
    createdAt: { $gte: startDate, $lte: endDate }
  });
  
  const total = verified + rejected;
  return total > 0 ? (verified / total) * 100 : 0;
};

const AdminAction = mongoose.model('AdminAction', adminActionSchema);
module.exports = AdminAction;
