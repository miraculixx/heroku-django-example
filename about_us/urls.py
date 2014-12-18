from django.conf.urls import patterns, url


urlpatterns = patterns('about_us.views',
    url(r'^$', 'home', name='home'),
    url(r'^check\-person/(?P<person_id>\d+)/$', 'check_person'),
)