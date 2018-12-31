from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from moments.models import Profile
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
            nameArgs = str(idinfo['name']).split(" ")
            email = idinfo['email']
            instance = User.objects.create(username=username,email=email,first_name=nameArgs[0], last_name=" ".join(nameArgs[1:]))
            Profile.objects.create(user=instance, googleID=userid)

            Moment.objects.create(momentID=username, name=instance.first_name+"'s Moments", imgIDs=[], username=username)

            request.session['username'] = username
            request.session['logged_in'] = "true"
            return HttpResponse("valid")
        else:
            request.session['logged_in'] = "false"
            return HttpResponse("invalid")
    else:
        return render(request, "registration.html")


@csrf_exempt
def home(request):
    # print(hashlib.md5(b"hello").hexdigest())
    # return HttpResponse('home')
    if request.POST:
        if request.POST.get("logout") == "true":
            request.session['logged_in'] = "false"
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
            if Profile.objects.filter(googleID=userid).exists():
                username = Profile.objects.get(googleID=userid).user.username
                request.session['username'] = username
                request.session['logged_in'] = "true"
                return HttpResponse("login,"+username)
            else:
                return HttpResponse("registration")
            # print("YAY", userid)
        except ValueError:
            # Invalid token
            request.session['logged_in'] = "false"
            pass
    return render(request, "home.html")