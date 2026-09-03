#!/bin/bash
cd /root/medsec
echo "[TVRA] Starting API..."
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
echo "[TVRA] Starting Redis..."
redis-server /etc/redis/redis-openvas.conf --daemonize yes 
sleep 10
echo "[TVRA] Starting Vulnerability Scanner..."
/usr/local/bin/ospd-openvas --foreground --unix-socket /run/ospd/ospd-openvas.sock --pid-file /run/ospd/ospd-openvas.pid --log-file /var/log/gvm/ospd-openvas.log --lock-file-dir /var/lock/openvas --socket-mode 0o770 --mqtt-broker-address "" --disable-notus-hashsum-verification yes &
sleep 30
while true;
do 
  if cat /var/log/gvm/ospd-openvas.log | grep 'Finished loading VTs\|VTs were up to date'; then 
      echo "[TVRA] Ready for connection";break;
  else
      echo [TVRA] Loading VTs `ps -aef | grep Reloaded | grep -v grep | sed 's/.*(\(.*\))/\1/'`
      sleep 30
  fi; 
done
wait
