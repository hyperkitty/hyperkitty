import logging

from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class Rating(models.Model):
	list_address = models.CharField(max_length=50)
	messageid = models.CharField(max_length=100)
	user = models.ForeignKey(User)
	vote = models.SmallIntegerField()

class UserProfile(models.Model):
	# User Object
	user = models.OneToOneField(User)
	
	karma = models.IntegerField(default=1)
