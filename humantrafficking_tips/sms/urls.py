from django.conf.urls import url
from sms import views


app_name = 'sms'
urlpatterns = [
    url(r'^$', views.index, name="index"),
    url(r'^enroll/$', views.enroll, name="enroll"),
    url(r'^enroll/first_name/$', views.enroll_first_name,
        name="enroll-firstname"),
    url(r'^enroll/last_name/$', views.enroll_last_name,
        name="enroll-lastname"),
    url(r'^enroll/tax_id/$', views.enroll_tax_id,
        name="enroll-taxid"),
    url(r'^enroll/confirm/$', views.enroll_confirm,
        name="enroll-confirm"),
    url(r'^start/$', views.start,
        name="start"),
    url(r'^start/handler/$', views.start_handler,
        name="start-handler"),
    url(r'^help/$', views.start,
        name="help"),
    url(r'^tip/$', views.tip_start,
        name="tip-start"),
    url(r'^tip/statement/(?P<tip>[0-9]+)$', views.tip_statement,
        name="tip-statement"),
    url(r'^tip/location/(?P<tip>[0-9]+)$', views.tip_location,
        name="tip-location"),
    url(r'^tip/photo/(?P<tip>[0-9]+)$', views.tip_photo,
        name="tip-photo"),
    url(r'^tip/confirm/(?P<tip>[0-9]+)$', views.tip_confirm,
        name="tip-confirm"),
]
