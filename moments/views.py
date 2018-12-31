from django.http import HttpResponse
from django.shortcuts import render

from .models import Moment
from django.contrib.auth.models import User
from .models import Profile

from momentsync import apps


def moment(request, momentID):

    # momentID = request.get_raw_uri().split("/moments/")[1]
    # print(momentID)



    if 'username' in request.session and 'logged_in' in request.session and momentID == request.session['username'] and request.session['logged_in']:
        print(request.session['username'], request.session['logged_in'])
        moment = Moment.objects.get(momentID=momentID)

        return render(request, 'moments/moment.html', {"moment": moment, "user": (User.objects.get(username=moment.username))})
    else:
        return HttpResponse("denied")
