from django.http import HttpResponse
from django.urls import reverse

from twilio import twiml

from .models import Statement
from .models import Photo

from .decorators import sms_view
from .decorators import tip_view


@sms_view
def index(request, reporter=None):
    response = twiml.Response()

    if not reporter or not reporter.completed_enroll:
        response.redirect(reverse('sms:enroll'))
    elif "INFO" in request.POST['Body'].upper() and \
         len(request.POST['Body']) == 4:
        response.redirect(reverse("sms:info"))
    elif "HELP" in request.POST['Body'].upper() and \
         len(request.POST['Body']) == 4:
        response.redirect(reverse("sms:help"))
    else:
        response.redirect(reverse("sms:tip"))

    return response


@tip_view
def enroll(request, reporter=None, tip=None):
    response = twiml.Response()

    if request.COOKIES.get("enroll_step", None):
        response.redirect(request.COOKIES.get("enroll_step"))
    else:
        save_statement(request, tip)

        tip.new = False
        tip.save()

        welcome = "Thank you for contacting the Human Trafficking " \
                  "Response Unit's SMS tipline. It looks like this " \
                  "is your first tip.\n\n" \
                  "To keep in touch, we'd like some contact info so " \
                  "we can follow up.\n\n" \
                  "We'll only ask for this info once - two questions, " \
                  "30 seconds.\n\n" \
                  "First, what's your name?"
        response.message(welcome)

        resp = twilio_response(response)
        resp.set_cookie("enroll_step", reverse('sms:enroll-name'))
        return resp

    return response


@tip_view
def enroll_name(request, reporter=None, tip=None):
    response = twiml.Response()

    reporter.name = request.POST['Body']
    reporter.save()

    response.message("Much obliged - I have you registered as "
                     "{0}.\n Next, can I have your Tax "
                     "ID number?".format(reporter.name))
    resp = twilio_response(response)
    resp.set_cookie("enroll_step", reverse('sms:enroll-taxid'))

    return resp


@tip_view
def enroll_tax_id(request, reporter=None, tip=None):
    response = twiml.Response()

    if reporter and reporter.name:
        reporter.tax_id = request.POST['Body']
        reporter.completed_enroll = True
        reporter.save()

        response.message("Thank you for that info. I have you "
                         "enrolled as:\n{0} {1}\n\n"
                         "Thank you for contacting "
                         "the Human Trafficking Response Unit - "
                         "you can continue sharing your tip by "
                         "responding with text and photos."
                         "".format(reporter.name,
                                   reporter.tax_id))
        resp = twilio_response(response)
        resp.delete_cookie("enroll_step")
    else:
        response.redirect(reverse('sms:enroll'))
        resp = twilio_response(response)
        resp.delete_cookie("enroll_step")

    return resp


@sms_view
def help(request, reporter=None, tip=None):
    response = twiml.Response()

    response.message("Thank you for assisting the Human Trafficking Response "
                     "Unit."
                     "Working with a victim? Text INFO for 24/7 services "
                     "you can offer.\n\n"
                     "Got a tip to share? Just text what you are seeing or "
                     "send photos to this number.")

    return response


@sms_view
def info(request, reporter=None, tip=None):
    response = twiml.Response()

    response.message("The National Human Trafficking Resource Center is "
                     "available 24 hours a day, 7 days a week with real "
                     "resources to assist human trafficking victims.\n\n"
                     "They can be reached by calling (888) 373-7888 or "
                     "by texting HELP to 233733 (BEFREE).")

    return response


@tip_view
def tip(request, reporter=None, tip=None):
    response = twiml.Response()

    if reporter and reporter.completed_enroll:
        if tip.new:
            response.message("Thank you for submitting another tip to the "
                             "Human Trafficking Response Unit. Go ahead "
                             "and text your info and photos here.\n\n")
            tip.new = False
            tip.save()

        if request.POST.get("NumMedia", None):
            if int(request.POST['NumMedia']) > 0:
                response.redirect(reverse("sms:tip-photo"))
            else:
                response.redirect(reverse("sms:tip-statement"))
        else:
            response.redirect(reverse("sms:tip-statement"))
    else:
        response.redirect(reverse("sms:enroll"))

    return response


@tip_view
def tip_statement(request, reporter=None, tip=None):
    response = twiml.Response()

    if reporter and reporter.completed_enroll:
        save_statement(request, tip)
    else:
        response.redirect(reverse("sms:enroll"))

    return response


@tip_view
def tip_photo(request, reporter=None, tip=None):
    response = twiml.Response()

    if reporter and reporter.completed_enroll:
        if request.POST.get("NumMedia", None):
            if int(request.POST['NumMedia']) > 0:
                for i in range(int(request.POST['NumMedia'])):
                    photo = Photo(related_tip=tip,
                                  url=request.POST['MediaUrl{0}'.format(i)])
                    photo.save()
                response.message("Thank you for those {0} photos. If you have "
                                 "any further information or photos, "
                                 "reply here."
                                 "".format(int(request.POST['NumMedia'])))
        else:
            response.redirect(reverse("sms:tip-statement"))

        if request.POST.get('Body', None):
            save_statement(request, tip)
    else:
        response.redirect(reverse("sms:enroll"))

    return response


def twilio_response(response):
    return HttpResponse(str(response), content_type="application/xml")


def save_statement(request, tip):
    if request.POST.get('Body', None):
        statement = Statement(related_tip=tip)
        statement.body = request.POST['Body']
        statement.save()
        return statement
    else:
        return False
