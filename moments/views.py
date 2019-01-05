from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import redirect
from momentsync import views


from .models import Moment
from django.contrib.auth.models import User
from .models import Profile

from momentsync import apps


@csrf_exempt
def moment(request, momentID):
    if request.POST.get("logout") == "true":
        print("yes")
        request.session['logged_in'] = "false"

    if 'username' in request.session and 'logged_in' in request.session and momentID == request.session['username'] and request.session['logged_in']=="true":
        print(request.session['username'], request.session['logged_in'])
        moment = Moment.objects.get(momentID=momentID)
        return render(request, 'moments/moment.html', {"moment": moment, "user": (User.objects.get(username=moment.username))})
    else:
        return redirect(views.home)
