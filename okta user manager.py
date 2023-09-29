import os
import requests

# Okta settings
OKTA_DOMAIN = os.environ.get('OKTA_DOMAIN', 'ENTER YOUR OKTA DOMAIN')
API_TOKEN = os.environ.get('API_TOKEN', 'ENTER YOUR API TOKEN')

if not OKTA_DOMAIN or not API_TOKEN:
    raise ValueError("Please set your environment variables for OKTA_DOMAIN and API_TOKEN.")

API_ENDPOINT = f"https://{OKTA_DOMAIN}/api/v1/users"

def get_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"SSWS {API_TOKEN}"
    }

def make_request(method, url, data=None):
    try:
        if method == 'get':
            response = requests.get(url, headers=get_headers())
        elif method == 'post':
            response = requests.post(url, headers=get_headers(), json=data)
        elif method == 'put':
            response = requests.put(url, headers=get_headers(), json=data)
        elif method == 'delete':
            response = requests.delete(url, headers=get_headers())
        
        response.raise_for_status()
        return response.json()

    except requests.HTTPError as e:
        print(f"Request failed with error: {e}")
        return None
    
def create_user(first_name, last_name, email, department, activate=True, send_email=False):
    user_profile = {
        'profile': {
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'login': email,
            'department': department
        }
    }
    url = f"{API_ENDPOINT}?activate={str(activate).lower()}"
    if send_email:
        url += "&sendEmail=true"
    response = requests.post(url, headers=get_headers(), json=user_profile)
    return response.json()

def list_users():
    response = requests.get(API_ENDPOINT, headers=get_headers())
    return response.json()

def update_user(user_id, update_data):
    url = f"{API_ENDPOINT}/{user_id}"
    response = requests.put(url, headers=get_headers(), json=update_data)
    return response.json()

def activate_user(user_id):
    url = f"{API_ENDPOINT}/{user_id}/lifecycle/activate"
    response = requests.post(url, headers=get_headers())
    return response.json()

def deactivate_user(user_id):
    url = f"{API_ENDPOINT}/{user_id}/lifecycle/deactivate"
    response = requests.post(url, headers=get_headers())
    return response.json()

def assign_user_to_group(user_id, group_id):
    url = f"{API_ENDPOINT}/{user_id}/groups/{group_id}"
    response = requests.put(url, headers=get_headers())
    return response.status_code

def remove_user_from_group(user_id, group_id):
    url = f"{API_ENDPOINT}/{user_id}/groups/{group_id}"
    response = requests.delete(url, headers=get_headers())
    return response.status_code

if __name__ == "__main__":
    while True:
        print("\nChoose an action:")
        print("1. List Users")
        print("2. Create User")
        print("3. Update User")
        print("4. Activate User")
        print("5. Deactivate User")
        print("6. Assign User to Group")
        print("7. Remove User from Group")
        print("8. Exit")
        
        choice = input("Enter choice: ")

        if choice == "1":
            users = list_users()
            for user in users:
                print(user['profile']['login'], user['id'])
        elif choice == "2":
            email = input("Enter email: ")
            first_name = input("Enter first name: ")
            last_name = input("Enter last name: ")
            department = input("Enter department: ")
            response = create_user(first_name, last_name, email, department)
            print("User created:", response['id'])
        elif choice == "3":
            user_id = input("Enter User ID to update: ")
            new_email = input("Enter new email: ")
            response = update_user(user_id, {'profile': {'email': new_email}})
            print("User updated:", response['id'])
        elif choice == "4":
            user_id = input("Enter User ID to activate: ")
            response = activate_user(user_id)
            print("User activated:", response['id'])
        elif choice == "5":
            user_id = input("Enter User ID to deactivate: ")
            response = deactivate_user(user_id)
            print("User deactivated:", response['id'])
        elif choice == "6":
            user_id = input("Enter User ID: ")
            group_id = input("Enter Group ID to assign the user to: ")
            status = assign_user_to_group(user_id, group_id)
            if status == 200:
                print(f"User {user_id} assigned to group {group_id}.")
            else:
                print(f"Failed to assign user {user_id} to group {group_id}.")
        elif choice == "7":
            user_id = input("Enter User ID: ")
            group_id = input("Enter Group ID to remove the user from: ")
            status = remove_user_from_group(user_id, group_id)
            if status == 204:
                print(f"User {user_id} removed from group {group_id}.")
            else:
                print(f"Failed to remove user {user_id} from group {group_id}.")
        elif choice == "8":
            break
        else:
            print("Invalid choice.")