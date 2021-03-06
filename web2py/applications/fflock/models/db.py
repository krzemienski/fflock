# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

import sys
import os
import datetime
sys.path.append(os.path.abspath('./../'))
from modules import fflock_globals
from modules import fflock_utility

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    #db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])

    sqlconn_string = "mysql://" + fflock_globals.DATABASE_USER + ":" + fflock_globals.DATABASE_PASSWD + "@"\
                     + fflock_globals.DATABASE_HOST + ":" + str(fflock_globals.DATABASE_PORT) + "/"\
                     + fflock_globals.DATABASE_NAME
    db = DAL(sqlconn_string)
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

db.define_table(
    'Servers',
    Field('UUID', 'string'),
    Field('ServerType', 'string'),
    Field('State', 'integer'),
    Field('LocalIP', 'string'),
    Field('PublicIP', 'string'),
    Field('LastSeen', 'datetime'),
    migrate=False
)

db.define_table(
    'Storage',
    Field('UUID', 'string'),
    Field('ServerUUID', 'string'),
    Field('StorageType', 'string'),
    Field('LocalPathNFS', 'string'),
    Field('PublicPathNFS', 'string'),
    migrate=False
)

db.define_table(
    'Connectivity',
    Field('SlaveServerUUID', 'string'),
    Field('StorageUUID', 'string'),
    Field('Latency', 'integer'),
    Field('IPType', 'string'),
    Field('Connected', 'integer'),
    migrate=False
)

db.define_table(
    'Jobs',
    Field('JobType', 'string'),
    Field('JobSubType', 'string'),
    Field('Command', 'string'),
    Field('CommandPreOptions', 'string'),
    Field('CommandOptions', 'string'),
    Field('JobInput', 'string'),
    Field('JobOutput', 'string'),
    Field('Assigned', 'integer'),
    Field('State', 'integer'),
    Field('Progress', 'integer'),
    Field('Priority', 'integer'),
    Field('ResultValue1', 'string'),
    Field('ResultValue2', 'string'),
    Field('Dependencies', 'string'),
    Field('UUID', 'string'),
    Field('AssignedServerUUID', 'string'),
    Field('StorageUUID', 'string'),
    Field('MasterUUID', 'string'),
    Field('AssignedTime', 'datetime'),
    Field('CreatedTime', 'datetime'),
    Field('FinishedTime', 'datetime'),
    migrate=False
)


# determine upload location from fflock database
now = datetime.datetime.now()
serveruuid = ""
nfsmountpath = ""
tempdb = fflock_utility.dbconnect()
cursor = tempdb.cursor()
storagecursor = tempdb.cursor()
storagecursor.execute("SELECT ServerType, UUID FROM Servers WHERE ServerType = '%s'" % "Storage")
storageresults = storagecursor.fetchall()
for storagerow in storageresults:
    serveruuid = storagerow[1]

storageuuids = []
__db = fflock_utility.dbconnect()
cursor.execute("SELECT UUID, ServerUUID FROM Storage WHERE ServerUUID = '%s'" % serveruuid)
results = cursor.fetchall()
for row in results:
    storageuuids.append(row[0])
__db.close()

for storageuuid in storageuuids:
    __db = fflock_utility.dbconnect()
    cursor2 = __db.cursor()
    cursor2.execute("SELECT LocalPathNFS, PublicPathNFS FROM Storage WHERE UUID = '%s'" % storageuuid)
    result2 = cursor2.fetchone()
    nfsmountpath = result2[0].split(':', 1)[-1]
    __db.close()

upload_location = nfsmountpath



db.define_table(
    'files',
    Field('title', "string", unique=False),
    Field('file', 'upload', uploadfolder=upload_location, autodelete=True),
    Field('datecreated', 'datetime', default=now, readable=False),
    migrate=False
)



db.files.title.requires = IS_NOT_EMPTY()


## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)

mail.settings.server = settings.email_server
mail.settings.sender = settings.email_sender
mail.settings.login = settings.email_login
