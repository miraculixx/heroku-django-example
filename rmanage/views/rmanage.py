import os
import sys
import traceback

from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

class Capture(object):
    def __init__(self, name="capture.log"):
        self.log_name=name
        self.open_log()
            
    def open_log(self):
        try:
            self.log = open(os.path.join(settings.TMP_FOLDER, self.log_name), 'w')
            self.stdout = sys.stdout
            self.stderr = sys.stderr
            sys.stdout = self.log
            sys.stderr = self.log
        except:
            raise
        
    def close_log(self): 
        try:
            sys.stdout = self.stdout
            sys.stderr = self.stderr
            self.log.close()
        except:
            raise
        
    def get_log(self):
        try:
            self.close_log()
            self.log = open(os.path.join(settings.TMP_FOLDER, self.log_name), 'r')
            log = self.log.read()
            if log:
                out1 = log
            else:
                out1 = ""
        except Exception as e:
            out1 = "Capture.get_log: %s" % e
        return out1
        
    def show_log(self):
        response = HttpResponse(content_type="text/plain")
        try:
            response.write(self.get_log())
            return response
        except Exception as e:
            response.content("Capture.show_log: %s" % e)
            raise e

def dump(request):
    if not request.user.is_superuser:
        raise
    logfile = request.GET.get('log', None)
    if logfile:
        response = HttpResponse(content_type="text/plain")
        try:
            logf = open(logfile, 'r')
            out1 = logf.read()
            response.write(out1)
            logf.close()
            return response
        except Exception as e:
            response.write("Capture.show_log: %s" % e)
            raise e


def test_reset(request):
    if not request.user.is_superuser:
        raise
    capture = Capture('test_reset.log')
    try:
        # sync db
        exec_cmd('syncdb')
        # get latest migration states
        migrations = get_latest_migrations()
        # flush db
        print "Flushing DB"
        exec_cmd('flush', '--noinput')
        print "Running migrations"
        # reapply previous migrations, and newest
        for app, mid in migrations.iteritems():
            exec_cmd('migrate', '--fake', app, mid)
            exec_cmd('migrate', app)
        # setup admin user
        print "Setup user"
        setupadmin(request)
        # import fixtures
        print "Setup fixtures"
        load_fixture('subsite.json')
        load_fixture('category.json')
        load_fixture('idea.json')
        load_fixture('flatpage_i18n.json')
    except:
        traceback.print_exc()
    return capture.show_log()
        
def load_fixture(fixture):
    print "-- loading %s" % fixture
    exec_cmd('loaddata', 'fixtures/%s' % fixture)
        
def get_latest_migrations():
    """
    using South' MigrationHistory, get the latest migration id per app
    using this, we can apply a --fake later on to get back the previous
    state
    """
    from south.models import MigrationHistory
    from django.db.models.aggregates import Max
    latest = MigrationHistory.objects.values('app_name').annotate(latest=Max('applied'))
    migrations = {}
    for l in latest:
        m = MigrationHistory.objects.filter(app_name=l['app_name']).filter(applied=l['latest'])
        mid = m[0].migration.split('_')[0]
        migrations[l['app_name']] = mid
    return migrations
    
def reindex(request):
    if not request.user.is_superuser:
        raise
    os.environ.setdefault('ES_RECREATE_INDEX', 'YES')
    capture = Capture('reindex.log')
    #exec_cmd('rebuild_index', noinput=True)
    argv = [sys.argv[0], 'rebuild_index', '--noinput']
    exec_cmd_line(argv)
    os.environ['ES_RECREATE_INDEX'] = 'NO'
    return capture.show_log()

@csrf_exempt
def rmanage(request):
    if not request.user.is_superuser:
        raise
    command = ""
    log = "no log"
    if request.method == 'POST':
        command = request.POST.get('command', '')
    if request.method == 'GET':
        command = request.GET.get('command', '')
    if not command == "":
        capture = Capture('rmanage.log')
        if command == "settings":
            from django.conf import settings
            for s in dir(settings):
                print make_secure(s, getattr(settings, s))
        elif command == "env":
            keys = os.environ.keys()
            keys.sort()
            for s in keys:
                print make_secure(s, os.environ[s])
        elif command == "request":
            for s in dir(request):
                print make_secure(s, getattr(request, s))
        elif command == "modules":
            keys = sys.modules.keys()
            keys.sort()
            for s in keys:
                print make_secure(s, sys.modules[s])
        elif command == "request.session":
            keys = request.session.keys()
            keys.sort()
            for s in keys:
                print make_secure(s, request.session[s])
        elif command == "request.META":
            keys = request.META.keys()
            keys.sort()
            for s in keys:
                print make_secure(s, request.META[s])
        else:
            commands = command.split()
            exec_cmd(*commands)
        log = capture.get_log()
    return render(request, 'rmanage/console.html', { 'command' : command, 'log' : log})

def repl(request):
    if not request.user.is_superuser:
        raise
    statement = ""
    log = "no log"
    if request.method == 'POST':
        statement = request.POST.get('statement', '')
        capture = Capture('repl.log')
        try:
            f = open('repl.py.tmp', 'w')
            f.write(statement)
            f.close()
            execfile('repl.py.tmp', {}, {})
        except:
            print traceback.print_exc()
        log = capture.get_log()
    return render(request, 'rmanage/repl.html', { 'statement' : statement, 'log' : log})
 

def make_secure(key,value):
    value = "%s=%s" % (key, value)
    if "secret" in value.lower():
        value = "%s=********" % key
        if "password" in value.lower():
            value = "%s=********" % key
        if "pass" in value.lower():
            value = "%s=********" % key
        if "key" in value.lower():
            value = "%s=********" % key
    return value

def migrate(request, version):
    if not request.user.is_superuser:
        raise
    capture = Capture('migrate.log')
    # usual syncdb
    exec_cmd('syncdb')
    # migrate applications explicetely
    # rationale: sometimes not all apps are migrated
    exec_cmd('migrate', 'reversion')
    exec_cmd('migrate', 'djcelery')
    exec_cmd('migrate', 'djangoratings')
    exec_cmd('migrate', 'shrui')
    exec_cmd('migrate', 'shrres')
    exec_cmd('migrate', 'tastypie')
    exec_cmd('migrate', 'django_extensions')
    exec_cmd('migrate')
    # load fixtures
    exec_cmd('loaddata', 'fixtures/category.json')
    return capture.show_log()
    
def setupadmin(request):
    from django.contrib.sites.models import Site
    default_username = 'admin'
    if settings.DEBUG:
        default_pass = "test"
    else:
        default_pass = 'e1fens1ndsch0en'
    default_email = 'info@shrebo.ch'
    # set the site name (for disqus)
    # see http://django-disqus.readthedocs.org/en/latest/installation.html
    #s = Site.objects.all()[0]
    #s.domain = 'shrebo.ch'
    #s.name = 'shrebo.com'
    #s.save()
    # create the admin account
    error = ""
    if authenticate(username=default_username, password=default_pass) is not None:
        # attempt to fix missing profile
        try:
            user = User.objects.get(username=default_username)
        except:
            capture = Capture('adminx.log')
            traceback.print_exc()
            error = capture.get_log()
        return HttpResponse("NOK %s" % error)
    try:
        # we create a profile so that this user can invite others
        # because invitation is currently tied to the ShreboProfile
        user = User.objects.create_user(default_username, email=default_email, password=default_pass)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.language="de"
        user.save()
        error = ""
        return HttpResponse("OK %s" % error)
    except:
        capture = Capture('adminx.log')
        traceback.print_exc()
        error = capture.get_log()
        return HttpResponse("Something went wrong: %s" % error)

def exec_cmd(*args, **kwargs):
    argv=[]
    argv.append(sys.argv[0])
    for arg in args:
        argv.append(arg)
    # for every keyword argument add the keyword
    # and its value
    for arg in kwargs:
        argv.append(arg)
        argv.append(kwargs[arg])
    exec_cmd_line(argv)
    
def exec_cmd_old(*args, **kwargs):
    from django.core import management
    with open(os.path.join(settings.TMP_FOLDER, 'manage.log'), 'w') as f:
        stdout = sys.stdout
        sys.stdout = f
        try:
            print "%s" % settings.HAYSTACK_CONNECTIONS
            management.call_command(*args, stdout=f, interactive=False, **kwargs) 
        except Exception as e:
            print e
        finally:
            f.close()
            sys.stdout = stdout
        
def exec_cmd_line(argv=None):
    from django.core import management
    try:
        #print "\nexec_cmd_line input: %s" % argv
        #print "%s" % settings.HAYSTACK_CONNECTIONS
        management.execute_from_command_line(argv) 
    except:
        print "exec_cmd_line using %s gave:" % (argv)
        traceback.print_exc()
        
def view_template(request, path=None):
    return render(request, path, request.GET)         


