const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const lostItemSchema = new Schema({
    user: {
        type: Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    itemName: {
        type: String,
        required: [true, 'Item name is required'],
        trim: true
    },
    category: {
        type: String,
        required: [true, 'Category is required'],
        enum: ['electronics', 'clothing', 'accessories', 'documents', 'keys', 'jewelry', 'bags', 'other']
    },
    description: {
        type: String,
        required: [true, 'Description is required']
    },
    photoUrl: {
        type: String
    },
    color: {
        type: String,
        trim: true
    },
    brand: {
        type: String,
        trim: true
    },
    lostLocation: {
        type: String,
        required: [true, 'location is required'],
        enum: ['BSH-Department', 'CIVIL-Department','BIOTECH-Department','ENTC-Department','Ground','Library','AIML-building', 'South-enclave', 'North-enclave','boys-hostel', 'Girls-hostel','MBA-building','other']
    },
    lostDate: {
        type: Date,
        required: [true, 'Lost date is required']
    },
    status: {
        type: String,
        enum: ['lost', 'reunited', 'matched', 'resolved', 'closed'],
        default: 'lost'
    },
    additionalNotes: {
        type: String
    },
    // ML Matching Fields
    mlMatchStatus: {
        type: String,
        enum: ['no_match', 'pending_match', 'verified_match'],
        default: 'no_match'
    },
    matchedWithFoundId: {
        type: Schema.Types.ObjectId,
        ref: 'FoundItem',
        default: null
    },
    matchedAt: {
        type: Date,
        default: null
    },
    matchConfidenceScore: {
        type: Number,
        min: 0,
        max: 1,
        default: null
    }
}, {
    timestamps: true
});

// Indexes for performance
lostItemSchema.index({ status: 1, mlMatchStatus: 1 });
lostItemSchema.index({ user: 1, status: 1 });
lostItemSchema.index({ category: 1, lostLocation: 1 });

const LostItem = mongoose.model('LostItem', lostItemSchema);
module.exports = LostItem;
