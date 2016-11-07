from django.test import TestCase
from django.test import Client

from sms.models import Reporter


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
            params = dict(params + extra_params.items())

        return self.post(path, params)


class HumanTraffickingTipsSmsTestCase(TestCase):
    def setUp(self):
        self.client = HumanTraffickingTipsSmsTestClient()

    def assert_twiml(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "</Response>")


class TestEnrollNoReporter(HumanTraffickingTipsSmsTestCase):
    def test_enroll_when_reporter_not_found(self):
        response = self.client.sms("Test.")

        self.assert_twiml(response)
        self.assertContains(response, "Redirect")
        self.assertContains(response, "/enroll/")

    def test_enroll_ask_for_name(self):
        response = self.client.sms("Test.", path="/sms/enroll/")

        self.assert_twiml(response)
        self.assertEquals(1, len(Reporter.objects.all()))
        self.assertTrue(Reporter.objects.all()[0].phone_number,
                        "+15556667777")
        self.assertContains(response, "what's your name")
        self.assertEquals(self.client.cookies['enroll_step'].value,
                          "/sms/enroll/name/")

    def test_enroll_ask_for_taxid(self):
        self.client.sms("Test.", path="/sms/enroll/")
        response = self.client.sms("Shrimply Pibbles",
                                   path="/sms/enroll/name/")

        self.assert_twiml(response)
        self.assertContains(response, "Shrimply Pibbles")
        self.assertEquals(Reporter.objects.all()[0].name,
                          "Shrimply Pibbles")
        self.assertEquals(self.client.cookies['enroll_step'].value,
                          "/sms/enroll/tax_id/")

    def test_enroll_complete(self):
        self.client.sms("Test.", path="/sms/enroll/")
        self.client.sms("Shrimply Pibbles",
                        path="/sms/enroll/name/")
        response = self.client.sms("12345",
                                   path="/sms/enroll/tax_id/")

        self.assert_twiml(response)
        self.assertContains(response, "Shrimply Pibbles")
        self.assertContains(response, "12345")
        self.assertEquals(Reporter.objects.all()[0].tax_id, "12345")
        self.assertTrue(Reporter.objects.all()[0].completed_enroll)
        self.assertEquals(self.client.cookies['enroll_step'].value, '')


class TestEnrollReportExists(HumanTraffickingTipsSmsTestCase):
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
