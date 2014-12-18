from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^about\-us/', include('about_us.urls')),
    url(r'^rmanage/', include('rmanage.urls')),
    url(r'^$', 'about_us.views.home', name='home'),
)

urlpatterns += patterns('',
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout'), 
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', 
        {'template_name': 'admin/login.html'}), 
)


if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^assets/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )