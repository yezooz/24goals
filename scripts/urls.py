from django.conf.urls.defaults import *

urlpatterns = patterns('myscore.scripts',
                       (r'^populate_activities/$', 'views.populate_acitivities.index'),
                       )
