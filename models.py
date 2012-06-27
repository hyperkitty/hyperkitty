import logging

from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class Rating(models.Model):
	# @TODO: instead of list_address, user list model from kittystore?
	list_address = models.CharField(max_length=50)

	# @TODO: instead of messsageid, use message model from kittystore?
	messageid = models.CharField(max_length=100)

	user = models.ForeignKey(User)

	vote = models.SmallIntegerField()

	def __unicode__(self):
		"""Unicode representation"""
		if self.vote == 1:
	  		return u'id = %s : %s voted up %s' % (self.id, unicode(self.user), self.messageid)
		else:
			return u'id = %s : %s voted down %s' % (self.id, unicode(self.user), self.messageid)

	


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

	def __unicode__(self):
		"""Unicode representation"""
		return u'%s' % (unicode(self.user))
