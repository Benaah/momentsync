from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import redirect
from momentsync import views

from ratelimit.decorators import ratelimit

from .models import Moment
from django.contrib.auth.models import User


@ratelimit(key='ip', rate='1/s')
def moment(request, momentID):
    if request.POST.get("logout") == "true":
        request.session['logged_in'] = "false"

    if not Moment.objects.filter(momentID=momentID).exists():
        return HttpResponse("404 Not Found")

    moment = Moment.objects.get(momentID=momentID)

    current_username = request.session['username']

    if 'username' in request.session and 'logged_in' in request.session and request.session['logged_in'] == "true" and moment.allowed_usernames.__contains__(current_username):
        print(request.session['username'], request.session['logged_in'])
        return render(request, 'moments/moment.html', {"moment": moment, "user": (User.objects.get(username=current_username))})
    else:
        return redirect(views.home)
