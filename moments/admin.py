from django.contrib import admin
from .models import Moment
from .models import Profile
from .models import InviteCode

admin.site.register(Moment)
admin.site.register(Profile)
admin.site.register(InviteCode)
# Register your models here.
