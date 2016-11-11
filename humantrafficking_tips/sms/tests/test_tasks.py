from datetime import timedelta

from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from django.core import mail

from mock import patch

from sms.models import Reporter
from sms.models import Tip
from sms.models import Statement
from sms.models import Photo

from sms.tasks import email_tip


class TestSmsTasksWithNewStatement(TestCase):
    def setUp(self):
        self.reporter = Reporter.objects.create(name="Shrimply Pibbles",
                                                phone_number="+15556667777",
                                                completed_enroll=True,
                                                tax_id="12345")
        self.tip = Tip.objects.create(related_reporter=self.reporter)
        Statement.objects.create(body="Shizzle", related_tip=self.tip)
        Photo.objects.create(url="https://example.com/shrimply.jpg",
                             related_tip=self.tip)

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    def test_email_tip_new_statement(self):
        results = email_tip(self.tip)

        self.assertFalse(results)
        self.assertEquals(len(mail.outbox), 0)


class TestSmsTasksWithNewPhoto(TestCase):
    def setUp(self):
        later = timezone.now() - timedelta(minutes=6)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = later

            self.reporter = Reporter.objects.create(name="Shrimply Pibbles",
                                                    phone_number="+15556667777",
                                                    completed_enroll=True,
                                                    tax_id="12345")
            self.tip = Tip.objects.create(related_reporter=self.reporter)
            Statement.objects.create(body="Shizzle", related_tip=self.tip)

        Photo.objects.create(url="https://example.com/shrimply.jpg",
                             related_tip=self.tip)

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    def test_email_tip_new_photo(self):
        statement = Statement.objects.all()[0]
        statement.date_created = statement.date_created - timedelta(minutes=6)

        results = email_tip(self.tip)

        self.assertFalse(results)
        self.assertEquals(len(mail.outbox), 0)


class TestSmsTasks(TestCase):
    def setUp(self):
        later = timezone.now() - timedelta(minutes=6)

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = later

            self.reporter = Reporter.objects.create(name="Shrimply Pibbles",
                                                    phone_number="+15556667777",
                                                    completed_enroll=True,
                                                    tax_id="12345")
            self.tip = Tip.objects.create(related_reporter=self.reporter)
            Statement.objects.create(body="Shizzle", related_tip=self.tip)
            Photo.objects.create(url="https://example.com/shrimply.jpg",
                                 related_tip=self.tip)

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    def test_email_tip(self):
        results = email_tip(self.tip)

        self.assertTrue(results)
        self.assertEquals(len(results), 1)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject,
                          "[humantrafficking.tips] New tip from Shrimply "
                          "Pibbles.")
