from django.shortcuts import render
from django.http import HttpResponse

from .models import Moment

def moment(request):

    momentID = request.get_raw_uri().split("/moments/")[1]
    print(momentID)

    return render(request, 'moments/moment.html', {"model": (Moment.objects.get(momentID=momentID))})
