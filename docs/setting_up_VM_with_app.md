## Steps to follow to get a VM with monitoring app running on Apache

To get a 'prototype' of the monitoring app running with Apache, follow these steps:
- create a cloud VM of the type: scientific-linux-7-aq
- continue by selecting sandbox 'testing_personality_2', archetype 'ral-tier1', personality 'apel-data-validation-test'

Allow 15 minutes after the machine is created, then remember to edit security groups from OpenStack to allow Apache to work.
Then follow these steps from within the machine:
- yum remove git && quattor-fetch && quattor-configure --all
- cd /usr/share/DJANGO_MONITORING_APP/monitoring
- modify the file settings.py, specifically the dict called DATABASES, to include the right credentials and database names
- cd ..
- source venv/bin/activate
- systemctl restart httpd
- sudo chown apache .

At this point the app should be working, so just get the ip address by writing "hostname -I" within the machine and the app should be already running at that address.


## What to do if the app seems to stop working after closing the VM
If the VM is shut down, next time we try to open the app, Apache might give the error message "Unable to open the database file".
If this happens, just follow these steps on the machine:
1. cd /usr/share/DJANGO_MONITORING_APP
2. source venv/bin/activate
3. sudo chown apache .

Note that step 2 is necessary for step 3 to work and the error message to disappear.

