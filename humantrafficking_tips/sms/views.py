from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from twilio import twiml

from .models import Reporter
from .models import Tip
from .models import Statement
from .models import Photo

from .tasks import email_tip


@csrf_exempt
def index(request):
    response = twiml.Response()

    if request.method == "POST":
        reporter = get_reporter(request)

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

    return twilio_response(response)


@csrf_exempt
def enroll(request):
    response = twiml.Response()

    if request.method == "POST":
        if request.COOKIES.get("enroll_step", None):
            response.redirect(request.COOKIES.get("enroll_step"))
        else:
            reporter = Reporter()
            reporter.phone_number = request.POST['From']
            reporter.save()

            welcome = "Thank you for contacting the Human Trafficking " \
                      "Response Unit's SMS tipline. It looks like this " \
                      "is your first tip.\n\n" \
                      "To keep in touch, we'd like some contact info so " \
                      "we can follow up.\n\n" \
                      "What's your name?  We'll only ask for this info once."
            response.message(welcome)

            resp = twilio_response(response)
            resp.set_cookie("enroll_step", reverse('sms:enroll-name'))
            return resp

    return twilio_response(response)


@csrf_exempt
def enroll_name(request):
    response = twiml.Response()

    if request.method == "POST":
        reporter = get_reporter(request)
        if reporter:
            reporter.name = request.POST['Body']
            reporter.save()

            response.message("Much obliged - I have you registered as "
                             "{0}.\n Next, can I have your Tax "
                             "ID number?".format(reporter.name))
            resp = twilio_response(response)
            resp.set_cookie("enroll_step", reverse('sms:enroll-taxid'))
            return resp
        else:
            response.redirect(reverse('sms:enroll'))
            resp = twilio_response(response)
            resp.delete_cookie("enroll_step")
            return resp

    return twilio_response(response)


@csrf_exempt
def enroll_tax_id(request):
    response = twiml.Response()

    if request.method == "POST":
        reporter = get_reporter(request)
        if reporter:
            reporter.tax_id = request.POST['Body']
            reporter.completed_enroll = True
            reporter.save()

            response.message("Thank you for that info. I have you "
                             "enrolled as:\n{0} {1}\n\n"
                             "To keep submitting tips, just text us "
                             "at this number. Thank you again for helping "
                             "the Human Trafficking Response Unit."
                             "".format(reporter.name,
                                       reporter.tax_id))
            resp = twilio_response(response)
            resp.delete_cookie("enroll_step")
            return resp
        else:
            response.redirect(reverse('sms:enroll'))
            resp = twilio_response(response)
            resp.delete_cookie("enroll_step")
            return resp

    return twilio_response(response)


@csrf_exempt
def help(request):
    response = twiml.Response()

    response.message("Thank you for assisting the Human Trafficking Response "
                     "Unit."
                     "Working with a victim? Text INFO for 24/7 services "
                     "you can offer.\n\n"
                     "Got a tip to share? Just text what you are seeing or "
                     "send photos to this number.")

    return twilio_response(response)


@csrf_exempt
def info(request):
    response = twiml.Response()

    response.message("The National Human Trafficking Resource Center is "
                     "available 24 hours a day, 7 days a week with real "
                     "resources to assist human trafficking victims.\n\n"
                     "They can be reached by calling (888) 373-7888 or "
                     "by texting HELP to 233733 (BEFREE).")

    return twilio_response(response)


@csrf_exempt
def tip(request):
    response = twiml.Response()

    reporter = get_reporter(request)

    if reporter:
        reporter_tip = Tip.objects.filter(related_reporter=reporter,
                                          sent=False)

        if len(reporter_tip) > 0:
            tip = reporter_tip[0]
        else:
            tip = Tip(related_reporter=reporter)
            tip.save()
            email_tip.apply_async(args=[tip.id], countdown=180)
            response.message("Thank you for submitting a tip to the "
                             "Human Trafficking Response Unit. Go ahead "
                             "and text your info and photos here.\n\n")

        if request.POST.get("NumMedia", None):
            if int(request.POST['NumMedia']) > 0:
                response.redirect(reverse("sms:tip-photo"))
            else:
                response.redirect(reverse("sms:tip-statement"))
        else:
            response.redirect(reverse("sms:tip-statement"))
    else:
        response.redirect(reverse("sms:enroll"))

    return twilio_response(response)


@csrf_exempt
def tip_statement(request):
    response = twiml.Response()

    reporter = get_reporter(request)

    if reporter:
        reporter_tip = Tip.objects.filter(related_reporter=reporter,
                                          sent=False)
        if len(reporter_tip) > 0:
            tip = reporter_tip[0]
        else:
            tip = Tip(related_reporter=reporter)
            tip.save()
            response.message("Thank you for sending in another tip to "
                             "the Human Trafficking Unit. If you have "
                             "further information and photos, simply "
                             "respond here.")

        statement = Statement(related_tip=tip)
        statement.body = request.POST['Body']
        statement.save()
    else:
        response.redirect(reverse("sms:enroll"))

    return twilio_response(response)


@csrf_exempt
def tip_photo(request):
    response = twiml.Response()

    reporter = get_reporter(request)

    if reporter:
        reporter_tip = Tip.objects.filter(related_reporter=reporter,
                                          sent=False)
        if len(reporter_tip) > 0:
            tip = reporter_tip[0]
        else:
            tip = Tip(related_reporter=reporter)
            tip.save()

        if request.POST.get("NumMedia", None):
            if int(request.POST['NumMedia']) > 0:
                for i in range(int(request.POST['NumMedia'])):
                    photo = Photo(related_tip=tip,
                                  url=request.POST['MediaUrl{0}'.format(i)])
                    photo.save()
                response.message("Thank you for those {0} photos. If you have "
                                 "any further information or photos, simply "
                                 "reply here."
                                 "".format(int(request.POST['NumMedia'])))

        if request.POST.get('Body', None):
            statement = Statement(related_tip=tip)
            statement.body = request.POST['Body']
            statement.save()
        else:
            response.redirect(reverse("sms:tip-statement"))
    else:
        response.redirect(reverse("sms:enroll"))

    return twilio_response(response)


def twilio_response(response):
    return HttpResponse(str(response), content_type="text/xml")


def get_reporter(request):
    query = Reporter.objects.filter(phone_number=request.POST['From'])
    if query and len(query) == 1:
        return query[0]

    return None
