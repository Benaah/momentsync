from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from moments.models import User
from moments.models import Moment



from google.oauth2 import id_token
from google.auth.transport import requests
# import hashlib


def about(request):
    # return HttpResponse('about')
    return render(request, "about.html")


# def register_username(request):
#
@csrf_exempt
def registration(request):
    print(request)
    if request.POST:
        username = request.POST.get("username", "")
        token = request.POST.get("googleToken","")

        if not User.objects.filter(username=username).exists():
            idinfo = id_token.verify_oauth2_token(token, requests.Request(),
                                                  "133754882345-b044u4p8radcpasmq9s38sc3k0hiktsb.apps.googleusercontent.com")
            userid = idinfo['sub']
            name = idinfo['name']
            email = idinfo['email']
            User.objects.create(googleID=userid,username=username,name=name,email=email)

            Moment.objects.create(momentID=username,name=name+"'s Moments",imgIDs=[],username=username)
            return HttpResponse("valid")
        else:
            return HttpResponse("invalid")
    else:
        return render(request, "registration.html")


@csrf_exempt
def home(request):
    # print(hashlib.md5(b"hello").hexdigest())
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
            if User.objects.filter(googleID=userid).exists():
                return HttpResponse("login,"+User.objects.get(googleID=userid).username)
            else:
                return HttpResponse("registration")
            # print("YAY", userid)
        except ValueError:
            # Invalid token
            pass
    return render(request, "home.html")