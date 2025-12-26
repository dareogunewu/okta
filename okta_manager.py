#!/usr/bin/env python3
"""
Okta User Management CLI - Modern Edition
A comprehensive CLI tool for managing Okta users, groups, apps, and MFA using the latest Okta SDK.
"""

import asyncio
import os
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

try:
    from okta.client import Client as OktaClient
    from okta.errors import OktaAPIError
except ImportError:
    print("Error: okta SDK not installed. Run: pip install okta")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using environment variables only.")


class OktaManager:
    """Enhanced Okta management with modern SDK and best practices."""

    def __init__(self):
        """Initialize Okta client with OAuth 2.0 or API token."""
        self.okta_domain = os.getenv('OKTA_DOMAIN')
        self.api_token = os.getenv('OKTA_API_TOKEN')
        self.client_id = os.getenv('OKTA_CLIENT_ID')
        self.private_key_path = os.getenv('OKTA_PRIVATE_KEY_PATH')

        if not self.okta_domain:
            raise ValueError("OKTA_DOMAIN environment variable is required")

        # Ensure domain has https://
        if not self.okta_domain.startswith('https://'):
            self.okta_domain = f'https://{self.okta_domain}'

        # Configure client based on available credentials
        if self.client_id and self.private_key_path:
            # OAuth 2.0 (recommended)
            self.config = {
                'orgUrl': self.okta_domain,
                'authorizationMode': 'PrivateKey',
                'clientId': self.client_id,
                'scopes': [
                    'okta.users.manage',
                    'okta.groups.manage',
                    'okta.apps.manage',
                    'okta.logs.read',
                    'okta.roles.manage'
                ],
                'privateKey': self.private_key_path
            }
            print("✓ Using OAuth 2.0 authentication (recommended)")
        elif self.api_token:
            # API Token (legacy)
            self.config = {
                'orgUrl': self.okta_domain,
                'token': self.api_token
            }
            print("⚠ Using API Token authentication (consider migrating to OAuth 2.0)")
        else:
            raise ValueError("Either OKTA_API_TOKEN or (OKTA_CLIENT_ID + OKTA_PRIVATE_KEY_PATH) required")

        self.client = OktaClient(self.config)

    async def handle_api_error(self, error: OktaAPIError, operation: str):
        """Handle API errors with detailed messages and retry logic."""
        if error.status == 429:
            retry_after = error.headers.get('X-Rate-Limit-Reset', 60)
            print(f"⚠ Rate limit exceeded. Retry after {retry_after} seconds.")
            return False
        elif error.status == 401:
            print(f"✗ Authentication failed. Check your credentials.")
            return False
        elif error.status == 403:
            print(f"✗ Permission denied for {operation}. Check OAuth scopes or API token permissions.")
            return False
        else:
            print(f"✗ API Error ({error.status}): {error}")
            return False

    async def list_users(self, query: Optional[str] = None, limit: int = 200,
                        status: Optional[str] = None, fields: Optional[str] = None):
        """
        List users with advanced filtering and pagination.

        Args:
            query: Search query (firstName, lastName, email)
            limit: Max results per page (default 200)
            status: Filter by status (ACTIVE, STAGED, DEPROVISIONED, etc.)
            fields: Specific fields to return (e.g., "id,profile.firstName,profile.email")
        """
        try:
            params = {}
            if query:
                params['q'] = query
            if status:
                params['filter'] = f'status eq "{status}"'
            if fields:
                params['fields'] = fields
            if limit:
                params['limit'] = limit

            users = []
            user_list, resp, err = await self.client.list_users(params)

            if err:
                print(f"✗ Error listing users: {err}")
                return []

            # Collect first page
            users.extend(user_list)

            # Handle pagination
            while resp.has_next():
                user_list, err = await resp.next()
                if err:
                    print(f"⚠ Error fetching next page: {err}")
                    break
                users.extend(user_list)

            print(f"\n{'='*80}")
            print(f"Found {len(users)} user(s)")
            print(f"{'='*80}\n")

            for user in users:
                profile = user.profile
                status_emoji = "✓" if user.status == "ACTIVE" else "○"
                print(f"{status_emoji} {profile.first_name} {profile.last_name}")
                print(f"   Email: {profile.email}")
                print(f"   Login: {profile.login}")
                print(f"   ID: {user.id}")
                print(f"   Status: {user.status}")
                if hasattr(profile, 'department') and profile.department:
                    print(f"   Department: {profile.department}")
                print()

            return users

        except OktaAPIError as e:
            await self.handle_api_error(e, "list users")
            return []

    async def search_users(self, search_expr: str):
        """
        Advanced user search with filter expressions.

        Examples:
            profile.firstName eq "John"
            profile.department eq "Engineering" and status eq "ACTIVE"
            profile.email sw "john"
        """
        try:
            params = {'search': search_expr}
            users, resp, err = await self.client.list_users(params)

            if err:
                print(f"✗ Error searching users: {err}")
                return []

            print(f"\nSearch: {search_expr}")
            print(f"Found {len(users)} result(s)\n")

            for user in users:
                print(f"✓ {user.profile.first_name} {user.profile.last_name} ({user.profile.email}) - {user.status}")

            return users

        except OktaAPIError as e:
            await self.handle_api_error(e, "search users")
            return []

    async def create_user(self, first_name: str, last_name: str, email: str,
                         department: Optional[str] = None, activate: bool = True,
                         send_email: bool = False, custom_attrs: Optional[Dict] = None):
        """
        Create a new user with enhanced profile options.

        Args:
            activate: Activate user immediately
            send_email: Send activation email
            custom_attrs: Dictionary of custom profile attributes
        """
        try:
            profile_data = {
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'login': email
            }

            if department:
                profile_data['department'] = department

            # Add custom attributes
            if custom_attrs:
                profile_data.update(custom_attrs)

            user_data = {
                'profile': profile_data
            }

            params = {
                'activate': activate,
                'sendEmail': send_email
            }

            user, resp, err = await self.client.create_user(user_data, params)

            if err:
                print(f"✗ Error creating user: {err}")
                return None

            print(f"\n✓ User created successfully!")
            print(f"   Name: {user.profile.first_name} {user.profile.last_name}")
            print(f"   Email: {user.profile.email}")
            print(f"   ID: {user.id}")
            print(f"   Status: {user.status}")

            return user

        except OktaAPIError as e:
            await self.handle_api_error(e, "create user")
            return None

    async def update_user(self, user_id: str, profile_updates: Dict[str, Any]):
        """
        Update user profile with any attributes.

        Args:
            user_id: User ID to update
            profile_updates: Dictionary of profile fields to update
        """
        try:
            user_data = {
                'profile': profile_updates
            }

            user, resp, err = await self.client.update_user(user_id, user_data)

            if err:
                print(f"✗ Error updating user: {err}")
                return None

            print(f"✓ User updated successfully!")
            print(f"   ID: {user.id}")
            print(f"   Updated fields: {', '.join(profile_updates.keys())}")

            return user

        except OktaAPIError as e:
            await self.handle_api_error(e, "update user")
            return None

    async def get_user(self, user_id: str):
        """Get detailed user information."""
        try:
            user, resp, err = await self.client.get_user(user_id)

            if err:
                print(f"✗ Error fetching user: {err}")
                return None

            print(f"\n{'='*80}")
            print(f"User Details: {user.profile.first_name} {user.profile.last_name}")
            print(f"{'='*80}\n")
            print(f"ID: {user.id}")
            print(f"Email: {user.profile.email}")
            print(f"Login: {user.profile.login}")
            print(f"Status: {user.status}")
            print(f"Created: {user.created}")
            print(f"Last Updated: {user.last_updated}")

            if hasattr(user, 'last_login') and user.last_login:
                print(f"Last Login: {user.last_login}")

            return user

        except OktaAPIError as e:
            await self.handle_api_error(e, "get user")
            return None

    async def activate_user(self, user_id: str, send_email: bool = True):
        """Activate a user account."""
        try:
            params = {'sendEmail': send_email}
            user, resp, err = await self.client.activate_user(user_id, params)

            if err:
                print(f"✗ Error activating user: {err}")
                return None

            print(f"✓ User activated successfully! (Email sent: {send_email})")
            return user

        except OktaAPIError as e:
            await self.handle_api_error(e, "activate user")
            return None

    async def deactivate_user(self, user_id: str, send_email: bool = False):
        """Deactivate a user account."""
        try:
            user, resp, err = await self.client.deactivate_user(user_id, {'sendEmail': send_email})

            if err:
                print(f"✗ Error deactivating user: {err}")
                return None

            print(f"✓ User deactivated successfully!")
            return user

        except OktaAPIError as e:
            await self.handle_api_error(e, "deactivate user")
            return None

    async def suspend_user(self, user_id: str):
        """Suspend a user account (temporary)."""
        try:
            user, resp, err = await self.client.suspend_user(user_id)

            if err:
                print(f"✗ Error suspending user: {err}")
                return None

            print(f"✓ User suspended successfully!")
            return user

        except OktaAPIError as e:
            await self.handle_api_error(e, "suspend user")
            return None

    async def unsuspend_user(self, user_id: str):
        """Unsuspend a user account."""
        try:
            user, resp, err = await self.client.unsuspend_user(user_id)

            if err:
                print(f"✗ Error unsuspending user: {err}")
                return None

            print(f"✓ User unsuspended successfully!")
            return user

        except OktaAPIError as e:
            await self.handle_api_error(e, "unsuspend user")
            return None

    async def delete_user(self, user_id: str, send_email: bool = False):
        """Delete a user (must be deactivated first)."""
        try:
            resp, err = await self.client.deactivate_or_delete_user(user_id, {'sendEmail': send_email})

            if err:
                print(f"✗ Error deleting user: {err}")
                return False

            print(f"✓ User deleted successfully!")
            return True

        except OktaAPIError as e:
            await self.handle_api_error(e, "delete user")
            return False

    # Group Management

    async def list_groups(self, query: Optional[str] = None):
        """List all groups."""
        try:
            params = {}
            if query:
                params['q'] = query

            groups, resp, err = await self.client.list_groups(params)

            if err:
                print(f"✗ Error listing groups: {err}")
                return []

            print(f"\nFound {len(groups)} group(s)\n")

            for group in groups:
                print(f"✓ {group.profile.name}")
                print(f"   ID: {group.id}")
                if hasattr(group.profile, 'description') and group.profile.description:
                    print(f"   Description: {group.profile.description}")
                print()

            return groups

        except OktaAPIError as e:
            await self.handle_api_error(e, "list groups")
            return []

    async def create_group(self, name: str, description: Optional[str] = None):
        """Create a new group."""
        try:
            group_data = {
                'profile': {
                    'name': name,
                    'description': description or ''
                }
            }

            group, resp, err = await self.client.create_group(group_data)

            if err:
                print(f"✗ Error creating group: {err}")
                return None

            print(f"✓ Group created: {group.profile.name} (ID: {group.id})")
            return group

        except OktaAPIError as e:
            await self.handle_api_error(e, "create group")
            return None

    async def add_user_to_group(self, user_id: str, group_id: str):
        """Add a user to a group."""
        try:
            resp, err = await self.client.add_user_to_group(group_id, user_id)

            if err:
                print(f"✗ Error adding user to group: {err}")
                return False

            print(f"✓ User added to group successfully!")
            return True

        except OktaAPIError as e:
            await self.handle_api_error(e, "add user to group")
            return False

    async def remove_user_from_group(self, user_id: str, group_id: str):
        """Remove a user from a group."""
        try:
            resp, err = await self.client.remove_user_from_group(group_id, user_id)

            if err:
                print(f"✗ Error removing user from group: {err}")
                return False

            print(f"✓ User removed from group successfully!")
            return True

        except OktaAPIError as e:
            await self.handle_api_error(e, "remove user from group")
            return False

    async def list_group_members(self, group_id: str):
        """List all members of a group."""
        try:
            users, resp, err = await self.client.list_group_users(group_id)

            if err:
                print(f"✗ Error listing group members: {err}")
                return []

            print(f"\nGroup Members ({len(users)}):\n")

            for user in users:
                print(f"✓ {user.profile.first_name} {user.profile.last_name} ({user.profile.email})")

            return users

        except OktaAPIError as e:
            await self.handle_api_error(e, "list group members")
            return []

    # MFA / Factors Management

    async def list_user_factors(self, user_id: str):
        """List all enrolled factors for a user."""
        try:
            factors, resp, err = await self.client.list_factors(user_id)

            if err:
                print(f"✗ Error listing factors: {err}")
                return []

            print(f"\nEnrolled Factors ({len(factors)}):\n")

            for factor in factors:
                status_emoji = "✓" if factor.status == "ACTIVE" else "○"
                print(f"{status_emoji} {factor.factor_type} ({factor.provider})")
                print(f"   Factor ID: {factor.id}")
                print(f"   Status: {factor.status}")
                print()

            return factors

        except OktaAPIError as e:
            await self.handle_api_error(e, "list user factors")
            return []

    async def reset_user_factors(self, user_id: str):
        """Reset all user factors (useful for MFA reset)."""
        try:
            resp, err = await self.client.reset_factors(user_id)

            if err:
                print(f"✗ Error resetting factors: {err}")
                return False

            print(f"✓ All user factors reset successfully!")
            return True

        except OktaAPIError as e:
            await self.handle_api_error(e, "reset user factors")
            return False

    # Application Management

    async def list_applications(self):
        """List all applications."""
        try:
            apps, resp, err = await self.client.list_applications()

            if err:
                print(f"✗ Error listing applications: {err}")
                return []

            print(f"\nApplications ({len(apps)}):\n")

            for app in apps:
                print(f"✓ {app.label}")
                print(f"   ID: {app.id}")
                print(f"   Status: {app.status}")
                print()

            return apps

        except OktaAPIError as e:
            await self.handle_api_error(e, "list applications")
            return []

    async def list_app_users(self, app_id: str):
        """List users assigned to an application."""
        try:
            app_users, resp, err = await self.client.list_application_users(app_id)

            if err:
                print(f"✗ Error listing app users: {err}")
                return []

            print(f"\nAssigned Users ({len(app_users)}):\n")

            for app_user in app_users:
                print(f"✓ {app_user.id}")
                print(f"   Scope: {app_user.scope}")
                print()

            return app_users

        except OktaAPIError as e:
            await self.handle_api_error(e, "list app users")
            return []

    # System Logs

    async def get_system_logs(self, filter_expr: Optional[str] = None,
                             since: Optional[str] = None, limit: int = 100):
        """
        Query system logs for audit and monitoring.

        Args:
            filter_expr: Filter expression (e.g., 'eventType eq "user.session.start"')
            since: ISO 8601 timestamp to query from
            limit: Max results to return
        """
        try:
            params = {'limit': limit}
            if filter_expr:
                params['filter'] = filter_expr
            if since:
                params['since'] = since

            logs, resp, err = await self.client.get_logs(params)

            if err:
                print(f"✗ Error fetching logs: {err}")
                return []

            print(f"\nSystem Logs ({len(logs)} events):\n")

            for log in logs:
                timestamp = log.published
                event_type = log.event_type
                actor = log.actor.get('alternateId', 'Unknown') if log.actor else 'Unknown'
                outcome = log.outcome.get('result', 'UNKNOWN') if log.outcome else 'UNKNOWN'

                outcome_emoji = "✓" if outcome == "SUCCESS" else "✗"
                print(f"{outcome_emoji} [{timestamp}] {event_type}")
                print(f"   Actor: {actor}")
                print(f"   Outcome: {outcome}")
                print()

            return logs

        except OktaAPIError as e:
            await self.handle_api_error(e, "get system logs")
            return []


async def interactive_menu():
    """Interactive CLI menu."""
    print("\n" + "="*80)
    print("Okta User Management CLI - Modern Edition")
    print("="*80 + "\n")

    try:
        manager = OktaManager()
    except Exception as e:
        print(f"✗ Failed to initialize Okta client: {e}")
        return

    while True:
        print("\n" + "-"*80)
        print("MAIN MENU")
        print("-"*80)
        print("\n👥 User Management:")
        print("  1.  List All Users")
        print("  2.  Search Users (Advanced)")
        print("  3.  Get User Details")
        print("  4.  Create User")
        print("  5.  Update User")
        print("  6.  Activate User")
        print("  7.  Deactivate User")
        print("  8.  Suspend User")
        print("  9.  Unsuspend User")
        print("  10. Delete User")

        print("\n👨‍👩‍👧‍👦 Group Management:")
        print("  11. List Groups")
        print("  12. Create Group")
        print("  13. Add User to Group")
        print("  14. Remove User from Group")
        print("  15. List Group Members")

        print("\n🔐 MFA Management:")
        print("  16. List User Factors")
        print("  17. Reset User Factors")

        print("\n📱 Application Management:")
        print("  18. List Applications")
        print("  19. List Application Users")

        print("\n📊 System Logs:")
        print("  20. View System Logs")

        print("\n❌ Exit:")
        print("  0. Exit")

        choice = input("\n👉 Enter choice: ").strip()

        try:
            if choice == "0":
                print("\nGoodbye! 👋\n")
                break

            elif choice == "1":
                query = input("Search query (press Enter for all): ").strip() or None
                status = input("Filter by status (ACTIVE/STAGED/DEPROVISIONED, or Enter for all): ").strip() or None
                await manager.list_users(query=query, status=status)

            elif choice == "2":
                print("\nExamples:")
                print('  profile.firstName eq "John"')
                print('  profile.department eq "Engineering" and status eq "ACTIVE"')
                search = input("Search expression: ").strip()
                if search:
                    await manager.search_users(search)

            elif choice == "3":
                user_id = input("User ID or email: ").strip()
                await manager.get_user(user_id)

            elif choice == "4":
                first_name = input("First Name: ").strip()
                last_name = input("Last Name: ").strip()
                email = input("Email: ").strip()
                department = input("Department (optional): ").strip() or None
                activate = input("Activate immediately? (y/n): ").strip().lower() == 'y'
                send_email = input("Send activation email? (y/n): ").strip().lower() == 'y'
                await manager.create_user(first_name, last_name, email, department, activate, send_email)

            elif choice == "5":
                user_id = input("User ID: ").strip()
                print("\nEnter fields to update (leave blank to skip):")
                updates = {}
                if first_name := input("First Name: ").strip():
                    updates['firstName'] = first_name
                if last_name := input("Last Name: ").strip():
                    updates['lastName'] = last_name
                if email := input("Email: ").strip():
                    updates['email'] = email
                if department := input("Department: ").strip():
                    updates['department'] = department

                if updates:
                    await manager.update_user(user_id, updates)
                else:
                    print("No updates provided.")

            elif choice == "6":
                user_id = input("User ID: ").strip()
                send_email = input("Send activation email? (y/n): ").strip().lower() == 'y'
                await manager.activate_user(user_id, send_email)

            elif choice == "7":
                user_id = input("User ID: ").strip()
                await manager.deactivate_user(user_id)

            elif choice == "8":
                user_id = input("User ID: ").strip()
                await manager.suspend_user(user_id)

            elif choice == "9":
                user_id = input("User ID: ").strip()
                await manager.unsuspend_user(user_id)

            elif choice == "10":
                user_id = input("User ID: ").strip()
                confirm = input("⚠️  Are you sure? This cannot be undone! (yes/no): ").strip().lower()
                if confirm == "yes":
                    await manager.delete_user(user_id)
                else:
                    print("Cancelled.")

            elif choice == "11":
                query = input("Search query (press Enter for all): ").strip() or None
                await manager.list_groups(query)

            elif choice == "12":
                name = input("Group Name: ").strip()
                description = input("Description (optional): ").strip() or None
                await manager.create_group(name, description)

            elif choice == "13":
                user_id = input("User ID: ").strip()
                group_id = input("Group ID: ").strip()
                await manager.add_user_to_group(user_id, group_id)

            elif choice == "14":
                user_id = input("User ID: ").strip()
                group_id = input("Group ID: ").strip()
                await manager.remove_user_from_group(user_id, group_id)

            elif choice == "15":
                group_id = input("Group ID: ").strip()
                await manager.list_group_members(group_id)

            elif choice == "16":
                user_id = input("User ID: ").strip()
                await manager.list_user_factors(user_id)

            elif choice == "17":
                user_id = input("User ID: ").strip()
                confirm = input("⚠️  Reset all MFA factors for this user? (yes/no): ").strip().lower()
                if confirm == "yes":
                    await manager.reset_user_factors(user_id)
                else:
                    print("Cancelled.")

            elif choice == "18":
                await manager.list_applications()

            elif choice == "19":
                app_id = input("Application ID: ").strip()
                await manager.list_app_users(app_id)

            elif choice == "20":
                print("\nExample filters:")
                print('  eventType eq "user.session.start"')
                print('  eventType eq "user.authentication.sso" and outcome.result eq "SUCCESS"')
                filter_expr = input("Filter expression (optional): ").strip() or None
                limit = input("Limit (default 100): ").strip()
                limit = int(limit) if limit else 100
                await manager.get_system_logs(filter_expr=filter_expr, limit=limit)

            else:
                print("Invalid choice. Please try again.")

        except KeyboardInterrupt:
            print("\n\nOperation cancelled.\n")
            continue
        except Exception as e:
            print(f"\n✗ Error: {e}\n")
            continue


def main():
    """Main entry point."""
    try:
        asyncio.run(interactive_menu())
    except KeyboardInterrupt:
        print("\n\nExiting...\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
