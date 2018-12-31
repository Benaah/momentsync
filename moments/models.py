from django.contrib.auth.models import User
from django.db import models
from django.contrib.postgres.fields import ArrayField
from annoying.fields import AutoOneToOneField


class Moment(models.Model):
    momentID = models.CharField(primary_key=True, max_length=60)
    name = models.CharField(max_length=33, null=True)
    username = models.CharField(max_length=20, null=True)
    #MD5HASH
    imgIDs = ArrayField(models.CharField(max_length=32), default=list, null=True)

    def __str__(self):
        return self.momentID

    def modelMethodExample(self):
        return "this is a cool test"


class Profile(models.Model):
    user = AutoOneToOneField(User, on_delete=models.CASCADE)
    googleID = models.CharField(primary_key=True, max_length=35)

    def __str__(self):
        return self.user.username

# class Images(models.Model):


# class Session(models.Model):
#     sessionID = models.CharField(primary_key=True, max_length=24)
#     googleID = models.CharField(primary_key=True, max_length=35, null=True)
#     username = models.CharField(max_length=20, null=True)
