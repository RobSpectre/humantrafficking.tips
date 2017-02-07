from django.db import models
from django.contrib.auth.models import User


class HumanTraffickingSMSTipsModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)


class Reporter(HumanTraffickingSMSTipsModel):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)
    email_address = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=255, blank=True)
    completed_enroll = models.BooleanField(default=False)

    def __str__(self):
        if self.name:
            return "{0}".format(self.name)
        else:
            return "Unenrolled Reporter"


class Tip(HumanTraffickingSMSTipsModel):
    users = models.ManyToManyField(User, related_name="users")
    sent = models.BooleanField(default=False)
    new = models.BooleanField(default=True)
    related_reporter = models.ForeignKey(Reporter,
                                         null=True,
                                         related_name="tips")

    def __str__(self):
        return "Tip submitted {0} by {1}".format(self.date_created,
                                                 self.related_reporter.name)


class Statement(HumanTraffickingSMSTipsModel):
    body = models.TextField(blank=True)
    related_tip = models.ForeignKey(Tip, null=True, related_name="statements")

    def __str__(self):
        name = self.related_tip.related_reporter.name
        return "Statement submitted {0} by {1}".format(self.date_created,
                                                       name)


class Photo(HumanTraffickingSMSTipsModel):
    image = models.ImageField(blank=True)
    url = models.CharField(max_length=255, blank=True)
    related_tip = models.ForeignKey(Tip, null=True, related_name="photos")

    def __str__(self):
        name = self.related_tip.related_reporter.name
        return "Photo submitted {0} by {1}".format(self.date_created,
                                                   name)


class Message(HumanTraffickingSMSTipsModel):
    from_number = models.CharField(max_length=255)
    to_number = models.CharField(max_length=255)
    body = models.TextField()


class Location(HumanTraffickingSMSTipsModel):
    body = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    zipcode = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    related_tip = models.ForeignKey(Tip, null=True, related_name="locations")
