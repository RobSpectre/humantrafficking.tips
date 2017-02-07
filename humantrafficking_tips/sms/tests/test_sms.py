try:  # pragma: no cover
    from http.cookies import SimpleCookie
except ImportError:  # pragma: no cover
    from Cookie import SimpleCookie

from django.test import TestCase
from django.test import Client
from django.test import override_settings

from twilio.util import RequestValidator

from sms.models import Reporter
from sms.models import Tip
from sms.models import Statement
from sms.models import Photo

from mock import patch


class HumanTraffickingTipsSmsTestClient(Client):
    def sms(self, body, path="/sms/", to="+15558675309", from_="+15556667777",
            extra_params=None):
        params = {"MessageSid": "CAtesting",
                  "AccountSid": "ACxxxxx",
                  "To": to,
                  "From": from_,
                  "Body": body,
                  "Direction": "inbound",
                  "FromCity": "BROOKLYN",
                  "FromState": "NY",
                  "FromCountry": "US",
                  "FromZip": "55555"}

        if extra_params:
            for k, v in extra_params.items():
                params[k] = v

        HTTP_HOST = "example.com"
        validator = RequestValidator("yyyyyyyy")
        absolute_url = "http://{0}{1}".format(HTTP_HOST,
                                              path)
        signature = validator.compute_signature(absolute_url,
                                                params)

        return self.post(path, params,
                         HTTP_X_TWILIO_SIGNATURE=signature,
                         HTTP_HOST=HTTP_HOST)


@override_settings(TWILIO_AUTH_TOKEN="yyyyyyyy")
class HumanTraffickingTipsSmsTestCase(TestCase):
    def setUp(self):
        self.client = HumanTraffickingTipsSmsTestClient()

    def assert_twiml(self, response):
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "<Response")


class TestEnrollNoReporter(HumanTraffickingTipsSmsTestCase):
    def test_enroll_when_reporter_not_found(self):
        response = self.client.sms("Test.")

        self.assert_twiml(response)
        self.assertContains(response, "Redirect")
        self.assertContains(response, "/enroll/")
        self.assertFalse(Tip.objects.all())

    @patch('sms.tasks.process_tip.apply_async')
    def test_enroll_ask_for_name(self, mock_process_tip):
        response = self.client.sms("Test.", path="/sms/enroll/")

        self.assert_twiml(response)
        self.assertEquals(1, len(Reporter.objects.all()))
        self.assertTrue(Reporter.objects.all()[0].phone_number,
                        "+15556667777")
        self.assertContains(response, "hat's your name")
        self.assertEquals(self.client.cookies['enroll_step'].value,
                          "/sms/enroll/name/")
        self.assertTrue(mock_process_tip.called)

    @patch('sms.tasks.process_tip.apply_async')
    def test_enroll_ask_for_tax_id(self, mock_process_tip):
        self.client.sms("Test.", path="/sms/enroll/")
        response = self.client.sms("Shrimply Pibbles",
                                   path="/sms/enroll/name/")

        self.assert_twiml(response)
        self.assertEquals(1, len(Reporter.objects.all()))
        self.assertContains(response, "Shrimply Pibbles")
        self.assertEquals(Reporter.objects.all()[0].name,
                          "Shrimply Pibbles")
        self.assertEquals(self.client.cookies['enroll_step'].value,
                          "/sms/enroll/tax_id/")
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(1, len(Tip.objects.all()))

    @patch('sms.tasks.process_tip.apply_async')
    def test_enroll_complete(self, mock_process_tip):
        self.client.sms("Test.", path="/sms/enroll/")
        self.client.sms("Shrimply Pibbles",
                        path="/sms/enroll/name/")
        response = self.client.sms("12345",
                                   path="/sms/enroll/tax_id/")

        self.assert_twiml(response)
        self.assertEquals(1, len(Reporter.objects.all()))
        self.assertContains(response, "Shrimply Pibbles")
        self.assertContains(response, "12345")
        self.assertEquals(Reporter.objects.all()[0].tax_id, "12345")
        self.assertTrue(Reporter.objects.all()[0].completed_enroll)
        self.assertEquals(self.client.cookies['enroll_step'].value, '')
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(1, len(Tip.objects.all()))

    @patch('sms.tasks.process_tip.apply_async')
    def test_enroll_cookie_routing(self, mock_process_tip):
        self.client.cookies = SimpleCookie({"enroll_step":
                                            "/sms/enroll/test/"})
        response = self.client.sms("Test.", path="/sms/enroll/")

        self.assert_twiml(response)
        self.assertContains(response, "/sms/enroll/test/")
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(1, len(Tip.objects.all()))

    def test_enroll_name_get(self):
        response = self.client.get("/sms/enroll/name/")

        self.assertTrue(response.status_code, 403)

    @patch('sms.tasks.process_tip.apply_async')
    def test_enroll_taxid_redirect(self, mock_process_tip):
        response = self.client.sms("Test.", path="/sms/enroll/tax_id/")

        self.assert_twiml(response)
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/enroll/")
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(1, len(Tip.objects.all()))

    def test_enroll_taxid_get(self):
        response = self.client.get("/sms/enroll/tax_id/")

        self.assertEquals(response.status_code, 403)

    @patch('sms.tasks.process_tip.apply_async')
    def test_enroll_first_statement_gets_saved(self, mock_process_tip):
        response = self.client.sms("Shizzle.", path="/sms/enroll/")

        self.assert_twiml(response)
        self.assertEquals(1, len(Statement.objects.all()))
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(1, len(Tip.objects.all()))


class TestEnrollReporterExists(HumanTraffickingTipsSmsTestCase):
    def setUp(self):
        Reporter.objects.create(name="Shrimply Pibbles",
                                phone_number="+15556667777",
                                completed_enroll=True,
                                tax_id="12345")
        self.client = HumanTraffickingTipsSmsTestClient()

    def test_enroll_when_reporter_found(self):
        response = self.client.sms("Test.")

        self.assert_twiml(response)
        self.assertNotContains(response, "/enroll/")
        self.assertFalse(self.client.cookies.get('enroll_step', None))

    def test_reporter_representation(self):
        reporter = Reporter.objects.all()[0]
        self.assertEquals(str(reporter),
                          "Shrimply Pibbles")

    def test_reporter_unenrolled_representations(self):
        reporter = Reporter.objects.create(phone_number="+15556667777")
        self.assertEquals(str(reporter),
                          "Unenrolled Reporter")


class TipRouting(HumanTraffickingTipsSmsTestCase):
    def setUp(self):
        Reporter.objects.create(name="Shrimply Pibbles",
                                phone_number="+15556667777",
                                completed_enroll=True,
                                tax_id="12345")
        self.client = HumanTraffickingTipsSmsTestClient()

    @patch('sms.tasks.process_tip.apply_async')
    def test_statement_routing(self, process_tip):
        process_tip.return_value = False
        response = self.client.sms("Test.", path="/sms/tip/")

        self.assert_twiml(response)
        self.assertContains(response, "Thank you")
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/tip/statement/")
        self.assertTrue(process_tip.called)
        self.assertEquals(1, len(Tip.objects.all()))

    @patch('sms.tasks.process_tip.apply_async')
    def test_photo_routing(self, process_tip):
        process_tip.return_value = False
        response = self.client.sms("Test.", path="/sms/tip/",
                                   extra_params={"NumMedia": "1"})

        self.assert_twiml(response)
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/tip/photo/")
        self.assertTrue(process_tip.called)
        self.assertEquals(1, len(Tip.objects.all()))

    @patch('sms.tasks.process_tip.apply_async')
    def test_photo_routing_num_media_zero(self, process_tip):
        process_tip.return_value = False
        response = self.client.sms("Test.", path="/sms/tip/",
                                   extra_params={"NumMedia": "0"})

        self.assert_twiml(response)
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/tip/statement/")
        self.assertTrue(process_tip.called)
        self.assertEquals(1, len(Tip.objects.all()))


class TipRoutingTipExists(HumanTraffickingTipsSmsTestCase):
    def setUp(self):
        reporter = Reporter.objects.create(name="Shrimply Pibbles",
                                           phone_number="+15556667777",
                                           completed_enroll=True,
                                           tax_id="12345")
        tip = Tip.objects.create(related_reporter=reporter)
        tip.new = False
        tip.save()

        self.client = HumanTraffickingTipsSmsTestClient()

    @patch('sms.tasks.process_tip.apply_async')
    def test_tip_exists_but_not_sent(self, process_tip):
        process_tip.return_value = False
        response = self.client.sms("Test.", path="/sms/tip/",
                                   extra_params={"NumMedia": "0"})

        self.assert_twiml(response)
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/tip/statement/")
        self.assertFalse(process_tip.called)
        self.assertEquals(len(Tip.objects.all()), 1)
        self.assertNotContains(response, "<Message>")

    def test_reporter_representation(self):
        tip = Tip.objects.all()[0]
        self.assertEquals(str(tip),
                          "Tip submitted {0} by Shrimply "
                          "Pibbles".format(tip.date_created))


class TipRoutingNoEnroll(HumanTraffickingTipsSmsTestCase):
    @patch('sms.tasks.process_tip.apply_async')
    def test_tip_no_enroll(self, mock_process_tip):
        response = self.client.sms("Test.", path="/sms/tip/")

        self.assert_twiml(response)
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/enroll/")
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(len(Tip.objects.all()), 1)

    @patch('sms.tasks.process_tip.apply_async')
    def test_photo_no_enroll(self, mock_process_tip):
        response = self.client.sms("Test.", path="/sms/tip/photo/")

        self.assert_twiml(response)
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/enroll/")
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(len(Tip.objects.all()), 1)

    @patch('sms.tasks.process_tip.apply_async')
    def test_statement_no_enroll(self, mock_process_tip):
        response = self.client.sms("Test.", path="/sms/tip/statement/")

        self.assert_twiml(response)
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/enroll/")
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(len(Tip.objects.all()), 1)


class TestStatement(HumanTraffickingTipsSmsTestCase):
    def setUp(self):
        Reporter.objects.create(name="Shrimply Pibbles",
                                phone_number="+15556667777",
                                completed_enroll=True,
                                tax_id="12345")
        self.client = HumanTraffickingTipsSmsTestClient()

    @patch('sms.tasks.process_tip.apply_async')
    def test_first_statement(self, mock_process_tip):
        response = self.client.sms("I found some shady shizzle.",
                                   path="/sms/tip/statement/")

        self.assert_twiml(response)
        self.assertEquals(len(Tip.objects.all()), 1)
        self.assertTrue("shizzle" in Statement.objects.all()[0].body)
        self.assertTrue(mock_process_tip.called)

    @patch('sms.tasks.process_tip.apply_async')
    def test_second_statement(self, mock_process_tip):
        self.client.sms("I found some shady shizzle.",
                        path="/sms/tip/statement/")
        response = self.client.sms("I found more shady shizzle.",
                                   path="/sms/tip/statement/")

        self.assert_twiml(response)
        self.assertContains(response, "<Response />")
        self.assertEquals(len(Tip.objects.all()), 1)
        self.assertEquals(len(Statement.objects.all()), 2)
        self.assertEquals(Statement.objects.all()[1].related_tip,
                          Tip.objects.all()[0])
        self.assertTrue(mock_process_tip.called)

    @patch('sms.tasks.process_tip.apply_async')
    def test_empty_statement(self, mock_process_tip):
        response = self.client.sms("",
                                   path="/sms/tip/statement/")

        self.assert_twiml(response)
        self.assertEquals(len(Tip.objects.all()), 1)
        self.assertFalse(Statement.objects.all())
        self.assertTrue(mock_process_tip.called)

    @patch('sms.tasks.process_tip.apply_async')
    def test_photo(self, mock_process_tip):
        response = self.client.sms("Photos of shady shizzle.",
                                   path="/sms/tip/photo/",
                                   extra_params={"NumMedia": "1",
                                                 "MediaUrl0": "https://example"
                                                 ".com/url.jpg"})

        self.assert_twiml(response)
        self.assertContains(response, "photo")
        self.assertEquals(len(Tip.objects.all()), 1)
        self.assertEquals(len(Photo.objects.all()), 1)
        self.assertEquals(Photo.objects.all()[0].related_tip,
                          Tip.objects.all()[0])
        self.assertTrue(mock_process_tip.called)

    @patch('sms.tasks.process_tip.apply_async')
    def test_multiple_photos(self, mock_process_tip):
        response = self.client.sms("",
                                   path="/sms/tip/photo/",
                                   extra_params={"NumMedia": "2",
                                                 "MediaUrl0": "https://example"
                                                 ".com/url.jpg",
                                                 "MediaUrl1": "https://example"
                                                 ".com/url.jpg"})

        self.assert_twiml(response)
        self.assertContains(response, "2 photos")
        self.assertEquals(len(Tip.objects.all()), 1)
        self.assertEquals(len(Photo.objects.all()), 2)
        self.assertEquals(Photo.objects.all()[0].related_tip,
                          Tip.objects.all()[0])
        self.assertEquals(Photo.objects.all()[1].related_tip,
                          Tip.objects.all()[0])
        self.assertTrue(mock_process_tip.called)

    @patch('sms.tasks.process_tip.apply_async')
    def test_photo_no_body(self, mock_process_tip):
        response = self.client.sms("", path="/sms/tip/photo/",
                                   extra_params={"NumMedia": "1",
                                                 "MediaUrl0": "https://example"
                                                 ".com/url.jpg"})

        self.assert_twiml(response)
        self.assertContains(response, "photo")
        self.assertEquals(len(Photo.objects.all()), 1)
        self.assertEquals(len(Statement.objects.all()), 0)
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(len(Tip.objects.all()), 1)

    @patch('sms.tasks.process_tip.apply_async')
    def test_photo_no_media(self, mock_process_tip):
        response = self.client.sms("", path="/sms/tip/photo/")

        self.assert_twiml(response)
        self.assertContains(response, "<Redirect>")
        self.assertContains(response, "/sms/tip/statement/")
        self.assertTrue(mock_process_tip.called)
        self.assertEquals(len(Tip.objects.all()), 1)

    @patch('sms.tasks.process_tip.apply_async')
    def test_photo_tip_exists(self, mock_process_tip):
        self.client.sms("I saw shady shizzle.", path="/sms/tip/statement/")
        response = self.client.sms("", path="/sms/tip/photo/",
                                   extra_params={"NumMedia": "1",
                                                 "MediaUrl0": "https://example"
                                                 ".com/url.jpg"})

        self.assert_twiml(response)
        self.assertContains(response, "photo")
        self.assertEquals(len(Tip.objects.all()), 1)

        photo = Photo.objects.all()[0]
        self.assertEquals(str(photo),
                          "Photo submitted {0} by "
                          "Shrimply Pibbles".format(photo.date_created))
        self.assertEquals(len(Tip.objects.all()), 1)
        self.assertTrue(mock_process_tip.called_once)

    def test_statement_representation(self):
        reporter = Reporter.objects.all()[0]
        tip = Tip.objects.create(related_reporter=reporter)
        statement = Statement.objects.create(related_tip=tip,
                                             body="Test.")
        self.assertEquals(str(statement),
                          "Statement submitted {0} by "
                          "Shrimply Pibbles".format(statement.date_created))


class TestKeywords(HumanTraffickingTipsSmsTestCase):
    def setUp(self):
        Reporter.objects.create(name="Shrimply Pibbles",
                                phone_number="+15556667777",
                                completed_enroll=True,
                                tax_id="12345")
        self.client = HumanTraffickingTipsSmsTestClient()

    def test_help_routing(self):
        response = self.client.sms("Help")

        self.assert_twiml(response)
        self.assertContains(response, "/sms/help/")
        self.assertEquals(0, len(Tip.objects.all()))

    def test_help(self):
        response = self.client.sms("Help", path="/sms/help/")

        self.assert_twiml(response)
        self.assertContains(response, "Text INFO")
        self.assertEquals(0, len(Tip.objects.all()))

    def test_info_routing(self):
        response = self.client.sms("Info")

        self.assert_twiml(response)
        self.assertContains(response, "/sms/info/")
        self.assertEquals(0, len(Tip.objects.all()))

    def test_info(self):
        response = self.client.sms("Info", path="/sms/info/")

        self.assert_twiml(response)
        self.assertContains(response, "BEFREE")
        self.assertEquals(0, len(Tip.objects.all()))
