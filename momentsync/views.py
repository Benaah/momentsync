from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.shortcuts import redirect

from moments.models import Profile
from moments.models import Moment
from moments.models import InviteCode

from google.oauth2 import id_token
from google.auth.transport import requests

from ratelimit.decorators import ratelimit

def about(request):
    return render(request, "about.html")

@ratelimit(key='ip', rate='10/m')
def registration(request):
    print(request)
    if request.POST:
        username = request.POST.get("username", "")
        token = request.POST.get("googleToken","")
        inviteCode = request.POST.get("inviteCode","")

        if InviteCode.objects.filter(code=inviteCode).exists() and InviteCode.objects.get(code=inviteCode).uses_left>0:
            invitecode_db = InviteCode.objects.get(code=inviteCode)
            invitecode_db.uses_left -= 1
            invitecode_db.save()
        else:
            return HttpResponse("bad_invite")

        if not User.objects.filter(username=username).exists():
            idinfo = id_token.verify_oauth2_token(token, requests.Request(),
                                                  "133754882345-b044u4p8radcpasmq9s38sc3k0hiktsb.apps.googleusercontent.com")
            userid = idinfo['sub']
            nameArgs = str(idinfo['name']).split(" ")
            email = idinfo['email']
            instance = User.objects.create(username=username,email=email,first_name=nameArgs[0], last_name=" ".join(nameArgs[1:]))
            Profile.objects.create(user=instance, googleID=userid)

            Moment.objects.create(momentID=username, name=instance.first_name+"'s Moments", imgIDs=[], owner_username=username, allowed_usernames=[username])

            request.session['username'] = username
            request.session['logged_in'] = "true"
            return HttpResponse("valid")
        else:
            request.session['logged_in'] = "false"
            return HttpResponse("invalid")
    else:
        return render(request, "registration.html")


@ratelimit(key='ip', rate='10/m')
def home(request):

    if 'username' in request.session and 'logged_in' in request.session and request.session['logged_in']=="true":
        return redirect("/moments/"+request.session['username'])
    else:
        if request.POST:

            token = request.POST.get("idtoken", "")
            try:
                idinfo = id_token.verify_oauth2_token(token, requests.Request(),
                                                      "133754882345-b044u4p8radcpasmq9s38sc3k0hiktsb.apps.googleusercontent.com")

                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError('Wrong issuer.')

                userid = idinfo['sub']
                if Profile.objects.filter(googleID=userid).exists():
                    username = Profile.objects.get(googleID=userid).user.username
                    request.session['username'] = username
                    request.session['logged_in'] = "true"
                    return HttpResponse("login,"+username)
                else:
                    return HttpResponse("registration")
            except ValueError:
                request.session['logged_in'] = "false"
                pass
        return render(request, "home.html")