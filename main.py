import os
from openai import OpenAI
import vrchatapi
from vrchatapi.api import authentication_api
from vrchatapi.exceptions import UnauthorizedException
from vrchatapi.models.two_factor_auth_code import TwoFactorAuthCode
from vrchatapi.models.two_factor_email_code import TwoFactorEmailCode
import configparser
from vrchatapi.rest import ApiException
from pprint import pprint
import time

# Configurations
creds = configparser.ConfigParser()
creds.read('logins.ini')

vrc_creds = vrchatapi.Configuration(
    username=creds['VRCHAT']['username'],
    password=creds['VRCHAT']['password'],
)

# Initialize OpenAI
openai = OpenAI(
    api_key=creds['OPENAI']['api_key'],  # this is also the default, it can be omitted
    organization=creds['OPENAI']['organization']
)

# Generate a new bio using ChatGPT
bio_prompt = 'Generate some complete and utter nonsense.'
update_minutes = 1


def generate_bio(prompt, model="gpt-4"):
    completion = openai.completions.create(
        model=model,
        prompt=prompt,
        temperature=0.7,
        max_tokens=50
    )
    print(completion.choices[0].text)
    print(dict(completion).get('usage'))
    print(completion.model_dump_json(indent=2))


print(generate_bio("give me text"))

quit()
def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.completions.create(
        model=model,
        prompt=prompt,
        temperature=0.7,
        max_tokens=50
    )
    print("Choices:", response.choices)
    return response.choices[0].message["content"]


# response = "static response for testing"
response = get_completion(bio_prompt)  # Uncomment to enable OpenAI prompts
print("response:", response)
quit()

# Step 2. VRChat consists of several API's (WorldsApi, UsersApi, FilesApi, NotificationsApi, FriendsApi, etc...)
# Here we enter a context of the API Client and instantiate the Authentication API which is required for logging in.

# Enter a context with an instance of the API client
with vrchatapi.ApiClient(vrc_creds) as api_client:
    # Instantiate instances of API classes
    auth_api = authentication_api.AuthenticationApi(api_client)

    try:
        # Step 3. Calling getCurrentUser on Authentication API logs you in if the user isn't already logged in.
        current_user = auth_api.get_current_user()
    except UnauthorizedException as e:
        if e.status == 200:
            if "Email 2 Factor Authentication" in e.reason:
                # Step 3.5. Calling email verify2fa if the account has 2FA disabled
                auth_api.verify2_fa_email_code(two_factor_email_code=TwoFactorEmailCode(input("Email 2FA Code: ")))
            elif "2 Factor Authentication" in e.reason:
                # Step 3.5. Calling verify2fa if the account has 2FA enabled
                auth_api.verify2_fa(two_factor_auth_code=TwoFactorAuthCode(input("2FA Code: ")))
            current_user = auth_api.get_current_user()
        else:
            print("Exception when calling API: %s\n", e)
    except vrchatapi.ApiException as e:
        print("Exception when calling API: %s\n", e)

    # Print basic details
    print("Logged in as:", current_user.display_name)
    print("Current user cookie:", auth_api.api_client.cookie)
    print("Cookie:", auth_api.verify_auth_token())
    print("Current user ID:", current_user.id)
    print("Current user Bio:", current_user.bio)

    user_id = current_user.id


    def update_bio(bio):
        # Generate a request
        usersapi = vrchatapi.UsersApi(api_client)
        update_user_request = vrchatapi.UpdateUserRequest(bio=bio)  # UpdateUserRequest |  (optional)

        # Send the request
        try:
            # Update User Info
            api_response = usersapi.update_user(user_id, update_user_request=update_user_request)
            pprint(api_response)
        except ApiException as e:
            print("Exception when calling UsersApi->update_user: %s\n" % e)

    # Enter a loop to repeatedly update bio at regular intervals
    while True:
        new_bio = get_completion(bio_prompt)
        update_bio(str(new_bio))
        time.sleep(update_minutes * 60)


