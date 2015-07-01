import os

import sys

# django settings
sys.path.append(os.path.dirname(__file__) + "../../")
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_pl'

from myscore.main.models import *
# from django.shortcuts import render_to_response
# from django.http import HttpResponseRedirect, HttpResponse

# SCRIPT HERE
