## Pages that can be accessed through the app

The following urls are the ones that can be accessed without passing any parameter:
- http://ip-address/publishing/cloud/
- http://ip-address/publishing/gridsync/

These pages show info for a number of sites, so do not require a site name to be specified within the url.

The url http://ip-address/publishing/grid/ , instead, should be used together with the name of the site we are looking for. 
For example: http://ip-address/publishing/grid/BelGrid-UCL/
It is not supposed to be used without passing the name of the site.

The url http://ip-address/publishing/gridsync/ shows a sync table, and it's probably the most important bit of the personality 'apel-data-validation'.
This table contains data related to many sites, specifically number of jobs being published vs in the db, and this number is shown for every (available) month of each site.

Clicking on any name in the first column (containing site names) allows to access a similar table which only shows the data relative to that site.
This more specific table is such that the first columns shows the months for which we have data (for that site). 
Clicking on the month allows to open another table that shows data for that month and site only, divided by submithost.

The pages accessed through the links can of course be accessed by typing directly the url. For example, if we want data related to the site 'CSCS-LCG2' and month '2013-11', we would type :
http://ip-address/publishing/gridsync/CSCS-LCG2/2013-11/ 
However, in this case if there is no data for the month we are looking for, we would get an error.
