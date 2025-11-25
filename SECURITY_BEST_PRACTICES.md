# Security Best Practices - Blood Sugar Monitoring System

## Critical Security Rules

### 🚨 NEVER DO THIS
1. ❌ **Don't commit `.env` file** - Contains real passwords
2. ❌ **Don't share terminal screenshots** - May show credentials
3. ❌ **Don't print passwords in code** - Leaves traces in logs
4. ❌ **Don't hardcode credentials** - Use environment variables
5. ❌ **Don't share SMTP passwords** - Even with team members
6. ❌ **Don't use personal email password** - Use App Passwords
7. ❌ **Don't commit database backups** - May contain user data
8. ❌ **Don't expose API keys** - Keep them in `.env`

### ✅ ALWAYS DO THIS
1. ✅ **Use `.env` for secrets** - Load with `python-dotenv`
2. ✅ **Add `.env` to `.gitignore`** - Already done
3. ✅ **Use App Passwords** - For Gmail SMTP
4. ✅ **Mask credentials in output** - Test scripts do this
5. ✅ **Use HTTPS in production** - For API endpoints
6. ✅ **Hash passwords** - System uses werkzeug hashing
7. ✅ **Validate user input** - Prevent SQL injection
8. ✅ **Check authentication** - Token-based auth implemented

## Environment Variables (.env)

### What Should Be in .env
```env
# Database credentials
DB_PASSWORD=your-database-password

# Email credentials
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Secret keys
JWT_SECRET_KEY=your-random-secret-key
```

### What Should NOT Be in Code
```python
# ❌ BAD - Hardcoded credentials
password = "mypassword123"
smtp_user = "myemail@gmail.com"

# ✅ GOOD - Use environment variables
import os
password = os.getenv("DB_PASSWORD")
smtp_user = os.getenv("SMTP_USERNAME")
```

## Password Security

### Database Passwords
- **Current:** Uses werkzeug `generate_password_hash()`
- **Method:** PBKDF2 with SHA-256
- **Storage:** Never store plain text passwords
- **Verification:** Use `check_password_hash()`

### SMTP Passwords
- **Gmail:** Requires App Password (not regular password)
- **Setup:** Google Account > Security > 2-Step > App Passwords
- **Storage:** Only in `.env` file (not in code)
- **Display:** Test scripts mask passwords automatically

## Git Security

### Files in .gitignore
```
.env
*.pyc
__pycache__/
*.log
.vscode/
node_modules/
```

### Before Committing
```bash
# Check what you're committing
git status
git diff

# Ensure .env is not staged
git status | grep .env

# If .env appears, remove it immediately
git rm --cached .env
```

### If You Accidentally Commit Secrets
```bash
# Remove from history (use with caution)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (only if necessary)
git push origin --force --all
```

## API Security

### Authentication
- **Method:** Token-based (JWT)
- **Storage:** localStorage with `_admin` suffix for admins
- **Expiration:** 30-minute inactivity timeout
- **Validation:** Every protected endpoint checks token

### CORS Configuration
```python
# app.py - CORS settings
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://127.0.0.1:5500", "http://localhost:5500"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### Protected Endpoints
```python
# Require authentication
@app.route('/api/readings', methods=['POST'])
def add_reading():
    user_info = get_user_from_token()
    if not user_info:
        return jsonify({"error": "Unauthorized"}), 401
    # ... rest of code
```

## Database Security

### SQL Injection Prevention
```python
# ❌ BAD - Vulnerable to SQL injection
sql = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ GOOD - Use parameterized queries
sql = "SELECT * FROM users WHERE email = %s"
cursor.execute(sql, (email,))
```

### Connection Security
```python
# Use environment variables
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)
```

### User Permissions
- **Root access:** Only for development
- **Production:** Create limited user with specific permissions
```sql
CREATE USER 'bloodsugar_app'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON blood_sugar_db.* TO 'bloodsugar_app'@'localhost';
FLUSH PRIVILEGES;
```

## File Upload Security

### Profile Images
- **Validation:** Check file type and size
- **Storage:** Convert to base64 data URLs
- **Size limit:** Prevent large files
- **Sanitization:** Remove malicious code

```python
# Validate image uploads
allowed_types = ['image/jpeg', 'image/png', 'image/gif']
max_size = 5 * 1024 * 1024  # 5MB

if file_type not in allowed_types:
    return error("Invalid file type")
    
if file_size > max_size:
    return error("File too large")
```

## Production Deployment

### Pre-Deployment Checklist
- [ ] All secrets in environment variables
- [ ] `.env` file NOT committed
- [ ] Flask debug mode OFF (`FLASK_DEBUG=False`)
- [ ] Use production WSGI server (not Flask dev server)
- [ ] HTTPS enabled
- [ ] Database user with limited permissions
- [ ] Regular security updates
- [ ] Logging configured (no sensitive data)
- [ ] Rate limiting enabled
- [ ] CORS restricted to production domains

### Production .env Example
```env
# Production settings
FLASK_DEBUG=False
FLASK_ENV=production

# Use production database user (not root)
DB_USER=bloodsugar_app
DB_PASSWORD=strong-random-password

# Production-grade secret key
JWT_SECRET_KEY=long-random-string-at-least-32-chars

# HTTPS in production
API_BASE_URL=https://yourdomain.com
```

## Monitoring & Logging

### What to Log
- ✅ Authentication attempts
- ✅ Failed login attempts
- ✅ API endpoint access
- ✅ Database errors
- ✅ Email sending status

### What NOT to Log
- ❌ Passwords (even hashed)
- ❌ Session tokens
- ❌ SMTP credentials
- ❌ JWT tokens
- ❌ Full email addresses (mask them)
- ❌ Health care numbers
- ❌ Credit card data

### Logging Example
```python
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Good logging
logger.info(f"User {user_id} logged in")
logger.warning(f"Failed login attempt for email: {email[:3]}***")

# Bad logging
logger.info(f"Password: {password}")  # ❌ NEVER DO THIS
logger.info(f"Token: {token}")  # ❌ NEVER DO THIS
```

## Common Vulnerabilities

### 1. SQL Injection
**Risk:** Attacker can manipulate database queries
**Prevention:** Use parameterized queries (already implemented)

### 2. Cross-Site Scripting (XSS)
**Risk:** Malicious scripts in user input
**Prevention:** Sanitize and escape user input

### 3. Cross-Site Request Forgery (CSRF)
**Risk:** Unauthorized actions on behalf of user
**Prevention:** CSRF tokens (implement in production)

### 4. Insecure Direct Object References
**Risk:** Access to unauthorized data
**Prevention:** Check user owns resource before returning it

### 5. Sensitive Data Exposure
**Risk:** Credentials in logs, git, or error messages
**Prevention:** Mask credentials, use .env, proper error handling

### 6. Broken Authentication
**Risk:** Weak passwords, no expiration
**Prevention:** Token expiration, password requirements implemented

## Emergency Response

### If Credentials Are Leaked
1. **Immediately change all passwords**
2. **Revoke App Passwords** (Google Account)
3. **Check access logs** for unauthorized access
4. **Notify affected users** if their data was accessed
5. **Review commit history** and remove secrets
6. **Force push cleaned history** (if necessary)

### If Database Is Compromised
1. **Take database offline**
2. **Change all database passwords**
3. **Review database logs**
4. **Check for data exfiltration**
5. **Notify users** per data protection regulations
6. **Restore from clean backup**

## Security Checklist

### Development
- [ ] `.env` file created and configured
- [ ] `.env` in `.gitignore`
- [ ] No hardcoded credentials
- [ ] Passwords hashed (werkzeug)
- [ ] Parameterized SQL queries
- [ ] Token-based authentication working
- [ ] Test scripts mask credentials

### Testing
- [ ] Run email test without exposing credentials
- [ ] Test authentication and authorization
- [ ] Verify SQL injection prevention
- [ ] Check error messages don't leak info
- [ ] Test rate limiting (if implemented)

### Pre-Production
- [ ] All secrets in environment variables
- [ ] Debug mode OFF
- [ ] Production database user configured
- [ ] HTTPS enabled
- [ ] CORS restricted
- [ ] Logging configured properly
- [ ] Security headers added
- [ ] Regular backup schedule

### Ongoing
- [ ] Monitor logs regularly
- [ ] Update dependencies monthly
- [ ] Review access logs
- [ ] Rotate passwords quarterly
- [ ] Security audit annually
- [ ] User training on security

## Tools & Resources

### Security Testing
- **OWASP ZAP:** Web application security scanner
- **SQLMap:** SQL injection testing
- **Bandit:** Python security linter
- **Safety:** Check for known vulnerabilities in dependencies

### Password Management
- **1Password, LastPass, Bitwarden:** Store credentials securely
- **pwgen:** Generate strong random passwords
- **Google App Passwords:** For SMTP authentication

### Documentation
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security: https://flask.palletsprojects.com/en/2.3.x/security/
- Python Security: https://python.readthedocs.io/en/stable/library/security_warnings.html

## Contact

If you discover a security vulnerability:
1. **Do NOT open a public GitHub issue**
2. Contact repository owner directly
3. Include detailed description
4. Allow time for fix before disclosure

---

**Remember: Security is everyone's responsibility!**

Last Updated: November 24, 2025
