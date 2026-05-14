const express = require('express');
const router = express.Router();
const MLMatch = require('../models/mlMatch');
const LostItem = require('../models/lostItem');
const FoundItem = require('../models/foundItem');
const AdminAction = require('../models/adminAction');
const notificationService = require('../services/notificationService');
const mlMatchingService = require('../services/mlMatchingService');

const normalizeItemName = (value) => String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();

const itemFamily = (item) => {
    const text = normalizeItemName(`${item?.itemName || ''} ${item?.description || ''}`);
    const families = {
        umbrella: ['umbrella'],
        watch: ['watch', 'wristwatch', 'timepiece', 'titan'],
        audio: ['headset', 'headsets', 'handsset', 'handssets', 'headphone', 'headphones', 'earphone', 'earphones', 'earbud', 'earbuds', 'airpods'],
        phone: ['phone', 'mobile', 'iphone', 'smartphone'],
        bag: ['bag', 'backpack', 'wallet', 'purse'],
        keys: ['key', 'keys', 'keychain'],
        documents: ['id', 'card', 'document', 'license'],
        glasses: ['glasses', 'spectacles', 'specs']
    };

    for (const [family, words] of Object.entries(families)) {
        if (words.some(word => text.includes(word))) {
            return family;
        }
    }

    return null;
};

const isReliableMatchForReview = (match) => {
    const source = match.sourceItemId;
    const matched = match.matchedItemId;
    const sourceName = normalizeItemName(source?.itemName);
    const matchedName = normalizeItemName(matched?.itemName);
    const sourceFamily = itemFamily(source);
    const matchedFamily = itemFamily(matched);

    if (sourceFamily && matchedFamily && sourceFamily !== matchedFamily) {
        return false;
    }

    if (sourceName && matchedName && sourceName !== matchedName) {
        const factors = match.matchingFactors || {};
        const directEvidence = Math.max(
            factors.itemNameSimilarity || 0,
            factors.tokenOverlap || 0
        );

        if (directEvidence < 0.20 && (!sourceFamily || !matchedFamily || sourceFamily !== matchedFamily)) {
            return false;
        }
    }

    return true;
};

// Middleware to check if user is admin
const isAdmin = (req, res, next) => {
    if (!req.isAuthenticated() || req.user.role !== 'admin') {
        return res.redirect('/admin-login');
    }
    next();
};

// ⭐ Get all ML matches for admin review
router.get('/matches', isAdmin, async (req, res) => {
    try {
        const allowedStatuses = ['pending_review', 'verified', 'rejected', 'resolved', 'all'];
        const statusFilter = allowedStatuses.includes(req.query.status) ? req.query.status : 'pending_review';
        const query = statusFilter === 'all' ? {} : { status: statusFilter };

        const matches = await MLMatch.find(query)
            .populate({
                path: 'sourceItemId',
                populate: { path: 'user finder', strictPopulate: false }
            })
            .populate({
                path: 'matchedItemId',
                populate: { path: 'user finder', strictPopulate: false }
            })
            .sort({ confidenceScore: -1, createdAt: -1 })
            .limit(50);

        const reliableMatches = matches.filter(isReliableMatchForReview);
        
        res.render('admin/matches', { 
            matches: reliableMatches,
            user: req.user,
            batchResult: req.query.batch || null,
            statusFilter
        });
        
    } catch (error) {
        console.error('Error fetching ML matches:', error);
        res.status(500).send('Error loading matches');
    }
});

// ⭐ Get detailed view of a specific match
// Run ML matching for all active lost items against all active found items
router.post('/matches/batch-process', isAdmin, async (req, res) => {
    try {
        const summary = await mlMatchingService.batchProcessAllMatches();

        await AdminAction.create({
            adminId: req.user._id,
            actionType: 'batch_ml_process',
            notes: `Processed ${summary.lostItemsProcessed} lost items against ${summary.activeFoundItems} found items. Saved ${summary.matchesSaved} matches. Errors: ${summary.errors}.`
        }).catch(error => {
            console.error('Error logging batch admin action:', error);
        });

        const message = encodeURIComponent(
            `Batch completed: processed ${summary.lostItemsProcessed} lost items vs ${summary.activeFoundItems} found items, saved ${summary.matchesSaved} matches.`
        );

        res.redirect(`/admin/matches?batch=${message}`);
    } catch (error) {
        console.error('Error running batch ML processing:', error);
        const message = encodeURIComponent(`Batch failed: ${error.message}`);
        res.redirect(`/admin/matches?batch=${message}`);
    }
});
router.get('/matches/:id', isAdmin, async (req, res) => {
    try {
        const match = await MLMatch.findById(req.params.id)
            .populate({
                path: 'sourceItemId',
                populate: { path: 'user finder', strictPopulate: false }
            })
            .populate({
                path: 'matchedItemId',
                populate: { path: 'user finder', strictPopulate: false }
            });
        
        if (!match) {
            return res.status(404).send('Match not found');
        }
        
        res.render('admin/match-detail', { 
            match,
            user: req.user 
        });
        
    } catch (error) {
        console.error('Error fetching match detail:', error);
        res.status(500).send('Error loading match');
    }
});

// ⭐ Verify a match
router.post('/matches/:id/verify', isAdmin, async (req, res) => {
    try {
        const match = await MLMatch.findById(req.params.id)
            .populate('sourceItemId')
            .populate('matchedItemId');
        
        if (!match) {
            return res.status(404).json({ error: 'Match not found' });
        }
        
        // Update match status
        match.status = 'verified';
        match.reviewedBy = req.user._id;
        match.reviewedAt = new Date();
        await match.save();
        
        // Determine which is lost and which is found
        const lostItem = match.sourceType === 'LostItem' ? match.sourceItemId : match.matchedItemId;
        const foundItem = match.sourceType === 'FoundItem' ? match.sourceItemId : match.matchedItemId;
        
        // Update item statuses
        lostItem.status = 'matched';
        lostItem.mlMatchStatus = 'verified_match';
        lostItem.matchedWithFoundId = foundItem._id;
        lostItem.matchedAt = new Date();
        lostItem.matchConfidenceScore = match.confidenceScore;
        await lostItem.save();
        
        foundItem.status = 'matched';
        foundItem.mlMatchStatus = 'verified_match';
        foundItem.matchedWithLostId = lostItem._id;
        foundItem.matchedAt = new Date();
        foundItem.matchConfidenceScore = match.confidenceScore;
        await foundItem.save();
        
        // Log admin action
        await AdminAction.create({
            adminId: req.user._id,
            actionType: 'verify_match',
            matchId: match._id,
            lostItemId: lostItem._id,
            foundItemId: foundItem._id
        });
        
        res.json({ 
            success: true, 
            message: 'Match verified successfully. You can now initiate contact between users.' 
        });
        
    } catch (error) {
        console.error('Error verifying match:', error);
        res.status(500).json({ error: 'Failed to verify match' });
    }
});

// ⭐ Reject a match
router.post('/matches/:id/reject', isAdmin, async (req, res) => {
    try {
        const { reason } = req.body;
        
        const match = await MLMatch.findById(req.params.id);
        if (!match) {
            return res.status(404).json({ error: 'Match not found' });
        }
        
        match.status = 'rejected';
        match.reviewedBy = req.user._id;
        match.reviewedAt = new Date();
        match.rejectionReason = reason;
        await match.save();
        
        await AdminAction.create({
            adminId: req.user._id,
            actionType: 'reject_match',
            matchId: match._id,
            notes: reason
        });
        
        res.json({ success: true, message: 'Match rejected' });
        
    } catch (error) {
        console.error('Error rejecting match:', error);
        res.status(500).json({ error: 'Failed to reject match' });
    }
});

// ⭐ Initiate contact between users
router.post('/matches/:id/contact', isAdmin, async (req, res) => {
    try {
        const match = await MLMatch.findById(req.params.id)
            .populate({
                path: 'sourceItemId',
                populate: { path: 'user finder', strictPopulate: false }
            })
            .populate({
                path: 'matchedItemId',
                populate: { path: 'user finder', strictPopulate: false }
            });
        
        if (!match || match.status !== 'verified') {
            return res.status(400).json({ error: 'Match must be verified first' });
        }
        
        const lostItem = match.sourceType === 'LostItem' ? match.sourceItemId : match.matchedItemId;
        const foundItem = match.sourceType === 'FoundItem' ? match.sourceItemId : match.matchedItemId;
        
        await notificationService.initiateUserContact(lostItem, foundItem);
        
        // Update match
        match.contactInitiated = true;
        match.contactInitiatedAt = new Date();
        await match.save();
        
        await AdminAction.create({
            adminId: req.user._id,
            actionType: 'initiate_contact',
            matchId: match._id,
            lostItemId: lostItem._id,
            foundItemId: foundItem._id
        });
        
        res.json({ success: true, message: 'Contact emails sent successfully to both users' });
        
    } catch (error) {
        console.error('Error initiating contact:', error);
        res.status(500).json({ error: 'Failed to initiate contact' });
    }
});

// ⭐ Dashboard API - Get ML matching statistics
router.get('/dashboard/stats', isAdmin, async (req, res) => {
    try {
        const pendingMatches = await MLMatch.countDocuments({ status: 'pending_review' });
        const verifiedMatches = await MLMatch.countDocuments({ status: 'verified' });
        const rejectedMatches = await MLMatch.countDocuments({ status: 'rejected' });
        
        const activeLostItems = await LostItem.countDocuments({ status: 'lost' });
        const pendingFoundItems = await FoundItem.countDocuments({ status: 'found' });
        
        const recentHighConfidence = await MLMatch.find({ 
            status: 'pending_review',
            confidenceScore: { $gte: 0.85 }
        })
        .populate('sourceItemId')
        .populate('matchedItemId')
        .sort({ createdAt: -1 })
        .limit(10);
        
        const totalReviewed = verifiedMatches + rejectedMatches;
        const successRate = totalReviewed > 0 ? ((verifiedMatches / totalReviewed) * 100).toFixed(1) : 0;
        
        res.json({
            pendingMatches,
            verifiedMatches,
            rejectedMatches,
            activeLostItems,
            pendingFoundItems,
            successRate,
            recentHighConfidence
        });
        
    } catch (error) {
        console.error('Error fetching dashboard stats:', error);
        res.status(500).json({ error: 'Failed to fetch statistics' });
    }
});

module.exports = router;

