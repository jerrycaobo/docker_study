from org.codehaus.jackson.map import ObjectMapper
from java.util import HashMap
from java.io import File
import os
import shutil

def startCreate():
 try:
  mapconfig = loadConfig()
  
  # Open a domain template
  readTemplate(os.environ.get('ORACLE_HOME')+'/common/templates/wls/wls.jar')
  setOption('OverwriteDomain', 'true')
  setOption('ServerStartMode', 'prod')
  setOption('JavaHome',mapconfig.get('java_home'))
  cmo.setConsoleEnabled(java.lang.Boolean.parseBoolean(mapconfig.get('console_enabled')))
  domain_name = os.environ.get('DOMAIN_HOME').split('/')[-1]
  if domain_name == '':
   domain_name = os.environ.get('DOMAIN_HOME').split('/')[-2]
  cd('/')
  create(domain_name,'AdminConsole')
  cd('/AdminConsole/'+domain_name)
  set('CookieName',domain_name+'_ADMINCONSOLESESSION')
  cd('/')
  create(domain_name,'JMX')
  cd('/JMX/'+domain_name)
  set('InvocationTimeoutSeconds',int(mapconfig.get('jmx_invocationtimeoutsec')))
  
  # Define admin user and password
  cd('/Security/base_domain/User/weblogic')
  cmo.setName(mapconfig.get('server').get('admin_username'))
  cmo.setUserPassword(mapconfig.get('server').get('admin_password'))
  
  # Create other user and password
  for user in mapconfig.get('users'):
   cd('/Security/base_domain/User')
   create(user.get('user_name'),'User')
   cd(user.get('user_name'))
   cmo.setUserPassword(user.get('user_password'))
   cmo.setGroupMemberOf(user.get('user_group'))
  
  # Configure admin server
  cd('/Server/AdminServer')
  cmo.setName(mapconfig.get('server').get('server_name'))
  cmo.setListenPort(int(os.environ.get('SERVER_PORT', '7001')))
  cmo.setListenAddress(mapconfig.get('server').get('listen_address'))
  cmo.setAcceptBacklog(int(mapconfig.get('server').get('accept_backlog')))
  cmo.setGracefulShutdownTimeout(int(mapconfig.get('server').get('gracefulshutdown_timeout')))
  create(mapconfig.get('server').get('server_name'),'Log')
  cd('/Servers/'+mapconfig.get('server').get('server_name')+'/Log/'+mapconfig.get('server').get('server_name'))
  cmo.setFileCount(int(mapconfig.get('server').get('log_config').get('serverlog').get('file_count')))
  cmo.setFileMinSize(int(mapconfig.get('server').get('log_config').get('serverlog').get('file_size')))
  cmo.setFileName('../../logs/'+mapconfig.get('server').get('server_name')+'.log')
  cd('/Server/'+mapconfig.get('server').get('server_name'))
  create(mapconfig.get('server').get('server_name'),'WebServer')
  cd('/Servers/'+mapconfig.get('server').get('server_name')+'/WebServer/'+mapconfig.get('server').get('server_name'))
  create(mapconfig.get('server').get('server_name'),'WebServerLog')
  cd('/Servers/'+mapconfig.get('server').get('server_name')+'/WebServer/'+mapconfig.get('server').get('server_name')+'/WebServerLog/'+mapconfig.get('server').get('server_name'))
  cmo.setFileName('../../logs/access.log')
  cmo.setLoggingEnabled(java.lang.Boolean.parseBoolean(mapconfig.get('server').get('log_config').get('accesslog').get('enabled')))  

 
  # Create JDBC
  for jdbc in mapconfig.get('jdbcs'):
   cd('/')
   create(jdbc.get('jdbc_name'), 'JDBCSystemResource')
   cd('JDBCSystemResource/'+jdbc.get('jdbc_name')+'/JdbcResource/'+jdbc.get('jdbc_name'))
   create(jdbc.get('jdbc_name'),'JDBCDriverParams')
   cd('JDBCDriverParams/NO_NAME_0')
   set('DriverName',jdbc.get('jdbc_driver'))
   set('URL',jdbc.get('jdbc_url'))
   set('PasswordEncrypted',jdbc.get('jdbc_password'))
   set('UseXADataSourceInterface', 'false')
   create(jdbc.get('jdbc_name'),'Properties')
   cd('Properties/NO_NAME_0')
   create('user','Property')
   cd('Property/user')
   cmo.setValue(jdbc.get('jdbc_user'))
   cd('/JDBCSystemResource/'+jdbc.get('jdbc_name')+'/JdbcResource/'+jdbc.get('jdbc_name'))
   create(jdbc.get('jdbc_name'),'JDBCDataSourceParams')
   cd('JDBCDataSourceParams/NO_NAME_0')
   set('JNDIName', java.lang.String(jdbc.get('jdbc_jndi')))
   cd('/JDBCSystemResource/'+jdbc.get('jdbc_name')+'/JdbcResource/'+jdbc.get('jdbc_name'))
   create(jdbc.get('jdbc_name'),'JDBCConnectionPoolParams')
   cd('JDBCConnectionPoolParams/NO_NAME_0')
   cmo.setTestConnectionsOnReserve(java.lang.Boolean.parseBoolean(jdbc.get('jdbc_testconnonreserve')))
   set('TestTableName',jdbc.get('jdbc_testsql'))
   set('ConnectionReserveTimeoutSeconds', 120)
   set('InitialCapacity',int(jdbc.get('jdbc_initcapacity')))
   set('MinCapacity',int(jdbc.get('jdbc_mincapacity')))
   set('MaxCapacity',int(jdbc.get('jdbc_maxcapacity')))
   set('StatementCacheSize',int(jdbc.get('jdbc_statementcachesize')))
   set('InactiveConnectionTimeoutSeconds',int(jdbc.get('jdbc_inactivetimeoutsec')))
   
   # Target JDBC
   cd('/')
   assign('JDBCSystemResource',jdbc.get('jdbc_name'),'Target',mapconfig.get('server').get('server_name'))

  # Deploy application
  for app in mapconfig.get('applications'):
   cd('/')
   create(app.get('app_name'),'AppDeployment')
   cd('AppDeployment')
   cd(app.get('app_name'))
   set('ModuleType','war')
   set('Name',app.get('app_name'))
   set('SecurityDdModel','DDOnly')
   set('SourcePath',app.get('app_path'))
   
   # Target app
   set('Target',mapconfig.get('server').get('server_name'))
   
  # Save domain
  writeDomain(os.environ.get('DOMAIN_HOME'))
  closeTemplate()
  
  # Generate boot.properties
  if not os.path.exists(os.environ.get('DOMAIN_HOME')+'/servers/'+mapconfig.get('server').get('server_name')+'/security'):
   os.makedirs(os.environ.get('DOMAIN_HOME')+'/servers/'+mapconfig.get('server').get('server_name')+'/security')
  fp = open(os.environ.get('DOMAIN_HOME')+'/servers/'+mapconfig.get('server').get('server_name')+'/security/boot.properties','wb')
  fp.write('username='+mapconfig.get('server').get('admin_username')+'\n')
  fp.write('password='+mapconfig.get('server').get('admin_password')+'\n')
  fp.flush()
  fp.close()
  fp = None
  
  # Generate logging.properties
  if not os.path.exists(os.environ.get('DOMAIN_HOME')+'/lib'):
   os.makedirs(os.environ.get('DOMAIN_HOME')+'/lib')
  fp = open(os.environ.get('DOMAIN_HOME')+'/lib/logging.properties','wb')
  fp.write('handlers = weblogic.logging.ServerLoggingHandler\n')
  fp.write('weblogic.logging.ServerLoggingHandler.level = OFF\n')
  fp.flush()
  fp.close()
  fp = None
   
  # Modify startWebLogic.sh
  shutil.copy(os.environ.get('DOMAIN_HOME')+'/bin/startWebLogic.sh',os.environ.get('DOMAIN_HOME')+'/bin/startWebLogic.sh_bak')
  fp_r = open(os.environ.get('DOMAIN_HOME')+'/bin/startWebLogic.sh','rb')
  lines = fp_r.readlines()
  fp_r.close()
  fp_r = None
   
  content = '''if [ "X${SERVER_NAME}" = "X" ] ; then
  SERVER_NAME="'''+mapconfig.get('server').get('server_name')+'''"
fi
CURRENTUSER=`whoami`
if [ "$CURRENTUSER" = "root" ] ; then 
   echo "Don't use root to start weblogic!!!"
   exit 0
fi
umask 022'''
   
  content = content+'\n\nLOG_PATH="'+mapconfig.get('server').get('log_path')+'"\nDUMP_PATH="'+mapconfig.get('server').get('dump_path')+'"\nUSER_MEM_ARGS="'+mapconfig.get('server').get('mem_args')+ \
'"\nJMX_OPTIONS="'+mapconfig.get('server').get('jmx_args')+'"\nLOG_OPTIONS="'+mapconfig.get('server').get('log_args')+'"\nGC_OPTIONS="'+ \
mapconfig.get('server').get('gc_args')+'"\nAPP_OPTIONS="'+mapconfig.get('server').get('app_args')+'"\n\nJAVA_OPTIONS=" -d64  $JMX_OPTIONS $LOG_OPTIONS $GC_OPTIONS $APP_OPTIONS '+ \
mapconfig.get('server').get('other_args')+'"\n\n. ${DOMAIN_HOME}/bin/setDomainEnv.sh $*'

  if "$" in mapconfig.get('server').get('log_path'):
   #if "false" in os.environ.get('LOGS2VOL'):
   # #if not os.path.exists(os.environ.get('DOMAIN_HOME')+'/logs'):
   #  #os.makedirs('/weblogic/logs')
   #  os.makedirs(mapconfig.get('server').get('log_path'))
   #  os.makedirs(mapconfig.get('server').get('dump_path'))
   #  print "use local dir and softlink "  
   #else:
   # 
   # #use volumn and softlink, need not create logs
   # print "use volume and softlink."
   print "log path defined." 
  else:
  # if not os.path.exists(mapconfig.get('server').get('log_path')):
  #  os.makedirs(mapconfig.get('server').get('log_path'))
  #  os.makedirs(mapconfig.get('server').get('dump_path'))
   print "please define log path."  
    
  fp_w = open(os.environ.get('DOMAIN_HOME')+'/bin/startWebLogic.sh','wb')
  for line in lines:
   if "umask 027" in line:
    line = line.replace("umask 027","#umask 027")
   if ". ${DOMAIN_HOME}/bin/setDomainEnv.sh $*" in line:
    line = line.replace(". ${DOMAIN_HOME}/bin/setDomainEnv.sh $*",content)
   fp_w.write(line)
  fp_w.flush()
  fp_w.close()
  fp_w = None

  # Modify stopWebLogic.sh
  shutil.copy(os.environ.get('DOMAIN_HOME')+'/bin/stopWebLogic.sh',os.environ.get('DOMAIN_HOME')+'/bin/stopWebLogic.sh_bak')
  fp_r = open(os.environ.get('DOMAIN_HOME')+'/bin/stopWebLogic.sh','rb')
  slines = fp_r.readlines()
  fp_r.close()
  fp_r = None
  
  fp_w = open(os.environ.get('DOMAIN_HOME')+'/bin/stopWebLogic.sh','wb')
  for line in slines:
   if "shutdown('${SERVER_NAME}','Server', ignoreSessions='true')" in line:
    line = line.replace("shutdown('${SERVER_NAME}','Server', ignoreSessions='true')","shutdown('${SERVER_NAME}','Server', ignoreSessions='true',force='true')")
   fp_w.write(line)
  fp_w.flush()
  fp_w.close()
  fp_w = None
   
   # Add jdbc driver jars
  for jdbc in mapconfig.get('jdbcs'):
   if '.db2.' in jdbc.get('jdbc_driver'):
    if not os.path.exists(os.environ.get('DOMAIN_HOME')+'/lib'):
     os.makedirs(os.environ.get('DOMAIN_HOME')+'/lib')
    shutil.copy('/weblogic/db2jcc.jar',os.environ.get('DOMAIN_HOME')+'/lib')
    shutil.copy('/weblogic/db2jcc_license_cu.jar',os.environ.get('DOMAIN_HOME')+'/lib')
    # Modify setDomainEnv.sh
    shutil.copy(os.environ.get('DOMAIN_HOME')+'/bin/setDomainEnv.sh',os.environ.get('DOMAIN_HOME')+'/bin/setDomainEnv.sh_bak')
    fp = open(os.environ.get('DOMAIN_HOME')+'/bin/setDomainEnv.sh','ab')
    fp.write('\nCLASSPATH=${DOMAIN_HOME}/lib/db2jcc.jar:${DOMAIN_HOME}/lib/db2jcc_license_cu.jar:${CLASSPATH}\nexport CLASSPATH\n')
    fp.flush()
    fp.close()
    fp = None
   
  wls_admin_ip = mapconfig.get('server').get('listen_address')
  if wls_admin_ip == "" :
     wls_admin_ip ="localhost"

  # Build WebLogic Server start script
  script = '''#!/bin/sh

# Change jdbc ip or password
# update 20180824, WLS_JDBC=ds1name^ds1url^ds1password;ds2name^ds2url^ds2password...

if [ "${WLS_JDBC}" != "" ]; then
   '''+ os.environ.get('ORACLE_HOME') + '''/common/bin/wlst.sh -skipWLSModuleScanning <<!

from sun.misc import BASE64Decoder
try:
 readDomain(\''''+ os.environ.get('DOMAIN_HOME') + '''\')
 for jdbcstr in os.environ.get('WLS_JDBC').split(';'):
  jdbc = jdbcstr.split('^')
  if jdbc[0] <> '':
   cd('/JDBCSystemResource/'+jdbc[0]+'/JdbcResource/'+jdbc[0]+'/JDBCDriverParams/NO_NAME_0')
   if jdbc[1] <> '':
    set('URL',jdbc[1])
   if jdbc[2] <> '':
    set('PasswordEncrypted',String(BASE64Decoder().decodeBuffer(jdbc[2])))
 updateDomain()
 closeDomain()
except Exception,e:
 print e
 dumpStack()

!
unset WLS_JDBC
fi

'''+ os.environ.get('DOMAIN_HOME') + '''/bin/docker_changePassword.sh >'''+ os.environ.get('DOMAIN_HOME')+'''/logs/changePassword.log 2>&1 &

'''+ os.environ.get('DOMAIN_HOME') + '''/bin/startWebLogic.sh

'''

  script2 = '''#!/bin/bash

cd '''+ os.environ.get('DOMAIN_HOME')+'''
# Change admin user password
# update 20180824

if [ "${WLS_PASSWORD}" != "" ]; then
   echo "\n\n***************************************************************"
   echo "Waiting for WebLogic Admin Server become available......"
   while :
   do
    (echo > /dev/tcp/'''+ wls_admin_ip + '''/'''+ os.environ.get('SERVER_PORT', '7001') + ''') >/dev/null 2>&1
    available=$?
    if [ $available -eq 0 ]; then
     echo "WebLogic Admin Server is now available."
     echo "\n***************************************************************"
     break
    fi
    sleep 1
   done
   
   '''+ os.environ.get('ORACLE_HOME') + '''/common/bin/wlst.sh -skipWLSModuleScanning <<!

from sun.misc import BASE64Decoder
try:
 wls_password = String(BASE64Decoder().decodeBuffer(os.environ.get('WLS_PASSWORD')))
 connect(adminServerName=\''''+mapconfig.get('server').get('server_name')+'''\',url='t3://''' + wls_admin_ip  + ''':''' + os.environ.get('SERVER_PORT', '7001') + '''\')
 cd('/SecurityConfiguration/base_domain/Realms/myrealm/AuthenticationProviders/DefaultAuthenticator')
 cmo.resetUserPassword(\''''+mapconfig.get('server').get('admin_username')+'''\',wls_password)
 f=open(\'''' + os.environ.get('DOMAIN_HOME') + '''/servers/''' + mapconfig.get('server').get('server_name')  + '''/security/boot.properties', 'wb')
 f.write('username='''+mapconfig.get('server').get('admin_username')+'''\\n')
 f.write('password='+encrypt(wls_password,\'''' + os.environ.get('DOMAIN_HOME') + '''\')+'\\n')
 f.close()
 f=None
 disconnect()
except Exception,e:
 print e
 disconnect()
 dumpStack()

!
unset WLS_PASSWORD
fi
echo "\n***************************************************************"
echo "Workdir:" && cd -
echo "***************************************************************"
'''

  fp = open(os.environ.get('DOMAIN_HOME')+'/bin/docker_startWebLogic.sh','wb')
  fp.write(script)
  fp.flush()
  fp.close()
  fp = None
  Runtime.getRuntime().exec('chmod 750 '+os.environ.get('DOMAIN_HOME')+'/bin/docker_startWebLogic.sh')

  fp = open(os.environ.get('DOMAIN_HOME')+'/bin/docker_changePassword.sh','wb')
  fp.write(script2)
  fp.flush()
  fp.close()
  fp = None
  Runtime.getRuntime().exec('chmod 750 '+os.environ.get('DOMAIN_HOME')+'/bin/docker_changePassword.sh')
   
 except Exception,e:
  print e
  dumpStack()

# Load WebLogic domain config
def loadConfig():
 mapper = ObjectMapper()
 maps = mapper.readValue(File('domain.json'),HashMap().getClass())
 return maps

if __name__== 'main':
 startCreate()

