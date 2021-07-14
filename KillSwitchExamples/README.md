README for EnvironmentalKillSwitch

# Power Strip Used
The power strip used as the kill switch is the Kasa Smart Wi-Fi Power Strip

# Hardware Setup
To setup the Kasa power strip download the Kasa app and add a smart plug. Then plug the
power strip into an outlet and follow the directions in the app to complete the setup

# Command line set up
To be able to run kasa commands in the terminal you will need to install python-kasa using
the command "pip install python-kasa --pre" to get the latest version. Then use "-kasa --help"
to learn about more commands.

# Getting the alias or host
To get the alias or host use "kasa --strip discover" and look for Host (ex: Host: 111.111.1.11)
or "== *Alias here* - HS300(US) =="