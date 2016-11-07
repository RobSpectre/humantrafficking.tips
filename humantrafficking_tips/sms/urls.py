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
    url(r'^help/$', views.start,
        name="help"),
    url(r'^info/$', views.info,
        name="info"),
    url(r'^tip/$', views.tip_start,
        name="tip"),
    url(r'^tip/statement/(?P<tip>[0-9]+)$', views.tip_statement,
        name="tip-statement"),
    url(r'^tip/location/(?P<tip>[0-9]+)$', views.tip_location,
        name="tip-location"),
    url(r'^tip/photo/(?P<tip>[0-9]+)$', views.tip_photo,
        name="tip-photo"),
    url(r'^tip/confirm/(?P<tip>[0-9]+)$', views.tip_confirm,
        name="tip-confirm"),
]
