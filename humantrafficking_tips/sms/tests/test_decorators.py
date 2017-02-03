from .test_sms import HumanTraffickingTipsSmsTestCase


class HumanTraffickingTipsDecoratorsTestCase(HumanTraffickingTipsSmsTestCase):
    def test_not_get_or_post(self):
        response = self.client.delete("/sms/")

        self.assertEquals(response.status_code, 405)

    def test_wrong_twilio_signature_post(self):
        response = self.client.post("/sms/", params={"body": "foo"},
                                    HTTP_X_TWILIO_SIGNATURE="Xxx")
        self.assertEquals(response.status_code, 403)

    def test_wrong_twilio_signature_get(self):
        response = self.client.get("/sms/?body=foo",
                                   HTTP_X_TWILIO_SIGNATURE="Xxx")
        self.assertEquals(response.status_code, 403)
