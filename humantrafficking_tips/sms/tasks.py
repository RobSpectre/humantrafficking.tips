from __future__ import absolute_import, unicode_literals

from datetime import timedelta

from celery import shared_task

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

from twilio.rest import TwilioRestClient

from .models import Tip
from .models import Statement
from .models import Location
from .models import Photo


@shared_task
def process_tip(tip_id):
    tip = Tip.objects.get(pk=tip_id)

    if not tip or tip.sent:
        return False

    context = collect_tip_context(tip)

    for statement in context['statements']:
        delta = timezone.now() - statement.date_created
        if delta < timedelta(minutes=1):
            process_tip.apply_async(args=[tip.id],
                                    countdown=60)
            return False

    for photo in context['photos']:
        delta = timezone.now() - photo.date_created
        if delta < timedelta(minutes=1):
            process_tip.apply_async(args=[tip.id],
                                    countdown=60)
            return False

    email_tip.apply_async(args=[tip_id])

    sms_reporter.apply_async(args=[tip_id])

    tip.sent = True
    tip.save()

    return True


@shared_task
def email_tip(tip_id):
    context = collect_tip_context(tip_id)

    html_message = render_to_string("tip_email.html", context)

    results = []
    for admin in settings.ADMINS:
        results.append(send_mail("[humantrafficking.tips] New tip from {0}"
                                 "".format(context['reporter'].name),
                                 "You received a new tip.",
                                 "no-reply@humantrafficking.tips",
                                 [admin[1]],
                                 html_message=html_message))
    return results


@shared_task
def sms_reporter(tip_id):
    context = collect_tip_context(tip_id)

    client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID,
                              settings.TWILIO_AUTH_TOKEN)

    statements_total = len(context['statements'])
    photos_total = len(context['photos'])

    msg = client.messages.create(from_="+{0}"
                                 "".format(settings.TWILIO_PHONE_NUMBER),
                                 to=context['reporter'].phone_number,
                                 body="Thank you for that tip with {0} "
                                 "messages and {0} photos. The Human "
                                 "Trafficking Response Unit "
                                 "will be in touch soon with followup "
                                 "questions.".format(statements_total,
                                                     photos_total))
    return msg.body


def collect_tip_context(tip_id):
    tip = Tip.objects.get(pk=tip_id)
    statements = Statement.objects.filter(related_tip=tip)
    locations = Location.objects.filter(related_tip=tip)
    photos = Photo.objects.filter(related_tip=tip)
    reporter = tip.related_reporter

    context = {"tip": tip,
               "statements": statements,
               "locations": locations,
               "photos": photos,
               "reporter": reporter}

    return context
