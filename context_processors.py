from django.conf import settings

def app_name(context):
    return {'app_name' : settings.APP_NAME}