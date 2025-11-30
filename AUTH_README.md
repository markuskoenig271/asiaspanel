# Authentication Setup

## Password File

The app uses a simple password file for authentication:

- **`backend/.pw`** - Contains the master password (gitignored, never committed)
- **`backend/.pw.template`** - Template showing format (committed to git)

## Current Password

```
gorps271
```

## How It Works

1. **Backend** reads password from `backend/.pw` file on startup
2. **Users** enter password on login screen
3. **Backend** returns session token (valid until server restart)
4. **Frontend** includes token in all API requests

## Setup

### Local Development

```bash
# Create .pw file in backend directory (already done)
cd backend
echo gorps271 > .pw

# Start backend
python app.py
```

### Production Deployment

```bash
# Ensure backend/.pw file exists
cd backend

# Deploy backend (includes .pw file automatically)
.\deploy.ps1

# Deploy frontend
cd ..
git add .
git commit -m "Add authentication"
git push
```

## Security Features

✅ Password stored in file (not in git)  
✅ Token-based authentication (not password in every request)  
✅ Tokens stored in-memory (cleared on server restart)  
✅ HTTPS enforced in production  
✅ SessionStorage (not localStorage) - cleared when browser closes

## Sharing Access

Send your colleagues:
1. The app URL: `https://proud-mud-09bc94003.3.azurestaticapps.net`
2. The password: `gorps271`

They'll see a login screen and can access after entering the password.

## Changing the Password

1. Edit `.pw` file with new password
2. Redeploy backend: `cd backend && .\deploy.ps1`
3. Users will need to re-login with new password
