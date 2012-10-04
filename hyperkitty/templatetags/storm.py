from django import template

register = template.Library()

@register.filter(name="count")
def count(expr):
    return expr.count()
