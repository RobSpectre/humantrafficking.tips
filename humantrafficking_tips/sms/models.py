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

    def __unicode__(self):
        if self.first_name and self.last_name:
            return "{0}, {1}".format(self.last_name,
                                     self.first_name)
        else:
            return "Unenrolled Reporter"


class Tip(HumanTraffickingSMSTipsModel):
    users = models.ManyToManyField(User, related_name="users")
    related_reporter = models.ForeignKey(Reporter, null=True, related_name="tips")


class Statement(HumanTraffickingSMSTipsModel):
    body = models.TextField(blank=True)
    related_tip = models.ForeignKey(Tip, null=True, related_name="statements")


class Photo(HumanTraffickingSMSTipsModel):
    image = models.ImageField(blank=True)
    url = models.CharField(max_length=255, blank=True)
    related_tip = models.ForeignKey(Tip, null=True, related_name="photos")


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
