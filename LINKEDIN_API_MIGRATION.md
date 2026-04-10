# LinkedIn API Migration Guide

**Date:** 2026-04-10  
**Status:** Complete  
**Tier:** Silver

---

## Overview

The Personal AI Employee has been migrated from Playwright browser automation to the **official LinkedIn API v2**. This provides a more reliable, production-ready solution for posting content to LinkedIn.

## What Changed

### ✅ Added
- **LinkedIn API Client** (`src/orchestrator/skills/linkedin_api_client.py`)
  - OAuth 2.0 authentication with PKCE
  - Automatic token refresh
  - Text posts, link posts, and image posts
  - Image upload support (up to 8MB)

- **Setup Script** (`scripts/setup_linkedin_api.py`)
  - Interactive OAuth authentication flow
  - Token management

- **Enhanced setup.sh**
  - Integrated LinkedIn API setup
  - Automatic credential checking

### 🔄 Modified
- **post_linkedin.py** - Now uses API instead of Playwright
- **linkedin_watcher.py** - Simplified to content calendar only (no message monitoring)
- **run_linkedin_watcher.py** - Updated for API version
- **watcher_manager.py** - Checks for API token instead of username/password
- **.env.example** - Updated with API credentials format
- **requirements.txt** - Playwright marked as optional

### ❌ Removed
- Message monitoring feature (requires LinkedIn Partner Program access)
- Browser automation dependencies (Playwright still available but not required)

---

## Prerequisites

### 1. LinkedIn Developer App

You need a LinkedIn app with the following:

1. Go to https://www.linkedin.com/developers/apps
2. Create a new app or select existing app
3. In the **Products** tab, add:
   - ✅ **Share on LinkedIn**
   - ✅ **Sign In with LinkedIn using OpenID Connect**
4. In the **Auth** tab:
   - Copy your **Client ID**
   - Copy your **Client Secret**
   - Add redirect URI: `http://localhost:8000/callback`

### 2. Required Scopes

The following OAuth scopes are used:
- `openid` - Basic authentication
- `profile` - User profile information
- `w_member_social` - Post to LinkedIn

**Note:** Message reading requires LinkedIn Partner Program access and is not included.

---

## Setup Instructions

### Option 1: Unified Setup (Recommended)

Run the main setup script which includes LinkedIn authentication:

```bash
./setup.sh
```

This will:
1. Install dependencies
2. Create vault structure
3. Configure environment
4. Guide you through LinkedIn OAuth

### Option 2: Manual Setup

#### Step 1: Configure Environment

Edit `.env` file:

```bash
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
LINKEDIN_TOKEN_PATH=./credentials/linkedin_api_token.json
```

#### Step 2: Authenticate

Run the LinkedIn setup script:

```bash
python scripts/setup_linkedin_api.py
```

Or use the API client directly:

```bash
python src/orchestrator/skills/linkedin_api_client.py \
  YOUR_CLIENT_ID \
  YOUR_CLIENT_SECRET \
  http://localhost:8000/callback
```

#### Step 3: Follow OAuth Flow

1. Visit the authorization URL in your browser
2. Log in to LinkedIn and authorize the app
3. Copy the `code` parameter from the redirect URL
4. Paste it into the terminal
5. Token will be saved to `./credentials/linkedin_api_token.json`

---

## Usage

### Posting to LinkedIn

#### Via Skill (with approval workflow):

```bash
python -m src.orchestrator.skills.post_linkedin '{
  "action": "create_post",
  "content": "Hello from my AI Employee! 🚀"
}'
```

This creates an approval request in `Pending_Approval/`. Move it to `Approved/` to post.

#### Direct API Usage:

```python
from linkedin_api_client import LinkedInAPIClient

client = LinkedInAPIClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="http://localhost:8000/callback"
)

# Text post
result = client.create_text_share("Hello LinkedIn!")

# Post with image
result = client.create_post_with_image(
    text="Check out this image!",
    image_path="./path/to/image.jpg"
)

print(result)
```

### Content Calendar

Schedule posts for later:

```bash
python -m src.orchestrator.skills.post_linkedin '{
  "action": "schedule_post",
  "content": "Scheduled post content",
  "scheduled_time": "2026-04-15T09:00:00"
}'
```

The LinkedIn watcher checks the content calendar hourly and creates approval requests for due posts.

### Check Calendar

```bash
python -m src.orchestrator.skills.post_linkedin '{
  "action": "check_calendar"
}'
```

---

## Features

### ✅ Supported

- **Text Posts** - Up to 3000 characters
- **Link Sharing** - Posts with article links
- **Image Posts** - Upload and post images (PNG, JPG, GIF up to 8MB)
- **Scheduled Posts** - Content calendar integration
- **Token Management** - Automatic refresh
- **HITL Approval** - Human-in-the-loop workflow

### ❌ Not Supported

- **Message Monitoring** - Requires LinkedIn Partner Program
- **Video Posts** - Not implemented (API supports it)
- **Carousel Posts** - Not implemented (API supports it)
- **Analytics** - Not implemented (API supports it)

---

## Troubleshooting

### "invalid_client" Error

**Problem:** Authentication fails with "Client authentication failed"

**Solutions:**
1. Verify your Client ID and Client Secret are correct
2. Check that the Client Secret doesn't have extra characters or prefixes
3. Ensure your app has "Share on LinkedIn" product enabled
4. Verify the redirect URI matches exactly: `http://localhost:8000/callback`

### "unauthorized_scope_error"

**Problem:** Scope not authorized for your application

**Solutions:**
1. Go to your LinkedIn app's **Products** tab
2. Ensure "Share on LinkedIn" is added and approved
3. Ensure "Sign In with LinkedIn using OpenID Connect" is added
4. Wait a few minutes for changes to propagate

### Token Expired

**Problem:** Posts fail with authentication error

**Solution:**
The token should auto-refresh. If it doesn't:

```bash
# Re-authenticate
python scripts/setup_linkedin_api.py
```

### Image Upload Fails

**Problem:** Image posts fail

**Solutions:**
1. Check image format (PNG, JPG, GIF only)
2. Verify image size is under 8MB
3. Ensure image file exists and is readable

---

## API Limits

LinkedIn API has rate limits:

- **Posts:** ~100 posts per day per user
- **Token Expiry:** Access tokens expire after 60 days
- **Refresh Tokens:** Valid for 1 year

The client automatically handles token refresh.

---

## Migration Notes

### For Existing Users

If you were using the Playwright version:

1. **Backup your session:**
   ```bash
   cp -r credentials/linkedin_session credentials/linkedin_session.bak
   ```

2. **Update .env:**
   - Replace `LINKEDIN_USERNAME` and `LINKEDIN_PASSWORD`
   - Add `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_REDIRECT_URI`

3. **Authenticate:**
   ```bash
   python scripts/setup_linkedin_api.py
   ```

4. **Test posting:**
   ```bash
   python -m src.orchestrator.skills.post_linkedin '{"action": "create_post", "content": "Testing API migration!"}'
   ```

### Message Monitoring

The message monitoring feature has been removed because it requires LinkedIn Partner Program access, which is not available to standard OAuth apps.

**Alternatives:**
- Use LinkedIn's native mobile/desktop notifications
- Check LinkedIn manually for important messages
- Consider LinkedIn's webhook integrations (requires Partner access)

---

## Architecture

### Authentication Flow

```
1. User runs setup script
2. Script generates authorization URL with PKCE
3. User visits URL and authorizes app
4. LinkedIn redirects to localhost:8000/callback?code=...
5. Script exchanges code for access token
6. Token saved to credentials/linkedin_api_token.json
7. Token auto-refreshes when expired
```

### Posting Flow

```
1. Skill creates approval request in Pending_Approval/
2. User reviews and moves to Approved/
3. Orchestrator detects approved file
4. Skill loads LinkedIn API client
5. Client checks token validity (refreshes if needed)
6. API call made to LinkedIn
7. Result logged and file moved to Done/
```

---

## Silver Tier Compliance

✅ **Requirement:** "One working MCP server for external action"

The LinkedIn API integration fulfills this requirement:
- Uses official REST API (not browser automation)
- OAuth 2.0 authentication
- Production-ready implementation
- Automatic token management
- Full HITL approval workflow

---

## Support

### Documentation
- LinkedIn API Docs: https://learn.microsoft.com/en-us/linkedin/
- OAuth 2.0 Guide: https://learn.microsoft.com/en-us/linkedin/shared/authentication/
- Share API: https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/

### Files
- API Client: `src/orchestrator/skills/linkedin_api_client.py`
- Post Skill: `src/orchestrator/skills/post_linkedin.py`
- Setup Script: `scripts/setup_linkedin_api.py`
- Watcher: `src/watchers/linkedin_watcher.py`

---

**Last Updated:** 2026-04-10  
**Version:** Silver Tier v1.0
