FROM weblogic 

# Maintainer
# ----------
MAINTAINER jerrycao <jerry.cao@oracle.com>

ENV ORACLE_HOME="/weblogic/1213/Oracle/Middleware/Oracle_Home" \
    DOMAIN_HOME="/weblogic/domains/1213/base_domain" \
    SERVER_PORT="7001"

ENV PATH="$PATH:$DOMAIN_HOME/bin"

# Copy installation and configuration file
USER weblogic
COPY create-wls-domain.py domain.json  /weblogic/
COPY db2jcc.jar db2jcc_license_cu.jar /weblogic/

# Create and configure domain
WORKDIR /weblogic
RUN $ORACLE_HOME/wlserver/common/bin/wlst.sh -skipWLSModuleScanning create-wls-domain.py

# Remove temporary files
RUN rm create-wls-domain.py domain.json db2jcc.jar db2jcc_license_cu.jar

RUN mkdir /weblogic/apps && mkdir /weblogic/logs && ln -s /weblogic/apps $DOMAIN_HOME/ && ln -s /weblogic/logs $DOMAIN_HOME/

# Copy app to $DOMAIN_HOME/apps/
COPY SessionTest.war test.war $DOMAIN_HOME/apps/

# EXPOSE SERVER PORT
EXPOSE $SERVER_PORT

# DEFINE DEFAULT COMMAND TO START 
CMD ["docker_startWebLogic.sh"]

WORKDIR /weblogic

