from django import template

from hyperkitty.lib import stripped_subject

register = template.Library()

@register.filter(name="count")
def count(expr):
    return expr.count()

@register.filter(name="strip_subject")
def strip_subject(subject, mlist):
    return stripped_subject(mlist, subject)
