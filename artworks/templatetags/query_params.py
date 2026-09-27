"""Query-string helpers for filter links.

The browse filters are links rather than a form, so each one has to carry the
*other* filters along with it -- clicking a medium must not silently drop the
tag you already chose. Building those URLs by hand in the template would mean
repeating every parameter in every link, and forgetting one is invisible until
someone combines two filters.
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    """Return the current query string with `kwargs` applied.

    An empty value removes the parameter instead of setting it blank, so 'All'
    produces `?tag=3` rather than `?medium=&tag=3` -- the view treats those the
    same, but only one of them is a URL you would want to read or share.
    """
    params = context['request'].GET.copy()

    for key, value in kwargs.items():
        if value in (None, '', False):
            params.pop(key, None)
        else:
            params[key] = value

    encoded = params.urlencode()
    # '?' alone rather than '' so the href is never empty: an empty href points
    # at the current URL *including* its query string, which would make the
    # 'All' option a no-op once a filter was active.
    return f'?{encoded}' if encoded else '?'
