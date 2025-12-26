# Okta User Management CLI - Modern Edition

A comprehensive, production-ready CLI tool for managing Okta users, groups, applications, and MFA using the latest Okta Python SDK (v3.0+) with OAuth 2.0 support.

## Features

### User Management
- ✅ List all users with advanced filtering and pagination
- ✅ Advanced user search with filter expressions
- ✅ Get detailed user information
- ✅ Create users with custom attributes
- ✅ Update user profiles
- ✅ Activate/deactivate users
- ✅ Suspend/unsuspend users
- ✅ Delete users

### Group Management
- ✅ List all groups
- ✅ Create new groups
- ✅ Add/remove users from groups
- ✅ List group members

### MFA Management
- ✅ List enrolled factors for users
- ✅ Reset user MFA factors

### Application Management
- ✅ List all applications
- ✅ List users assigned to applications

### System Logs & Monitoring
- ✅ Query system logs with filters
- ✅ Audit trail for compliance

## Latest Okta Capabilities (2025)

This tool leverages the latest Okta features:

- **OAuth 2.0 Authentication** (recommended over API tokens)
- **Advanced Search** with filter expressions
- **Pagination** for large datasets
- **Rate Limit Handling** with proper error messages
- **Field Selection** to reduce response sizes
- **Async Operations** for better performance
- **Modern Python SDK** (v3.0+ with OAS 3.0 support)

## Prerequisites

- Python 3.9 or higher
- An Okta organization
- Either:
  - OAuth 2.0 credentials (recommended), OR
  - API Token (legacy)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/dareogunewu/okta.git
cd okta
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install okta>=3.0.0 python-dotenv>=1.0.0
```

## Configuration

### Option 1: OAuth 2.0 (Recommended)

OAuth 2.0 provides better security with scoped permissions and token-based authentication.

#### Step 1: Create an OAuth 2.0 Application in Okta

1. Log in to your Okta Admin Console
2. Navigate to **Applications** > **Applications**
3. Click **Create App Integration**
4. Select **API Services** as the application type
5. Give it a name (e.g., "Okta Management CLI")
6. Click **Save**
7. Note your **Client ID**

#### Step 2: Generate Private/Public Key Pair

```bash
# Generate private key
openssl genrsa -out private_key.pem 2048

# Generate public key
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

#### Step 3: Add Public Key to Okta

1. In your OAuth app settings, go to **General** tab
2. Scroll to **Client Credentials** section
3. Click **Edit** next to **Public Keys**
4. Click **Add Key**
5. Paste the contents of `public_key.pem`
6. Click **Save**

#### Step 4: Grant Scopes

1. In the **Okta API Scopes** tab of your app
2. Grant the following scopes:
   - `okta.users.manage`
   - `okta.groups.manage`
   - `okta.apps.manage`
   - `okta.logs.read`
   - `okta.roles.manage`

#### Step 5: Configure Environment Variables

Create a `.env` file in the project directory:

```bash
OKTA_DOMAIN=your-domain.okta.com
OKTA_CLIENT_ID=your_client_id_here
OKTA_PRIVATE_KEY_PATH=/path/to/private_key.pem
```

### Option 2: API Token (Legacy)

#### Step 1: Create an API Token

1. Log in to your Okta Admin Console
2. Navigate to **Security** > **API**
3. Click **Tokens** tab
4. Click **Create Token**
5. Give it a name and click **Create Token**
6. Copy the token (you won't be able to see it again!)

#### Step 2: Configure Environment Variables

Create a `.env` file in the project directory:

```bash
OKTA_DOMAIN=your-domain.okta.com
OKTA_API_TOKEN=your_api_token_here
```

## Usage

### Run the Interactive CLI

```bash
python okta_manager.py
```

Or make it executable:

```bash
chmod +x okta_manager.py
./okta_manager.py
```

### Interactive Menu

The CLI provides an interactive menu with the following options:

```
👥 User Management:
  1.  List All Users
  2.  Search Users (Advanced)
  3.  Get User Details
  4.  Create User
  5.  Update User
  6.  Activate User
  7.  Deactivate User
  8.  Suspend User
  9.  Unsuspend User
  10. Delete User

👨‍👩‍👧‍👦 Group Management:
  11. List Groups
  12. Create Group
  13. Add User to Group
  14. Remove User from Group
  15. List Group Members

🔐 MFA Management:
  16. List User Factors
  17. Reset User Factors

📱 Application Management:
  18. List Applications
  19. List Application Users

📊 System Logs:
  20. View System Logs
```

### Advanced Search Examples

When using option 2 (Search Users), you can use advanced filter expressions:

```
# Find users by first name
profile.firstName eq "John"

# Find active users in a department
profile.department eq "Engineering" and status eq "ACTIVE"

# Find users by email domain
profile.email sw "john"

# Complex multi-condition search
profile.firstName eq "Jane" and profile.department eq "Sales" and status eq "ACTIVE"
```

### System Log Query Examples

When viewing system logs (option 20), you can filter by event type:

```
# User login events
eventType eq "user.session.start"

# Successful SSO attempts
eventType eq "user.authentication.sso" and outcome.result eq "SUCCESS"

# Failed authentication attempts
eventType eq "user.authentication.auth_via_mfa" and outcome.result eq "FAILURE"
```

## Security Best Practices

1. **Never commit credentials**: Keep `.env` file out of version control (already in `.gitignore`)
2. **Use OAuth 2.0**: Prefer OAuth 2.0 over API tokens for better security
3. **Least Privilege**: Only grant necessary OAuth scopes
4. **Rotate Credentials**: Regularly rotate API tokens and OAuth keys
5. **Secure Storage**: Store private keys securely (use secrets management in production)
6. **Monitor Logs**: Regularly review system logs for suspicious activity
7. **Rate Limits**: The tool handles rate limits automatically, but avoid excessive API calls

## Rate Limits

Okta enforces rate limits to protect their API:

- **Default**: 60 requests/minute per client
- **Concurrent**: Max 5 concurrent requests per client
- **429 Response**: Tool automatically detects and reports rate limit errors

The CLI automatically handles rate limits and provides clear error messages when limits are exceeded.

## Error Handling

The tool provides comprehensive error handling:

- **401 Unauthorized**: Check your credentials
- **403 Forbidden**: Insufficient permissions (check OAuth scopes or API token permissions)
- **429 Rate Limit**: Too many requests (wait and retry)
- **404 Not Found**: User/Group/App not found
- **500 Server Error**: Okta service issue

## Troubleshooting

### "Authentication failed" Error

- Verify your `OKTA_DOMAIN` is correct (e.g., `your-domain.okta.com`)
- For OAuth 2.0: Ensure private key path is correct and public key is registered in Okta
- For API Token: Verify token is valid and not expired

### "Permission denied" Error

- For OAuth 2.0: Check that required scopes are granted to your application
- For API Token: Ensure the token has admin privileges

### "Module not found" Error

```bash
pip install -r requirements.txt
```

### Rate Limit Errors

- Wait 60 seconds before retrying
- Consider reducing the frequency of API calls
- Use pagination limits to reduce request volume

## Migration from Old Script

If you're upgrading from the old `okta user manager.py`:

1. **Install new dependencies**: `pip install -r requirements.txt`
2. **Set up OAuth 2.0** (recommended) or use existing API token
3. **Update environment variables**: Use `.env` file instead of hardcoded values
4. **New features available**:
   - Advanced search
   - Suspend/unsuspend users
   - MFA management
   - Application management
   - System logs
   - Better error handling
   - Pagination support

## API Reference

For more information about Okta APIs:

- [Okta Developer Documentation](https://developer.okta.com/docs/reference/)
- [Users API](https://developer.okta.com/docs/api/openapi/okta-management/management/tag/User/)
- [Groups API](https://developer.okta.com/docs/reference/api/groups/)
- [System Log API](https://developer.okta.com/docs/api/openapi/okta-management/management/tag/SystemLog/)
- [Python SDK Documentation](https://github.com/okta/okta-sdk-python)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues or questions:

1. Check the [Okta Developer Documentation](https://developer.okta.com/docs/)
2. Review [Okta Community](https://support.okta.com/help/s/?language=en_US)
3. Open an issue in this repository

## Changelog

### Version 2.0.0 (2025)

- ✨ Complete rewrite using Okta SDK v3.0+
- ✨ Added OAuth 2.0 support (recommended authentication method)
- ✨ Advanced user search with filter expressions
- ✨ Pagination support for large datasets
- ✨ Suspend/unsuspend user functionality
- ✨ MFA factor management
- ✨ Application management
- ✨ System logs querying
- ✨ Comprehensive error handling
- ✨ Rate limit detection and reporting
- ✨ Async operations for better performance
- ✨ Modern Python 3.9+ support
- ✨ Environment variable configuration with `.env` support
- 🔒 Enhanced security with OAuth 2.0 scopes
- 📚 Complete documentation

### Version 1.0.0 (2023)

- Initial release with basic user and group management
