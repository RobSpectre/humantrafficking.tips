from django.conf.urls import url
from sms import views


app_name = 'sms'
urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^enroll/$', views.enroll, name="enroll"),
    url(r'^enroll/name/$', views.enroll_name,
        name="enroll-name"),
    url(r'^enroll/tax_id/$', views.enroll_tax_id,
        name="enroll-taxid"),
    url(r'^help/$', views.help, name="help"),
    url(r'^info/$', views.info, name="info"),
    url(r'^tip/$', views.tip, name="tip"),
    url(r'^tip/statement/$', views.tip_statement,
        name="tip-statement"),
    url(r'^tip/photo/$', views.tip_photo,
        name="tip-photo"),
]
