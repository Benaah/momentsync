from django.db import models
from django.contrib.postgres.fields import ArrayField


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


class User(models.Model):
    googleID = models.CharField(primary_key=True, max_length=35)
    #the main momentID will be the user's username
    username = models.CharField(max_length=20, null=True)
    name = models.CharField(max_length=35, default="PLACEHOLDER_NAME", null=True)
    email = models.EmailField(max_length=80, null=True)

    def __str__(self):
        return self.username

# class Images(models.Model):
