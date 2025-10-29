# Puzfeed


## Incoming Mail Handling

We'll use **CloudMailin** for receiving .puz file attachments via email:

- Each puzzle feed will have a unique email address (e.g., `puzzle-{feed-id}@puzzles.cloudmailin.net`)
- Users/publishers can submit puzzles by emailing .puz files to the feed's address
- CloudMailin will POST the email content and attachments to our webhook endpoint
- We'll extract the .puz file, parse metadata, and add it to the appropriate feed
- Free tier supports 200 emails/month, upgradeable as needed

**Setup Tasks:**
1. Create CloudMailin account and configure webhook endpoint
2. Add POST `/webhooks/cloudmailin` endpoint to receive emails
3. Parse .puz file attachments from email payload
4. Associate email address with feed ID for routing
