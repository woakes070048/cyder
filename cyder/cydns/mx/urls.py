from django.conf.urls.defaults import *

from cyder.cydns.views import cydns_record_view, table_update


urlpatterns = patterns('',
   url(r'^$', cydns_record_view, name='mx'),
   url(r'(?P<pk>[\w-]+)/tableupdate/$', table_update,
       name='mx-table-update'),
)