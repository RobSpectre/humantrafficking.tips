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
    @patch('sms.tasks.email_tip.apply_async')
    def test_email_tip_new_statement(self, task):
        results = email_tip(self.tip.id)

        self.assertFalse(results)
        self.assertTrue(task.called)
        self.assertEquals(len(mail.outbox), 0)
        self.assertFalse(self.tip.sent)


class TestSmsTasksWithNewPhoto(TestCase):
    def setUp(self):
        later = timezone.now() - timedelta(minutes=3)

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
    @patch('sms.tasks.email_tip.apply_async')
    def test_email_tip_new_photo(self, task):
        statement = Statement.objects.all()[0]
        statement.date_created = statement.date_created - timedelta(minutes=6)

        results = email_tip(self.tip.id)

        self.assertFalse(results)
        self.assertTrue(task.called)
        self.assertEquals(len(mail.outbox), 0)
        self.assertFalse(self.tip.sent)


class TestSmsTasks(TestCase):
    def setUp(self):
        later = timezone.now() - timedelta(minutes=3)

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
    @override_settings(TWILIO_ACCOUNT_SID="ACxxxxx")
    @override_settings(TWILIO_AUTH_TOKEN="yyyyyyyy")
    @override_settings(TWILIO_PHONE_NUMBER="+15556667777")
    @patch('twilio.rest.resources.Messages.create')
    def test_email_tip(self, mock_messages):
        mock_messages.return_value = True
        results = email_tip(self.tip.id)

        self.assertTrue(results)
        self.assertEquals(len(results), 1)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject,
                          "[humantrafficking.tips] New tip from Shrimply "
                          "Pibbles")
        self.assertTrue(mock_messages.called)
        tip = Tip.objects.get(pk=self.tip.id)
        self.assertTrue(tip.sent)


class TestSmsTasksWithSentTip(TestCase):
    def setUp(self):
        self.reporter = Reporter.objects.create(name="Shrimply Pibbles",
                                                phone_number="+15556667777",
                                                completed_enroll=True,
                                                tax_id="12345")
        self.tip = Tip.objects.create(related_reporter=self.reporter)
        self.tip.sent = True
        self.tip.save()

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    @patch('sms.tasks.email_tip.apply_async')
    def test_email_tip_when_tip_already_sent(self, task):
        results = email_tip(self.tip.id)

        self.assertFalse(results)
        self.assertFalse(task.called)
        self.assertEquals(len(mail.outbox), 0)
