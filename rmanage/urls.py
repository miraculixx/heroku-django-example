from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from south.management.commands import migrate

from rmanage.views.rmanage import repl, setupadmin, dump, reindex, rmanage
from rmanage.views.sqlmgr import sqlmanager


urlpatterns = patterns('rmanage',
    # Enable DB sync and migration
    url(r'^migrate/(?P<version>\d?)', login_required(migrate), name='admin_migrate'),
    # Enable remote python console
    url(r'^repl/', login_required(repl), name='admin_repl'),
    # Enable remote sql execute
    url(r'^rsql/', login_required(sqlmanager), name='admin_rsql'),
    # Enable initial user creating
    url(r'^setup/', setupadmin, name='admin_setup'),
    # enable log dumping
    url(r'^dump/', login_required(dump), name='admin_dump'),
    # Enable reindexing of Whoosh
    url(r'^reindex/', login_required(reindex), name='admin_reindex'),
    # Enable remote manage via web
    url(r'^/?', login_required(rmanage), name='admin_rmanage'),
)