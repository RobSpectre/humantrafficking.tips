from datetime import timedelta

from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from django.core import mail

from mock import patch
from mock import Mock

from sms.models import Reporter
from sms.models import Tip
from sms.models import Statement
from sms.models import Photo

from sms.tasks import process_tip
from sms.tasks import email_tip
from sms.tasks import sms_reporter
from sms.tasks import collect_tip_context


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
    @patch('sms.tasks.process_tip.apply_async')
    @patch('sms.tasks.email_tip.apply_async')
    @patch('sms.tasks.sms_reporter.apply_async')
    def test_process_tip_new_statement(self, mock_sms_reporter,
                                       mock_email_tip, mock_task):
        results = process_tip(self.tip.id)

        self.assertFalse(results)
        self.assertTrue(mock_task.called)
        self.assertFalse(mock_email_tip.called)
        self.assertFalse(mock_sms_reporter.called)
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
    @patch('sms.tasks.process_tip.apply_async')
    @patch('sms.tasks.email_tip.apply_async')
    @patch('sms.tasks.sms_reporter.apply_async')
    def test_process_tip_new_photo(self, mock_sms_reporter,
                                   mock_email_tip, mock_task):
        statement = Statement.objects.all()[0]
        statement.date_created = statement.date_created - timedelta(minutes=6)

        results = process_tip(self.tip.id)

        self.assertFalse(results)
        self.assertTrue(mock_task.called)
        self.assertFalse(mock_sms_reporter.called)
        self.assertFalse(mock_email_tip.called)
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

    @patch('sms.tasks.email_tip.apply_async')
    @patch('sms.tasks.sms_reporter.apply_async')
    def test_process_tip(self, mock_sms_reporter, mock_email_tip):
        results = process_tip(self.tip.id)

        self.assertTrue(results)
        self.assertTrue(mock_sms_reporter.called)
        self.assertTrue(mock_email_tip.called)

        tip = Tip.objects.all()[0]
        self.assertTrue(tip.sent)

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    def test_email_tip(self):
        results = email_tip(self.tip.id)

        self.assertTrue(results)
        self.assertEquals(len(results), 1)
        self.assertEquals(len(mail.outbox), 1)

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    @override_settings(TWILIO_ACCOUNT_SID="ACxxxxx")
    @override_settings(TWILIO_AUTH_TOKEN="yyyyyyyy")
    @override_settings(TWILIO_PHONE_NUMBER="15556667777")
    @patch('twilio.rest.resources.Messages.create')
    def test_sms_reporter(self, mock_messages):
        mock_message = Mock()
        mock_message.body.return_value = True
        mock_messages.return_value = mock_message
        results = sms_reporter(self.tip.id)

        self.assertTrue(results)
        mock_messages.assert_called_once_with(from_="+15556667777",
                                              to=self.reporter.phone_number,
                                              body="Thank you for that tip "
                                                   "with 1 message and 1 "
                                                   "photo.\nThe Human "
                                                   "Trafficking Response Unit"
                                                   " will be in touch soon.")

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    @override_settings(TWILIO_ACCOUNT_SID="ACxxxxx")
    @override_settings(TWILIO_AUTH_TOKEN="yyyyyyyy")
    @override_settings(TWILIO_PHONE_NUMBER="15556667777")
    @patch('twilio.rest.resources.Messages.create')
    def test_correct_statement_and_photo_count(self, mock_messages):
        mock_message = Mock()
        mock_message.body.return_value = True
        mock_messages.return_value = mock_message

        Statement.objects.create(body="We could be kings...",
                                 related_tip=self.tip)
        Statement.objects.create(body="but we were damned from the start.",
                                 related_tip=self.tip)

        results = sms_reporter(self.tip.id)

        self.assertTrue(results)
        mock_messages.assert_called_once_with(from_="+15556667777",
                                              to=self.reporter.phone_number,
                                              body="Thank you for that tip "
                                                   "with 3 messages and 1 "
                                                   "photo.\nThe Human "
                                                   "Trafficking Response Unit"
                                                   " will be in touch soon.")

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    @override_settings(TWILIO_ACCOUNT_SID="ACxxxxx")
    @override_settings(TWILIO_AUTH_TOKEN="yyyyyyyy")
    @override_settings(TWILIO_PHONE_NUMBER="15556667777")
    @patch('twilio.rest.resources.Messages.create')
    def test_correct_statement_count_no_photo(self, mock_messages):
        mock_message = Mock()
        mock_message.body.return_value = True
        mock_messages.return_value = mock_message

        new_tip = Tip.objects.create(related_reporter=self.reporter)

        Statement.objects.create(body="We could be kings...",
                                 related_tip=new_tip)

        results = sms_reporter(new_tip.id)

        self.assertTrue(results)
        mock_messages.assert_called_once_with(from_="+15556667777",
                                              to=self.reporter.phone_number,
                                              body="Thank you for that tip "
                                                   "with 1 message.\nThe Human "
                                                   "Trafficking Response Unit"
                                                   " will be in touch soon.")

    @override_settings(ADMINS=[('Shrimply Pibbles', 'pibbles@shrimply.org')])
    @override_settings(TWILIO_ACCOUNT_SID="ACxxxxx")
    @override_settings(TWILIO_AUTH_TOKEN="yyyyyyyy")
    @override_settings(TWILIO_PHONE_NUMBER="15556667777")
    @patch('twilio.rest.resources.Messages.create')
    def test_correct_photo_count_no_statement(self, mock_messages):
        mock_message = Mock()
        mock_message.body.return_value = True
        mock_messages.return_value = mock_message

        new_tip = Tip.objects.create(related_reporter=self.reporter)

        Photo.objects.create(url="https://example.com/shrimply.jpg",
                             related_tip=new_tip)

        results = sms_reporter(new_tip.id)

        self.assertTrue(results)
        mock_messages.assert_called_once_with(from_="+15556667777",
                                              to=self.reporter.phone_number,
                                              body="Thank you for that tip "
                                                   "with 1 photo.\nThe Human "
                                                   "Trafficking Response Unit"
                                                   " will be in touch soon.")

    def test_collect_tip_context(self):
        Statement.objects.create(body="We could be kings...",
                                 related_tip=self.tip)
        Statement.objects.create(body="but we were damned from the start.",
                                 related_tip=self.tip)

        context = collect_tip_context(self.tip.id)
        self.assertEquals(3, len(context['statements']))
        self.assertEquals(1, len(context['photos']))


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
    @patch('sms.tasks.sms_reporter.apply_async')
    def test_process_tip_when_tip_already_sent(self, task):
        results = process_tip(self.tip.id)

        self.assertFalse(results)
        self.assertFalse(task.called)
        self.assertEquals(len(mail.outbox), 0)
