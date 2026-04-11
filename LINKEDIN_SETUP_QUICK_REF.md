# LinkedIn API Setup - Quick Reference

## Current Status
- ✅ LinkedIn API client implemented
- ✅ OAuth 2.0 authentication flow ready
- ✅ Image posting support added
- ✅ Setup scripts created
- ⚠️ **Authentication pending** - Need to verify client secret

## Issue Encountered

During testing, we encountered an `invalid_client` error when exchanging the authorization code for an access token. This typically means:

1. **Client Secret is incorrect** - The format `[SECRET_VALUE_REDACTED]` looks unusual
2. **Client ID is incorrect** - Less likely, but possible
3. **App not properly configured** - Products not enabled

## How to Verify Your Credentials

### Step 1: Check LinkedIn Developer Portal

1. Go to https://www.linkedin.com/developers/apps
2. Select your app
3. Go to **Auth** tab
4. Under **Application credentials**:
   - **Client ID**: Should be alphanumeric
   - **Client Secret**: Should be a random string WITHOUT any prefix

### Step 2: Verify Products

In the **Products** tab, ensure these are added and **verified**:
- ✅ Share on LinkedIn
- ✅ Sign In with LinkedIn using OpenID Connect

### Step 3: Check Redirect URIs

In the **Auth** tab, under **OAuth 2.0 settings**:
- Authorized redirect URLs must include: `your_callback_url`

## Correct Setup Flow

Once you have the correct credentials:

### 1. Update .env file

```bash
LINKEDIN_CLIENT_ID=your_actual_client_id
LINKEDIN_CLIENT_SECRET=your_actual_client_secret_without_prefix
LINKEDIN_REDIRECT_URI='your callback url'
```

### 2. Run authentication

```bash
python scripts/setup_linkedin_api.py
```

### 3. Follow the prompts

1. Visit the authorization URL
2. Log in to LinkedIn
3. Authorize the app
4. Copy the `code` from the redirect URL
5. Paste it into the terminal

### 4. Test posting

```bash
python -m src.orchestrator.skills.post_linkedin '{
  "action": "create_post",
  "content": "Hello from my AI Employee! 🚀 #automation #ai"
}'
```

This will create an approval request in `Pending_Approval/`. Move it to `Approved/` to post.

## Common Issues

### "unauthorized_scope_error"

**Problem:** Scope not authorized

**Solution:**
- Ensure "Share on LinkedIn" product is added in your app
- Wait a few minutes for changes to propagate
- Try re-authenticating

### "invalid_redirect_uri"

**Problem:** Redirect URI doesn't match

**Solution:**
- Verify `your_callback_url` is in your app's authorized redirect URLs
- Check for typos (http vs https, trailing slashes, etc.)

### Token Expired

**Problem:** Posts fail after some time

**Solution:**
- The client automatically refreshes tokens
- If it fails, re-run: `python scripts/setup_linkedin_api.py`

## Testing Without Authentication

You can test the approval workflow without posting:

```bash
# Set dry run mode
export DRY_RUN=true

# Create a test post
python -m src.orchestrator.skills.post_linkedin '{
  "action": "create_post",
  "content": "Test post"
}'
```

This will create the approval request but won't actually post to LinkedIn.

## Next Steps

1. **Verify your LinkedIn Client Secret** - This is the most likely issue
2. **Update .env with correct credentials**
3. **Run authentication**: `python scripts/setup_linkedin_api.py`
4. **Test posting**: Create a simple test post
5. **Verify on LinkedIn**: Check that the post appears

## Support

If you continue to have issues:

1. Double-check all credentials in LinkedIn Developer Portal
2. Ensure your app has the correct products enabled
3. Try creating a new app if the current one has issues
4. Check LinkedIn API status: https://www.linkedin-apistatus.com/

---

**Created:** 2026-04-10  
**Status:** Awaiting credential verification
