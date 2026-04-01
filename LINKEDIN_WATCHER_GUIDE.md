# LinkedIn Watcher Testing Guide

## Overview

The LinkedIn watcher monitors LinkedIn messages for keywords indicating business opportunities. Due to LinkedIn's strong anti-automation measures, initial setup requires manual intervention.

---

## Known Challenges

LinkedIn has robust security measures that make browser automation difficult:

1. **CAPTCHA Challenges** - Frequently triggered on automated logins
2. **Email/Phone Verification** - May require verification code
3. **Suspicious Activity Detection** - Browser automation is often detected
4. **Session Expiration** - Sessions expire frequently requiring re-login

---

## Current Implementation

The LinkedIn watcher uses Playwright for browser automation with these features:

- **Non-headless mode** - Browser window visible for manual intervention
- **Session persistence** - Saves browser session to avoid repeated logins
- **Extended timeouts** - 2-minute wait for manual verification
- **Keyword monitoring** - Detects messages with: urgent, opportunity, partnership, meeting, invoice, payment

---

## Testing Steps

### 1. Prerequisites

```bash
# Ensure Playwright is installed
pip install playwright
playwright install chromium

# Verify credentials in .env
cat .env | grep LINKEDIN
```

### 2. Run LinkedIn Watcher

```bash
# Run with visible browser
python -m src.watchers.run_linkedin_watcher ./ai_employee_vault
```

### 3. Manual Login Process

When the browser opens:

1. **Wait for login page** to load
2. **Complete any CAPTCHA** if shown
3. **Enter verification code** if requested (check email/phone)
4. **Wait for redirect** to LinkedIn feed or messaging
5. **Keep browser open** - watcher will continue monitoring

### 4. Expected Behavior

Once logged in successfully:

- Watcher navigates to LinkedIn messaging
- Checks for unread conversations every 5 minutes
- Creates action files in `Needs_Action/` for messages with keywords
- Logs activity to `Logs/linkedinwatcher_YYYY-MM-DD.log`

---

## Action File Format

When a message with keywords is detected:

```markdown
---
type: linkedin_message
sender: John Doe
detected_at: 2026-04-01T15:30:00
timestamp: 2h ago
priority: high
keywords_matched: opportunity, meeting
status: pending
requires_approval: true
---

# LinkedIn Message from John Doe

## Message Preview
> Hi, I have an exciting opportunity to discuss...

## Detected Keywords
- **opportunity**
- **meeting**

## Suggested Actions
- [ ] Review full conversation on LinkedIn
- [ ] Draft a response if needed
- [ ] Check sender's profile for context
- [ ] Mark as priority if business opportunity
- [ ] Create task in project management if needed
```

---

## Troubleshooting

### Issue: Login Timeout

**Symptom**: `LinkedIn login failed: Timeout exceeded`

**Solution**:
- Increase timeout in `linkedin_watcher.py` (currently 120 seconds)
- Complete CAPTCHA/verification faster
- Try running during off-peak hours

### Issue: Security Challenge

**Symptom**: `LinkedIn security challenge detected`

**Solution**:
- Complete the challenge manually in the browser
- Wait for the 2-minute timeout to allow completion
- Session will be saved for future runs

### Issue: Session Expired

**Symptom**: Watcher keeps asking for login

**Solution**:
```bash
# Clear old session
rm -rf credentials/linkedin_session

# Run watcher again
python -m src.watchers.run_linkedin_watcher ./ai_employee_vault
```

### Issue: Browser Not Opening

**Symptom**: No browser window appears

**Solution**:
```bash
# Check if running in WSL without display
echo $DISPLAY

# If empty, set display
export DISPLAY=:0

# Or run in headless mode (won't help with CAPTCHA)
# Edit linkedin_watcher.py: headless=True
```

---

## Alternative: LinkedIn API

For production use, consider using LinkedIn's official API instead of browser automation:

### Advantages
- No CAPTCHA challenges
- More reliable
- Better rate limits
- Official support

### Setup
1. Create LinkedIn App at https://www.linkedin.com/developers/apps
2. Get OAuth credentials
3. Implement OAuth flow
4. Use LinkedIn Messaging API

### Implementation Notes
- Requires LinkedIn API access (may need approval)
- OAuth flow more complex but more reliable
- Better for long-term production use

---

## Current Status

**Implementation**: ✅ Complete  
**Testing**: 🔄 In Progress  
**Production Ready**: ⚠️ Requires manual login intervention

**Recommendation**: 
- For Silver Tier demo: Current implementation works with manual setup
- For Gold Tier production: Migrate to LinkedIn API with OAuth

---

## Configuration

Edit `.env` file:

```bash
# LinkedIn credentials
LINKEDIN_USERNAME=your_email@example.com
LINKEDIN_PASSWORD=your_password

# Session storage
LINKEDIN_SESSION_PATH=./credentials/linkedin_session

# Check interval (seconds)
LINKEDIN_CHECK_INTERVAL=300

# Keywords to monitor (comma-separated)
LINKEDIN_KEYWORDS=urgent,opportunity,partnership,meeting,invoice,payment
```

---

## Logs

Monitor watcher activity:

```bash
# View real-time logs
tail -f ai_employee_vault/Logs/linkedinwatcher_2026-04-01.log

# Check for errors
grep ERROR ai_employee_vault/Logs/linkedinwatcher_*.log
```

---

## Next Steps

1. **Manual Testing**: Run watcher and complete login manually
2. **Message Testing**: Send test message with keywords to yourself
3. **Action File Verification**: Check `Needs_Action/` for created files
4. **Multi-Watcher**: Test running Gmail + LinkedIn watchers simultaneously
5. **Production Planning**: Consider LinkedIn API migration for Gold Tier

---

**Last Updated**: 2026-04-01
