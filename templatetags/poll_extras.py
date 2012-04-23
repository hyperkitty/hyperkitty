from django import template
from django.http import HttpRequest
from django.utils.datastructures import SortedDict

register = template.Library()

@register.filter(name='sort')
def listsort(value):
    if isinstance(value, dict):
        new_dict = SortedDict()
        key_list = value.keys()
        key_list.sort()
        key_list.reverse()
        for key in key_list:
            values = value[key]
            values.sort()
            values.reverse()
            new_dict[key] = values
        return new_dict.items()
    elif isinstance(value, list):
        new_list = list(value)
        new_list.sort()
        return new_list
    else:
        return value
    listsort.is_safe = True

@register.filter(name="tomonth")
def to_month(value):
    months = ('January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December')
    return months[value -1]

@register.filter(name="strip_page")
def strip_page(value):
    print repr(value), repr(value)[-2]
    if not value:
        return value
    if value.endswith('/') and value[-3] == '/':
        end_with_number = False
        try: 
            if int(value[-2]) in range(0,10):
                end_with_number = True
            if end_with_number:
                output = value.rsplit('/', 2)
        except ValueError:
            output = value.rsplit('/', 1)
    else:
        output = value.rsplit('/', 1)
    return output[0]
