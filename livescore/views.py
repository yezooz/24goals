from myscore.main.models import *
# from lxml.etree import Element, ElementTree, SubElement, parse, tostring
from django.http import HttpResponse


def index(request):
    return HttpResponse("index")
