const axios = require('axios');
const MLMatch = require('../models/mlMatch');
const LostItem = require('../models/lostItem');
const FoundItem = require('../models/foundItem');
const notificationService = require('./notificationService');

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:5000';
const ML_API_KEY = process.env.ML_SERVICE_API_KEY;
const ML_ENABLED = process.env.ML_ENABLED === 'true';

class MLMatchingService {
  
  /**
   * Find matches for a newly reported Found item
   */
  async findMatchesForFoundItem(foundItem, options = {}) {
    if (!ML_ENABLED) {
      console.log('[ML] ML matching is disabled');
      return [];
    }

    try {
      console.log(`[ML] Searching matches for Found item: ${foundItem._id}`);
      
      const payload = this._sanitizeItemData(foundItem);
      
      const response = await axios.post(
        `${ML_SERVICE_URL}/match/found-to-lost`,
        payload,
        {
          headers: { 'X-API-Key': ML_API_KEY },
          timeout: 15000
        }
      );
      
      const matches = this._filterReliableMatches(response.data.matches || []);

      if (matches.length > 0) {
        await this._saveMatches(foundItem._id, 'FoundItem', matches);
        if (options.notify !== false) {
          await notificationService.sendAdminMatchAlert(matches);
        }
      }
      
      return matches;
      
    } catch (error) {
      console.error('[ML] Error finding matches for found item:', error.message);
      // Don't throw - fail gracefully
      return [];
    }
  }
  
  /**
   * Find matches for a newly reported Lost item
   */
  async findMatchesForLostItem(lostItem, options = {}) {
    if (!ML_ENABLED) {
      console.log('[ML] ML matching is disabled');
      return [];
    }

    try {
      console.log(`[ML] Searching matches for Lost item: ${lostItem._id}`);
      
      const payload = this._sanitizeItemData(lostItem);
      
      const response = await axios.post(
        `${ML_SERVICE_URL}/match/lost-to-found`,
        payload,
        {
          headers: { 'X-API-Key': ML_API_KEY },
          timeout: 15000
        }
      );
      
      const matches = this._filterReliableMatches(response.data.matches || []);

      if (matches.length > 0) {
        await this._saveMatches(lostItem._id, 'LostItem', matches);
        if (options.notify !== false) {
          await notificationService.sendAdminMatchAlert(matches);
        }
      }
      
      return matches;
      
    } catch (error) {
      console.error('[ML] Error finding matches for lost item:', error.message);
      return [];
    }
  }
  
  /**
   * Sanitize item data before sending to ML service
   * SECURITY: Remove sensitive user data
   */
  _sanitizeItemData(item) {
    return {
      itemId: item._id.toString(),
      itemName: item.itemName,
      category: item.category,
      description: item.description,
      location: item.lostLocation || item.foundLocation,
      date: item.lostDate || item.foundDate,
      color: item.color || null,
      brand: item.brand || null,
      photoUrl: item.photoUrl || null
    };
  }

  /**
   * Re-run ML matching for every active lost item against all active found items.
   * The Python service performs candidate lookup, scoring, and returns only matches.
   */
  async batchProcessAllMatches() {
    if (!ML_ENABLED) {
      throw new Error('ML matching is disabled. Set ML_ENABLED=true in .env.');
    }

    const lostQuery = {
      status: { $nin: ['reunited', 'resolved', 'closed'] },
      mlMatchStatus: { $ne: 'verified_match' }
    };

    const foundQuery = {
      status: { $nin: ['claimed', 'resolved', 'closed'] },
      mlMatchStatus: { $ne: 'verified_match' }
    };

    const lostItems = await LostItem.find(lostQuery).sort({ createdAt: -1 });
    const activeFoundCount = await FoundItem.countDocuments(foundQuery);

    const summary = {
      lostItemsProcessed: 0,
      activeFoundItems: activeFoundCount,
      matchesSaved: 0,
      errors: 0
    };

    console.log(`[ML] Batch processing started: ${lostItems.length} lost items vs ${activeFoundCount} found items`);

    for (const lostItem of lostItems) {
      try {
        const matches = await this.findMatchesForLostItem(lostItem, { notify: false });
        summary.lostItemsProcessed += 1;
        summary.matchesSaved += matches.length;
      } catch (error) {
        summary.errors += 1;
        console.error(`[ML] Batch error for lost item ${lostItem._id}:`, error.message);
      }
    }

    console.log(
      `[ML] Batch processing finished: ${summary.matchesSaved} matches saved, ` +
      `${summary.errors} errors`
    );

    return summary;
  }

  /**
   * Reject weak category-only matches before saving them.
   * This prevents cases like headset vs umbrella from reaching admin review.
   */
  _filterReliableMatches(matches) {
    return matches.filter(match => {
      const factors = match.factors || {};
      const textEvidence = Math.max(
        factors.descriptionSimilarity || 0,
        factors.itemNameSimilarity || 0,
        factors.tokenOverlap || 0
      );
      const objectTypeMatch = factors.objectTypeMatch ?? 0.5;

      if (objectTypeMatch === 0) {
        console.log(`[ML] Dropped match ${match.matchedItemId}: conflicting object type`);
        return false;
      }

      if (objectTypeMatch < 0.8 && (factors.itemNameSimilarity || 0) < 0.20) {
        console.log(`[ML] Dropped match ${match.matchedItemId}: different item names/types`);
        return false;
      }

      if ((factors.itemNameSimilarity || 0) < 0.12 && (factors.tokenOverlap || 0) < 0.12) {
        console.log(`[ML] Dropped match ${match.matchedItemId}: no direct item evidence`);
        return false;
      }

      if (textEvidence < 0.12 && objectTypeMatch < 0.8) {
        console.log(`[ML] Dropped match ${match.matchedItemId}: weak text evidence`);
        return false;
      }

      return true;
    });
  }
  
  /**
   * Save ML matches to database
   */
  async _saveMatches(sourceItemId, sourceType, matches) {
    const operations = matches.map(match => {
      const document = {
        sourceItemId,
        sourceType,
        matchedItemId: match.matchedItemId,
        matchedType: sourceType === 'LostItem' ? 'FoundItem' : 'LostItem',
        confidenceScore: match.confidenceScore,
        matchingFactors: {
          categoryMatch: match.factors.categoryMatch,
          descriptionSimilarity: match.factors.descriptionSimilarity,
          locationProximity: match.factors.locationProximity,
          dateProximity: match.factors.dateProximity,
          itemNameSimilarity: match.factors.itemNameSimilarity || 0,
          attributeMatch: match.factors.attributeMatch || 0,
          objectTypeMatch: match.factors.objectTypeMatch ?? 0.5,
          colorMatch: match.factors.colorMatch ?? 0.5,
          brandMatch: match.factors.brandMatch ?? 0.5,
          modelTokenMatch: match.factors.modelTokenMatch ?? 0.5,
          tokenOverlap: match.factors.tokenOverlap || 0
        },
        status: 'pending_review'
      };

      return {
        updateOne: {
          filter: { sourceItemId, matchedItemId: match.matchedItemId },
          update: { $set: document },
          upsert: true
        }
      };
    });
    
    if (operations.length === 0) {
      return;
    }

    await MLMatch.bulkWrite(operations, { ordered: false });
    console.log(`[ML] Saved or updated ${operations.length} matches in database`);
  }
}

module.exports = new MLMatchingService();
