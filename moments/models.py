from django.db import models
from django.contrib.postgres.fields import ArrayField


class Moment(models.Model):
    momentID = models.CharField(primary_key=True, max_length=60)
    name = models.CharField(max_length=33, default="PLACEHOLDER_NAME")
    googleID = models.CharField(max_length=35, default="PLACEHOLDER_GOOGLEID")
    #MD5HASH
    imgIDs = ArrayField(models.CharField(max_length=32), default=list)

    def __str__(self):
        return self.momentID

    def modelMethodExample(self):
        return "this is a cool test"


class User(models.Model):
    googleID = models.CharField(primary_key=True, max_length=35)
    #the main momentID will be the user's username
    username = models.CharField(max_length=20)
    name = models.CharField(max_length=35, default="PLACEHOLDER_NAME")
    email = models.EmailField(max_length=80)

    def __str__(self):
        return self.username

# class Images(models.Model):
