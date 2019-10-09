from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import ArrayField
from annoying.fields import AutoOneToOneField


class InviteCode(models.Model):
    code = models.CharField(max_length=100)
    uses_left = models.IntegerField()

    def __str__(self):
        return "[" + str(self.uses_left) +"] " +self.code


class Moment(models.Model):
    momentID = models.CharField(primary_key=True, max_length=60)
    name = models.CharField(max_length=33, null=True)
    owner_username = models.CharField(max_length=35, null=True)

    allowed_usernames = ArrayField(models.CharField(max_length=35), default=list, null=True)
    description = models.CharField(max_length=500, default="Click here to customize the description of this moment page.")

    #MD5HASH
    imgIDs = ArrayField(models.CharField(max_length=32), default=list, null=True)

    def __str__(self):
        return self.momentID



class Profile(models.Model):
    user = AutoOneToOneField(User, on_delete=models.CASCADE)
    googleID = models.CharField(primary_key=True, max_length=35)

    def __str__(self):
        return self.user.username