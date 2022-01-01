#!/bin/bash
SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")

if [[ $(whoami) -ne 'root' ]]; then
  echo "Must run as root!"
  exit -1
fi

apt-get -y install rpi-update git build-essential python-dev python-smbus python-pip logrotate

echo "Installing logrotate config..."
cp $BASEDIR/silvia-pi-logrotate /etc/logrotate.d

echo "Installing ivPID library..."
cd ~
git clone https://github.com/ivmech/ivPID.git
cp ~/ivPID/PID.py ~/silvia-pi/

echo "Installing remaining python libraries..."
pip3 install --upgrade -r $BASEDIR/requirements.txt

if ! grep silvia-pi.py /etc/rc.local; then
  echo "Adding entry to /etc/rc.local"
  cp /etc/rc.local /etc/rc.local.bak
  cat /etc/rc.local | sed 's|^exit 0$|sudo python /root/silvia-pi/silvia-pi.py & > /root/silvia-pi/silvia-pi.log 2>\&1 \&\n\nexit 0|g' > /etc/rc.local.new
  mv /etc/rc.local.new /etc/rc.local
  chmod 755 /etc/rc.local
else
  echo "Skipping /etc/rc.local modification since entry already found"
fi

echo "Installation complete.  Please reboot."
