#!/bin/bash

# Copyright 2013 BrewPi
# This file is part of BrewPi.

# BrewPi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# BrewPi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with BrewPi.  If not, see <http://www.gnu.org/licenses/>.

########################
### This script assumes a clean Wheezy Raspbian install. 
### Freeder, v1.0, Aug 2013
### Using a custom 'die' function shamelessly stolen from http://mywiki.wooledge.org/BashFAQ/101
### Using ideas even more shamelessly stolen from Elco and mdma. Thanks guys!
########################


############
### Functions to catch/display errors during setup
############
warn() {
  local fmt="$1"
  shift
#  printf "$fmt\n" "${@}" >&2
  echo -e "\n*** ERROR ERROR ERROR ERROR ERROR ***\n----------------------------------\nSee above lines for error message\nSetup NOT completed\n"
}

die () {
  local st="$?"
  warn "$@"
  exit "$st"
}

############
### Install required packages
############
sudo apt-get update
sudo apt-get install rpi-update apache2 libapache2-mod-php5 php5-cli php5-common php5-cgi php5 python-serial python-simplejson python-configobj python-psutil python-gitdb python-setuptools arduino-core git-core||die 

############
### Create/configure user accounts
############
echo "Creating and configuring user accounts..."
sudo chown -R www-data:www-data /var/www||die
if id -u brewpi >/dev/null 2>&1; then
  echo "User 'brewpi' already exists, skipping..."
else
  sudo useradd -m -k /dev/null -G www-data,dialout brewpi||die
fi
echo -e "brewpi\nbrewpi\n" | sudo passwd brewpi||die
sudo usermod -a -G www-data pi||die
sudo usermod -a -G brewpi pi||die
sudo chown -R www-data:www-data /var/www||die
sudo chown -R brewpi:brewpi /home/brewpi||die

############
### Set sticky bit! nom nom nom
############
sudo find /home/brewpi -type f -exec chmod g+rwx {} \;||die
sudo find /home/brewpi -type d -exec chmod g+rwxs {} \;||die
sudo find /var/www -type d -exec chmod g+rwxs {} \;||die
sudo find /var/www -type f -exec chmod g+rwx {} \;||die

############
### Clone BrewPi repositories
############
echo "Downloading most recent BrewPi codebase..."
sudo rm /var/www/*||die
sudo -u brewpi git clone https://github.com/BrewPi/brewpi-script /home/brewpi||die
sudo -u www-data git clone https://github.com/BrewPi/brewpi-www /var/www||die

############
### Install Web Crontab
############
sudo -u brewpi crontab -l > /tmp/tempcron
sudo -u brewpi echo -e "* * * * * python -u /home/brewpi/brewpi.py --dontrunfile 1>/home/brewpi/logs/stdout.txt 2>>/home/brewpi/logs/stderr.txt &" >> /tmp/tempcron||die
echo -e "Installing BrewPi www crontab..."
sudo -u brewpi crontab /tmp/tempcron||die
rm /tmp/tempcron||die

############
### Check for insecure SSH key
############
defaultKey="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDLNC9E7YjW0Q9btd9aUoAg++/wa06LtBMc1eGPTdu29t89+4onZk1gPGzDYMagHnuBjgBFr4BsZHtng6uCRw8fIftgWrwXxB6ozhD9TM515U9piGsA6H2zlYTlNW99UXLZVUlQzw+OzALOyqeVxhi/FAJzAI9jPLGLpLITeMv8V580g1oPZskuMbnE+oIogdY2TO9e55BWYvaXcfUFQAjF+C02Oo0BFrnkmaNU8v3qBsfQmldsI60+ZaOSnZ0Hkla3b6AnclTYeSQHx5YqiLIFp0e8A1ACfy9vH0qtqq+MchCwDckWrNxzLApOrfwdF4CSMix5RKt9AF+6HOpuI8ZX root@raspberrypi" 

if grep -q "$defaultKey" /etc/ssh/ssh_host_rsa_key.pub; then
  echo "Replacing default SSH keys. You will need to remove the previous key from known hosts on any clients that have previously connected to this rpi."
  if rm -f /etc/ssh/ssh_host_* && dpkg-reconfigure openssh-server; then
     echo "Default SSH keys replaced."
  else
    echo "ERROR - Unable to replace SSH key. You probably want to take the time to do this on your own."
  fi
fi

echo -e "\n* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *"
echo -e "Review the log above for any errors, otherwise, your initial environment install is complete!"
echo -e "Edit your /home/brewpi/settings/config.cfg file if needed and then read http://docs.brewpi.com/getting-started/program-arduino.html for your next steps"
echo -e "\nYou are currently using the password 'brewpi' for the brewpi user. If you wish to change this, type 'sudo passwd brewpi' now, and follow the prompt"
echo -e "\nHappy Brewing!"



