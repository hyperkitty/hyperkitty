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

	def _get_votes(self):
   	    "Returns all the votes by a user"
            # Extract all the votes by this user
     	    try:
	    	votes = Rating.objects.filter(user = self.user)
            except Rating.DoesNotExist:
		votes = {}

     	    return votes


	votes = property(_get_votes)
