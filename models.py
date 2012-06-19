from django.db import models
from django.contrib.auth.models import User

class Rating(models.Model):
	list_address = models.CharField(max_length=50)
	messageid = models.CharField(max_length=30)
	user = models.ForeignKey(User, unique=True)
	vote = models.SmallIntegerField()
