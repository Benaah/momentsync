from django.shortcuts import render

from .models import Moment
from .models import User

from momentsync import apps


def moment(request, momentID):

    # momentID = request.get_raw_uri().split("/moments/")[1]
    # print(momentID)

    moment = Moment.objects.get(momentID=momentID)

    return render(request, 'moments/moment.html', {"moment": moment, "user": (User.objects.get(username=moment.username))})
