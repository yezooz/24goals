import os

import apachelog
import sys
from time import *


# django settings
sys.path.append(os.path.dirname(__file__) + "../../")
os.environ["DJANGO_SETTINGS_MODULE"] = 'myscore.settings_production'

# Format copied and pasted from Apache conf - use raw string + single quotes
# {
#    '%>s': '200',
#    '%b': '2607',
#    '%h': '212.74.15.68',
#    '%l': '-',
#    '%r': 'GET /images/previous.png HTTP/1.1',
#    '%t': '[23/Jan/2004:11:36:20 +0000]',
#    '%u': '-',
#    '%{Referer}i': 'http://peterhi.dyndns.org/bandwidth/index.html',
#    '%{User-Agent}i': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.2) Gecko/20021202'
#    }

INTERNAL_IPS = (
'192.168.0.107', '217.153.221.57', '195.95.170.13', '217.20.127.170', '153.19.183.4', '85.128.90.27', '66.249.66.175')
p = apachelog.parser(apachelog.formats['extended'])

from django.db import connection

cursor = connection.cursor()

for line in open('/var/log/apache2/access.log'):
    # try:

    data = p.parse(line)
    date = strptime(data['%t'][1:21], "%d/%b/%Y:%H:%M:%S")

    if data['%h'] not in INTERNAL_IPS and data['%r'].find('/static/') == -1:
        sql = "INSERT IGNORE INTO logs_apache VALUES('', '%s', '%s', '%s', '%s', '%s', '%s')" % (
        data['%h'], data['%{Referer}i'], data['%r'], data['%>s'], "", strftime("%Y-%m-%d %H:%M:%S", date))
        cursor.execute(sql)
