'''
Created on Nov 10, 2013

@author: patrick
'''
import csv
import logging

from django.contrib.admin.sites import site
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, InvalidPage
from django.db import connection
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import render


logger = logging.getLogger(__name__)

@permission_required('is_superuser')
def sqlmanager(request):
    query = ""
    page = None
    count = None
    count_profiles = None
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    # get users as per partial query
    query = request.GET.get('query', "")
    action = request.GET.get('action', "")
    desc = []
    rows = []
    count = None
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        desc = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        count = len(rows)
    except BaseException as e:
        return render(request, "rmanage/sqlmanager.html", { 'error' : "%s" % e, 'query' : query, 'header' : desc })
    # on GET just show users
    if action == "search":
        # paginate result
        paginator = Paginator(rows, 50)
        try:
            page = paginator.page(int(request.GET.get('page', 1)))
        except InvalidPage:
            raise Http404("No such page of results!")
    # get the CSV
    if action == "getcsv":
        # create a CSV file to download
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="list.csv"'
        writer = csv.writer(response)
        writer.writerow(desc)
        for row in rows:
            writer.writerow(row)
        return response
    return render(request, "rmanage/sqlmanager.html", { 'page' : page, 'query' : query, 'count' : count, 'header' : desc, 'count_profiles' : count_profiles})    
        
