# Use an official Ubuntu base image
FROM ubuntu:22.04

# Set environment variables
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib \
    INSTALL_PREFIX=/usr/local \
    MEDSEC_HOME=/root/medsec \
    PATH=$PATH:/usr/local/sbin:/root/medsec: \
    SOURCE_DIR=/root/source \
    INSTALL_DIR=/root/install \
    BUILD_DIR=/root/build \
    DEBIAN_FRONTEND=noninteractive \
    GVM_LIBS_VERSION=22.9.1 \
    OPENVAS_SCANNER_VERSION=23.3.0 \
    OSPD_OPENVAS_VERSION=22.7.1

# Fix mirror list
RUN echo 'Acquire::Retries "100";\
Acquire::https::Timeout "240";\
Acquire::http::Timeout "240";\
' > /etc/apt/apt.conf.d/99custom

#APT::Get::Assume-Yes "true";\
#APT::Install-Recommends "false";\
#APT::Install-Suggests "false";\
#Debug::Acquire::https "false";\
#Debug::Acquire::http "true";\

COPY sources.list /etc/apt

# Update first 
RUN apt-get update 

# Update and install all apt packages
RUN DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y --no-install-recommends \
        build-essential curl cmake pkg-config python3 gnupg libglib2.0-dev libgpgme-dev libgnutls28-dev uuid-dev libssh-gcrypt-dev libhiredis-dev libxml2-dev libpcap-dev libnet1-dev libpaho-mqtt-dev libldap2-dev libradcli-dev \
        libical-dev xsltproc rsync gnutls-bin bison \
        libgcrypt20-dev libpcap-dev libksba-dev nmap libjson-glib-dev libbsd-dev libcurl4-gnutls-dev \
        python3-impacket libsnmp-dev python3-packaging python3-wrapt python3-cffi python3-psutil python3-redis python3-gnupg python3-paho-mqtt \
        python3-pip python3-venv python3-setuptools python3-lxml python3-defusedxml python3-paramiko \
        redis-server mosquitto net-tools python3-xmltodict python3-validators python3-fastapi python3-uvicorn vim && \
    rm -rf /var/lib/apt/lists/*

# Extra packages
RUN python3 -m pip install BeautifulSoup4 requests python-multipart

# Make sure requiments are installed
#RUN python3 -m pip install -r src/requirements.txt

# Create necessary directories
RUN mkdir -p $SOURCE_DIR $BUILD_DIR $INSTALL_DIR


# Install GPG key
RUN curl -f -L https://www.greenbone.net/GBCommunitySigningKey.asc -o /tmp/GBCommunitySigningKey.asc && \
    gpg --import /tmp/GBCommunitySigningKey.asc && \
    echo "8AE4BE429B60A59B311C2E739823FAA60ED1E580:6:" | gpg --import-ownertrust

# Install gvm-libs
RUN curl -f -L https://github.com/greenbone/gvm-libs/archive/refs/tags/v$GVM_LIBS_VERSION.tar.gz -o $SOURCE_DIR/gvm-libs-$GVM_LIBS_VERSION.tar.gz && \
    curl -f -L https://github.com/greenbone/gvm-libs/releases/download/v$GVM_LIBS_VERSION/gvm-libs-v$GVM_LIBS_VERSION.tar.gz.asc -o $SOURCE_DIR/gvm-libs-$GVM_LIBS_VERSION.tar.gz.asc && \
    gpg --verify $SOURCE_DIR/gvm-libs-$GVM_LIBS_VERSION.tar.gz.asc $SOURCE_DIR/gvm-libs-$GVM_LIBS_VERSION.tar.gz && \
    tar -C $SOURCE_DIR -xvzf $SOURCE_DIR/gvm-libs-$GVM_LIBS_VERSION.tar.gz && \
    mkdir -p $BUILD_DIR/gvm-libs && cd $BUILD_DIR/gvm-libs && \
    cmake $SOURCE_DIR/gvm-libs-$GVM_LIBS_VERSION -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX -DCMAKE_BUILD_TYPE=Release -DSYSCONFDIR=/etc -DLOCALSTATEDIR=/var && \
    make -j$(nproc) && \
    make DESTDIR=$INSTALL_DIR/gvm-libs install && \
    cp -rv $INSTALL_DIR/gvm-libs/* /

# Install openvas-scanner
RUN curl -f -L https://github.com/greenbone/openvas-scanner/archive/refs/tags/v$OPENVAS_SCANNER_VERSION.tar.gz -o $SOURCE_DIR/openvas-scanner-$OPENVAS_SCANNER_VERSION.tar.gz && \
    curl -f -L https://github.com/greenbone/openvas-scanner/releases/download/v$OPENVAS_SCANNER_VERSION/openvas-scanner-v$OPENVAS_SCANNER_VERSION.tar.gz.asc -o $SOURCE_DIR/openvas-scanner-$OPENVAS_SCANNER_VERSION.tar.gz.asc && \
    gpg --verify $SOURCE_DIR/openvas-scanner-$OPENVAS_SCANNER_VERSION.tar.gz.asc $SOURCE_DIR/openvas-scanner-$OPENVAS_SCANNER_VERSION.tar.gz && \
    tar -C $SOURCE_DIR -xvzf $SOURCE_DIR/openvas-scanner-$OPENVAS_SCANNER_VERSION.tar.gz && \
    mkdir -p $BUILD_DIR/openvas-scanner && cd $BUILD_DIR/openvas-scanner && \
    cmake $SOURCE_DIR/openvas-scanner-$OPENVAS_SCANNER_VERSION -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX -DCMAKE_BUILD_TYPE=Release -DINSTALL_OLD_SYNC_SCRIPT=OFF -DSYSCONFDIR=/etc -DLOCALSTATEDIR=/var -DOPENVAS_FEED_LOCK_PATH=/var/lib/openvas/feed-update.lock -DOPENVAS_RUN_DIR=/run/ospd && \
    make -j$(nproc) && \
    make DESTDIR=$INSTALL_DIR/openvas-scanner install && \
    cp -rv $INSTALL_DIR/openvas-scanner/* /

# Install ospd-openvas
RUN curl -f -L https://github.com/greenbone/ospd-openvas/archive/refs/tags/v$OSPD_OPENVAS_VERSION.tar.gz -o $SOURCE_DIR/ospd-openvas-$OSPD_OPENVAS_VERSION.tar.gz && \
    curl -f -L https://github.com/greenbone/ospd-openvas/releases/download/v$OSPD_OPENVAS_VERSION/ospd-openvas-v$OSPD_OPENVAS_VERSION.tar.gz.asc -o $SOURCE_DIR/ospd-openvas-$OSPD_OPENVAS_VERSION.tar.gz.asc && \
    gpg --verify $SOURCE_DIR/ospd-openvas-$OSPD_OPENVAS_VERSION.tar.gz.asc $SOURCE_DIR/ospd-openvas-$OSPD_OPENVAS_VERSION.tar.gz && \
    tar -C $SOURCE_DIR -xvzf $SOURCE_DIR/ospd-openvas-$OSPD_OPENVAS_VERSION.tar.gz && \
    cd $SOURCE_DIR/ospd-openvas-$OSPD_OPENVAS_VERSION && \
    python3 -m pip install --root=$INSTALL_DIR/ospd-openvas --no-warn-script-location . && \
    cp -rv $INSTALL_DIR/ospd-openvas/* /

# Install greenbone-feed-sync
RUN python3 -m pip install --root=$INSTALL_DIR/greenbone-feed-sync --no-warn-script-location greenbone-feed-sync && \
    cp -rv $INSTALL_DIR/greenbone-feed-sync/* /

# Install gvm-tools
RUN python3 -m pip install --root=$INSTALL_DIR/gvm-tools --no-warn-script-location gvm-tools==24.3.0 python-gvm==24.3.0 && \
    cp -rv $INSTALL_DIR/gvm-tools/* /

# Configure services
#COnfig to recreate
#db_address = /run/redis-openvas/redis.sock
#mqtt_server_uri = localhost:1883
#table_driven_lsc = yes
#log_whole_attack = yes
#test_alive_hosts_only = no
#timeout_retry = 1
#max_checks = 5
#checks_read_timeout = 5
#time_between_request = 1
#open_sock_max_attempts = 3
#test_alive_wait_timeout = 2
#safe_checks = yes
#scanner_plugins_timeout = 360
#plugins_timeout = 30
RUN cp $SOURCE_DIR/openvas-scanner-$OPENVAS_SCANNER_VERSION/config/redis-openvas.conf /etc/redis/ && \
    chown redis:redis /etc/redis/redis-openvas.conf && \
    sed -i 's/^\(logfile .*\)$/logfile \/var\/log\/redis\/redis.log/' /etc/redis/redis-openvas.conf && \
    echo "db_address = /run/redis-openvas/redis.sock" | tee -a /etc/openvas/openvas.conf && \
    echo "mqtt_server_uri = localhost:1883\ntable_driven_lsc = yes\nlog_whole_attack = yes\ntest_alive_hosts_only = no\ntimeout_retry = 1\nmax_checks = 5" | tee -a /etc/openvas/openvas.conf && \
    echo "checks_read_timeout = 5\ntime_between_request = 1\nopen_sock_max_attempts = 3\ntest_alive_wait_timeout = 2\nsafe_checks = yes\nscanner_plugins_timeout = 360\nplugins_timeout = 30" | tee -a /etc/openvas/openvas.conf && \
    mkdir -p /var/lib/notus /var/lib/gvm /var/log/gvm /run/ospd /var/lib/openvas

# Cleanup unnecessary files
RUN rm -rf /var/lib/apt/lists/* /root/build /root/install /root/source

RUN mkdir -p /var/lib/openvas /var/lib/notus/advisories /var/lib/notus/products /run/redis-openvas

COPY nvt/plugins /var/lib/openvas/plugins
COPY nvt/products /var/lib/notus/products
COPY nvt/advisories /var/lib/notus/advisories

COPY src/medsec /root/medsec

# If we need to refresh feeds before we release the image
#CMD while true; do if ! /usr/local/bin/greenbone-feed-sync --type nvt; then sleep 5; continue; else break; fi; done; \

#CMD python3 -m http.server --directory /root/medsec/www 8080 & redis-server /etc/redis/redis-openvas.conf --daemonize yes && sleep 10 && /usr/local/bin/ospd-openvas --foreground --unix-socket /run/ospd/ospd-openvas.sock --pid-file /run/ospd/ospd-openvas.pid --log-file /var/log/gvm/ospd-openvas.log --lock-file-dir /var/lock/openvas --socket-mode 0o770 --mqtt-broker-address "" --disable-notus-hashsum-verification yes
ENTRYPOINT ["/root/medsec/entrypoint.sh"]
