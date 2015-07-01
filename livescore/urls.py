from django.conf.urls.defaults import *

urlpatterns = patterns('myscore.livescore.views',

                       # (r'^matches/', include('myscore.main.urls')),
                       # (r'^news/', include('myscore.main.urls')),
                       # (r'^messages/', include('myscore.main.urls')),
                       (r'^ls/index$', 'index')

                       )
