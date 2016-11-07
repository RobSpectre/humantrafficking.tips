from random import choice

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.mail import mail_admins
from django.template.loader import render_to_string

from twilio import twiml

from .models import Reporter
from .models import Tip
from .models import Statement
from .models import Location
from .models import Photo


@csrf_exempt
def index(request):
    response = twiml.Response()

    if request.method == "POST":
        reporter = get_reporter(request)

        if not reporter or not reporter.completed_enroll:
            response.redirect(reverse('sms:enroll'))
        elif request.COOKIES.get("tip", None):
            response.redirect(request.COOKIES["tip"])
        elif "INFO" in request.POST['Body'].upper() and \
             len(request.POST['Body']) == 4:
            response.redirect(reverse("sms:info"))
        elif "TIP" in request.POST['Body'].upper():
            response.redirect(reverse("sms:tip-start"))
        else:
            response.redirect(reverse("sms:help"))

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
                      "we can follow up. We'll only ask for this info " \
                      "once.\n\n First, what's your name?"
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
def start(request):
    response = twiml.Response()

    response.message("Suspect you are seeing human trafficking? Text TIP to "
                     "share what you are seeing.\n\n"
                     "Working with a victim? Text INFO for 24/7 services "
                     "you can offer.\n\n")

    resp = twilio_response(response)
    resp.set_cookie("start", reverse("sms:start-handler"))
    return resp


@csrf_exempt
def start_handler(request):
    response = twiml.Response()

    if request.method == "POST":
        if "TIP" in request.POST['Body'].upper():
            response.redirect(reverse("sms:tip-start"))

    resp = twilio_response(response)
    resp.delete_cookie("start")
    return resp


@csrf_exempt
def tip_start(request):
    response = twiml.Response()

    reporter = get_reporter(request)

    if reporter:
        tip = Tip(related_reporter=reporter)
        tip.save()

        response.message("Got it - we'll make this simple with three "
                         "quick questions. First, what did you see?\n\n"
                         "Write as much as you like - just say DONE when "
                         "you are finished.")
        resp = twilio_response(response)
        resp.set_cookie("tip", reverse("sms:tip-statement", args=[tip.id]))
        return resp

    return twilio_response(response)


@csrf_exempt
def tip_statement(request, tip):
    response = twiml.Response()

    reporter = get_reporter(request)

    encouragement = [
        "Got it - anything else?",
        "Thank you for that - is that all? Just say DONE if so or keep going.",
        "Gotcha - keep writing what you saw until you are DONE.",
        "Mmm hmm. What else did you see? If that's it, text DONE.",
        "Understood - keep going as long as necessary. Just text DONE when "
        "finished.",
        "I hear you. Is that all? Text DONE if so, or keep going."
    ]

    if reporter:
        tip = Tip.objects.get(id=tip)

        if "DONE" in request.POST['Body'].upper():
            response.message("Got it - thank you for that info. Next question -"
                             " where did you see this happen? Just text an "
                             "address or intersection.")
            resp = twilio_response(response)
            resp.set_cookie("tip", reverse("sms:tip-location", args=[tip.id]))
            return resp
        else:
            response.message(choice(encouragement))
            statement = Statement(related_tip=tip)
            statement.body = request.POST['Body']
            statement.save()

            return twilio_response(response)

    return twilio_response(response)


@csrf_exempt
def tip_location(request, tip):
    response = twiml.Response()

    reporter = get_reporter(request)

    if reporter:
        tip = Tip.objects.get(id=tip)
        location = Location(related_tip=tip, body=request.POST['Body'])
        location.save()

        response.message("Got it - thanks for providing the location."
                         " Last question - do you have any photos of "
                         "what you saw?\n\n If yes, just reply with them -"
                         " if not just reply NO.")

        resp = twilio_response(response)
        resp.set_cookie("tip", reverse("sms:tip-photo",
                                       args=[tip.id]))
        return resp

    return twilio_response(response)


@csrf_exempt
def tip_photo(request, tip):
    response = twiml.Response()

    reporter = get_reporter(request)

    if reporter:
        tip = Tip.objects.get(id=tip)

        if request.POST.get("NumMedia", None):
            if int(request.POST['NumMedia']) > 0:
                for i in range(int(request.POST['NumMedia'])):
                    photo = Photo(related_tip=tip,
                                  url=request.POST['MediaUrl{0}'.format(i)])
                    photo.save()
                response.message("Thank you for those {0} photos. Do you have "
                                 "any other photographs of what you saw? If "
                                 "so, "
                                 "just reply with them. If not, just text NO."
                                 "".format(int(request.POST['NumMedia'])))
                return twilio_response(response)
            else:
                response.message("Got it - thanks. Is that all the info "
                                 "you have for this tip? Text back YES or NO.")
                resp = twilio_response(response)

                resp.set_cookie("tip", reverse("sms:tip-confirm",
                                               args=[tip.id]))
                return resp


@csrf_exempt
def tip_confirm(request, tip):
    response = twiml.Response()

    reporter = get_reporter(request)

    if reporter:
        tip = Tip.objects.get(id=tip)

        if "Y" in request.POST['Body'].upper():
            send_tip(tip)
            response.message("Thank you so much for the tip {0}.\n\n"
                             "We appreciate you helping the Human "
                             "Trafficking Response Unit with this important "
                             "info - we'll be in touch soon if we have "
                             "questions.".format(reporter.first_name))
            resp = twilio_response(response)
            resp.delete_cookie("tip")
            return resp
        else:
            response.message("What else can we help you with?")
            return twilio_response(response)


@csrf_exempt
def help(request):
    response = twiml.Response()

    response.message("Thank you for contacting the Human Trafficking "
                     "Response Unit SMS tipline.")

    response.redirect(reverse("sms:start"))

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


def twilio_response(response):
    return HttpResponse(str(response), content_type="text/xml")


def get_reporter(request):
    query = Reporter.objects.filter(phone_number=request.POST['From'])
    if query and len(query) == 1:
        return query[0]

    return None


def send_tip(tip):
    statements = Statement.objects.filter(related_tip=tip)
    locations = Location.objects.filter(related_tip=tip)
    photos = Photo.objects.filter(related_tip=tip)
    reporter = tip.related_reporter

    context = {"tip": tip,
               "statements": statements,
               "locations": locations,
               "photos": photos,
               "reporter": reporter}

    html_message = render_to_string("tip_email.html", context)

    mail_admins("[humantrafficking.tips] New tip from {0} "
                "{1}.".format(tip.related_reporter.first_name,
                             tip.related_reporter.last_name),
                "You received a new tip.",
                html_message=html_message)

    return
