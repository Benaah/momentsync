from django.db import models


class Moment(models.Model):
    name = models.CharField(max_length=60)
    momentID = models.CharField(max_length=35)


    def __str__(self):
        return self.momentID

    def modelMethodExample(self):
        return "this is a cool test"

# class Images(models.Model):
