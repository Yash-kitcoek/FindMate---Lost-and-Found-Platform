const nodemailer = require('nodemailer');

// Configure email transporter
const transporter = nodemailer.createTransport({
  service: process.env.EMAIL_SERVICE || 'gmail',
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASSWORD
  }
});

class NotificationService {
  
  /**
   * Notify admin of new ML matches
   */
  async sendAdminMatchAlert(matches) {
    try {
      const adminEmail = process.env.ADMIN_EMAIL;
      
      if (!adminEmail) {
        console.warn('[Notification] No admin email configured');
        return;
      }
      
      const highConfidenceMatches = matches.filter(m => m.confidenceScore >= 0.85);
      
      if (highConfidenceMatches.length === 0) return;
      
      const mailOptions = {
        from: process.env.EMAIL_USER,
        to: adminEmail,
        subject: `🔍 FindMate: ${highConfidenceMatches.length} New High-Confidence Match(es)`,
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">New ML Matches Detected</h2>
            <p>${highConfidenceMatches.length} high-confidence match(es) found.</p>
            <p>Please review them in the admin dashboard:</p>
            <a href="${process.env.APP_URL || 'http://localhost:3000'}/admin/matches" 
               style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">
              View Matches
            </a>
            <br/><br/>
            <h3>Top Matches:</h3>
            <ul>
              ${highConfidenceMatches.slice(0, 3).map(m => `
                <li style="margin: 10px 0;">
                  <strong>Confidence: ${(m.confidenceScore * 100).toFixed(1)}%</strong><br/>
                  Match ID: ${m.matchedItemId}
                </li>
              `).join('')}
            </ul>
          </div>
        `
      };
      
      await transporter.sendMail(mailOptions);
      console.log('[Notification] Admin match alert sent');
      
    } catch (error) {
      console.error('[Notification] Failed to send admin alert:', error.message);
    }
  }
  
  /**
   * Initiate contact between Lost and Found item reporters
   * Called after admin verifies match
   */
  async initiateUserContact(lostItem, foundItem) {
    try {
      // Populate user data if not already populated
      if (!lostItem.user.email) {
        await lostItem.populate('user');
      }
      if (!foundItem.finder.email) {
        await foundItem.populate('finder');
      }

      // Email to Lost item reporter
      await transporter.sendMail({
        from: process.env.EMAIL_USER,
        to: lostItem.user.email,
        subject: '✅ FindMate: Potential Match Found for Your Lost Item',
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #059669;">Great News!</h2>
            <p>We found a potential match for your lost <strong>${lostItem.itemName}</strong>.</p>
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
            <h3>Finder's Contact:</h3>
            <ul style="list-style: none; padding: 0;">
              <li><strong>Name:</strong> ${foundItem.finder.fullName}</li>
              <li><strong>Email:</strong> ${foundItem.finder.email}</li>
              <li><strong>Phone:</strong> ${foundItem.contactPhone || foundItem.finder.phone || 'Not provided'}</li>
            </ul>
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
            <h3>Item Details:</h3>
            <ul style="list-style: none; padding: 0;">
              <li><strong>Found Location:</strong> ${foundItem.foundLocation}</li>
              <li><strong>Found Date:</strong> ${new Date(foundItem.foundDate).toLocaleDateString()}</li>
              <li><strong>Current Location:</strong> ${foundItem.currentLocation}</li>
            </ul>
            <p>Please reach out to verify and reclaim your item.</p>
            <a href="${process.env.APP_URL || 'http://localhost:3000'}/profile" 
               style="background-color: #059669; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">
              View Your Items
            </a>
          </div>
        `
      });
      
      // Email to Found item reporter
      await transporter.sendMail({
        from: process.env.EMAIL_USER,
        to: foundItem.finder.email,
        subject: '✅ FindMate: Match Confirmed for Found Item',
        html: `
          <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #059669;">Match Confirmed!</h2>
            <p>The <strong>${foundItem.itemName}</strong> you found has been matched with its owner.</p>
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
            <h3>Owner's Contact:</h3>
            <ul style="list-style: none; padding: 0;">
              <li><strong>Name:</strong> ${lostItem.user.fullName}</li>
              <li><strong>Email:</strong> ${lostItem.user.email}</li>
              <li><strong>Phone:</strong> ${lostItem.user.phone || 'Not provided'}</li>
            </ul>
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
            <p>They will be reaching out to you soon. Thank you for helping reunite lost items!</p>
            <a href="${process.env.APP_URL || 'http://localhost:3000'}/profile" 
               style="background-color: #059669; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">
              View Your Items
            </a>
          </div>
        `
      });
      
      console.log('[Notification] Contact initiated between users');
      
    } catch (error) {
      console.error('[Notification] Failed to send user contact emails:', error.message);
      throw error;
    }
  }
}

module.exports = new NotificationService();
