from __future__ import absolute_import, unicode_literals

from datetime import timedelta

from celery import shared_task

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from .models import Statement
from .models import Location
from .models import Photo


@shared_task
def email_tip(tip):
    statements = Statement.objects.filter(related_tip=tip)
    locations = Location.objects.filter(related_tip=tip)
    photos = Photo.objects.filter(related_tip=tip)
    reporter = tip.related_reporter

    for statement in statements:
        delta = timezone.now() - statement.date_created
        if delta < timedelta(minutes=3):
            return False

    for photo in photos:
        delta = timezone.now() - photo.date_created
        if delta < timedelta(minutes=3):
            return False

    context = {"tip": tip,
               "statements": statements,
               "locations": locations,
               "photos": photos,
               "reporter": reporter}

    html_message = render_to_string("tip_email.html", context)

    results = []
    for admin in settings.ADMINS:
        results.append(send_mail("[humantrafficking.tips] New tip from {0}"
                                 ".".format(tip.related_reporter.name),
                                 "You received a new tip.",
                                 "no-reply@humantrafficking.tips",
                                 [admin[1]],
                                 html_message=html_message))

    return results
