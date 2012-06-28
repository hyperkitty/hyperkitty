from django.utils import unittest
from django.test.client import Client

class SimpleTest(unittest.TestCase):
	def setUp(self):
		# Every test needs a client
		self.client = Client()
	
	def test_index_page(self):
		#Issue a get request
		response = self.client.get('/')
		
		self.assertEquals(response.status_code, 200)
