from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from google.oauth2 import id_token
from google.auth.transport import requests

def about(request):
    # return HttpResponse('about')
    return render(request, "about.html")

@csrf_exempt
def home(request):
    # return HttpResponse('home')
    if request.POST:
        token = request.POST.get("idtoken", "")
        try:
            # Specify the CLIENT_ID of the app that accesses the backend:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(),
                                                  "133754882345-b044u4p8radcpasmq9s38sc3k0hiktsb.apps.googleusercontent.com")

            # Or, if multiple clients access the backend server:
            # idinfo = id_token.verify_oauth2_token(token, requests.Request())
            # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
            #     raise ValueError('Could not verify audience.')

            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # If auth request is from a G Suite domain:
            # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
            #     raise ValueError('Wrong hosted domain.')

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            userid = idinfo['sub']
            name = idinfo['name']
            email = idinfo['email']

            # print("YAY", userid)
        except ValueError:
            # Invalid token
            pass
    return render(request, "home.html")