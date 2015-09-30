2.0.0 (build 216)
------------------------------------
Special Notes
---------------
-	This is the 2.0 final release, which includes both Ubuntu 14 and CentOS 7 packages. 
-	16 new features are added, and 33 bugs are fixed till this release.


New Features
---------------
-	[VSM-342](https//01.org/jira/browse/VSM-342)	support ceph upgrade on centos 7
-	[VSM-88](https//01.org/jira/browse/VSM-88)	On monitor status page, report what server each monitor is running on.
-	[VSM-162](https//01.org/jira/browse/VSM-162)	need to support typical openstack deployment with multiple cinder/nova/glance instances beside currrent all-in-one mode
-	[VSM-246](https//01.org/jira/browse/VSM-246)	a separate tool to help make a node ready for addition into cluster
-	[VSM-307](https//01.org/jira/browse/VSM-307)	the operator expects to upgrade ceph cluster
-	[VSM-309](https//01.org/jira/browse/VSM-309)	Disk identification: the operator expects to identify physical location of failed disks for replacement
-	[VSM-327](https//01.org/jira/browse/VSM-327)	Dashboard: it's required to have summary for device capacity status to show if full
-	[VSM-358](https//01.org/jira/browse/VSM-358)	Support normal user instead of root to install vsm
-	[VSM-355](https//01.org/jira/browse/VSM-355)	there are some used disk paths list in the data path field and journal dik path field on page 'add new osd'
-	[VSM-352](https//01.org/jira/browse/VSM-352)	servermgmt page autorefrush too frequent
-	[VSM-346](https//01.org/jira/browse/VSM-346)	Add complete set of Juno features in Horizon; pluggable settings, etc.
-	[VSM-341](https//01.org/jira/browse/VSM-341)	expect to have some utilties to help make automation tests.
-	[VSM-291](https//01.org/jira/browse/VSM-291)	The operator expects to present pools to multiple openstack clusters or regions
-	[VSM-331](https//01.org/jira/browse/VSM-331)	it's necesary to monitor device utilization from dashboard
-	[VSM-339](https//01.org/jira/browse/VSM-339)	Configuration Management: as more and more features are added, and different scenarios require different settings, configuration is requried.
-	[VSM-337](https//01.org/jira/browse/VSM-337)	Upgrade: expect to upgrade from 1.0 to 2.0


Resolved bugs
----------------
-	[VSM-312](https//01.org/jira/browse/VSM-312)	vsm-node sets node status="Need more IP" if a Monitor only node does not have a cluster IP address..
-	[VSM-17](https//01.org/jira/browse/VSM-17)		[CDEK-1608] User can remove himself, but after command execution he is not automatically log out
-	[VSM-329](https//01.org/jira/browse/VSM-329)	Remove Monitors button in Manage Servers hangs when Monitor node also has MDS daemon
-	[VSM-274](https//01.org/jira/browse/VSM-274)	a new user logged in vsm and can delete himself
-	[VSM-362](https//01.org/jira/browse/VSM-362)	there are a lot of "in-Up" log in apache error log
-	[VSM-364](https//01.org/jira/browse/VSM-364)	when remove one monitor without MDS co-located, the operation keeps running and no end.
-	[VSM-359](https//01.org/jira/browse/VSM-359)	get smart info inaccurate
-	[VSM-363](https//01.org/jira/browse/VSM-363)	if removing a monitor where the MDS is co-located, after finished, the status has changed to "available" instead of "active".
-	[VSM-319](https//01.org/jira/browse/VSM-319)	performance monitor error when restart vsm processes on controller
-	[VSM-322](https//01.org/jira/browse/VSM-322)	there are exceptions when request vsm dashboard
-	[VSM-330](https//01.org/jira/browse/VSM-330)	When upgrading from Firefly to Giant, the upgrade complains missing python-rados package
-	[VSM-360](https//01.org/jira/browse/VSM-360)	No servers list after newly installed with errors " Permission denied: '/tmp/crushmap'"
-	[VSM-332](https//01.org/jira/browse/VSM-332)	sometimes diamond service start failed
-	[VSM-333](https//01.org/jira/browse/VSM-333)	Error: "Activation of org.freedesktop.secrets timed out", when installing with 2.0 beta 1
-	[VSM-345](https//01.org/jira/browse/VSM-345)	remove server error：no pemssion to stop osd service
-	[VSM-348](https//01.org/jira/browse/VSM-348)	deploy agent node after vsm cluster has been created, the token in .token file is invalid
-	[VSM-361](https//01.org/jira/browse/VSM-361)	when one osd is full, the dashboard doesn't mark one osd is full
-	[VSM-347](https//01.org/jira/browse/VSM-347)	When clicking on "add new osd" at device management, a server error page pops up
-	[VSM-353](https//01.org/jira/browse/VSM-353)	changed the password of current user,an error page pops up
-	[VSM-336](https//01.org/jira/browse/VSM-336)	On Dashboard, even no cluster is created, the VSM version and uptime should be displayed
-	[VSM-343](https//01.org/jira/browse/VSM-343)	can't create cache tier with latest code
-	[VSM-344](https//01.org/jira/browse/VSM-344)	after a few times install, clean-up, reinstall, we have seem some "eaddrinuse" errors on starting rabbitmq
-	[VSM-357](https//01.org/jira/browse/VSM-357)	'add new disk':if data disk and journal disk is in the different partitions of the same disk, the opearation will be unsuccessful
-	[VSM-350](https//01.org/jira/browse/VSM-350)	no response when get latency performance on dashboard
-	[VSM-351](https//01.org/jira/browse/VSM-351)	ceph upgrade on ubuntu unsuccess
-	[VSM-356](https//01.org/jira/browse/VSM-356)	I got warning info means that the number of pg in each osd is too large after upgrade ceph from a lower version to hammar
-	[VSM-354](https//01.org/jira/browse/VSM-354)	when 'create cluster' page opened,other pages still can be opened
-	[VSM-349](https//01.org/jira/browse/VSM-349)	click 'create cluster',I got the tip:there are some zones no monitor created
-	[VSM-340](https//01.org/jira/browse/VSM-340)	Manifest: even using the same token generated from agent-token, server_manifest still complains connection error
-	[VSM-328](https//01.org/jira/browse/VSM-328)	Dashboard: when one disk is full, the warning message is not showing correctly
-	[VSM-338](https//01.org/jira/browse/VSM-338)	Upgrade: current ceph upgrade requires all agent nodes have internet connections, which normally is not true.
-	[VSM-334](https//01.org/jira/browse/VSM-334)	upgrade: when set hammer url, then click "submit", the final ceph version is still firefly.
-	[VSM-335](https//01.org/jira/browse/VSM-335)	The version on UI only shows 2.0.0, but no build number


Known issues
-----------------



2.0.0 (build 163)
------------------------------------
Special Notes
---------------
-	this is a 2.0 beta 1 release, still plenty of changes in this release, and we did some initial tests  on it. 
-	15 new features are added, and 41 bugs are fixed till this release.


New Features
---------------
-	[VSM-135](https//01.org/jira/browse/VSM-135)	CentOS 6.5 and 7.0 Support			
-	[VSM-296](https//01.org/jira/browse/VSM-296)	Show performance on the dashboard			
-	[VSM-4](https//01.org/jira/browse/VSM-4)	Average Response Time" missing in dashboard Overview panel "VSM Status" section.			
-	[VSM-159](https//01.org/jira/browse/VSM-159)	add issue reporting tool			
-	[VSM-156](https//01.org/jira/browse/VSM-156)	add sanity check tool to help identify potential issues before or after deployment			
-	[VSM-15](https//01.org/jira/browse/VSM-15)	VSM-backup prompt info not correct			
-	[VSM-124](https//01.org/jira/browse/VSM-124)	[CDEK-1852] VSM | adding possibility to manipulate ceph values in cluster.manifest file			
-	[VSM-242](https//01.org/jira/browse/VSM-242)	Allow user to modify ceph.conf outside VSM			
-	[VSM-184](https//01.org/jira/browse/VSM-184)	add automated script to help deploy VSM on multiple nodes			
-	[VSM-103](https//01.org/jira/browse/VSM-103)	Suport a Single Keystone Instance in OpenStack Environments			
-	[VSM-303](https//01.org/jira/browse/VSM-303)	Ajust the UI like openstack dashboard			
-	[VSM-54](https//01.org/jira/browse/VSM-54)	On OSD Status page: Provide filter option to only display OSDs that are not up and in			
-	[VSM-190](https//01.org/jira/browse/VSM-190)	Add disks to cluster		
-	[VSM-220](https//01.org/jira/browse/VSM-220)	Operator expects to know what's happending inside ceph cluster through performance counters
-	[VSM-134](https//01.org/jira/browse/VSM-134)	Ubuntu 14.X Support


Resolved bugs
----------------
-	[VSM-318](https//01.org/jira/browse/VSM-318)	"remove osd" doesn't work
-	[VSM-325](https//01.org/jira/browse/VSM-325)	Monitor: negative update time shown on monitor status when removing an monitor.
-	[VSM-269](https//01.org/jira/browse/VSM-269)	Smart info doesn't work in Device mgmt.
-	[VSM-324](https//01.org/jira/browse/VSM-324)	Monitor: inconsistent monitor number on Monitor status page when removing one monitor
-	[VSM-326](https//01.org/jira/browse/VSM-326)	UI: the progress indicator is not showing at the center of screen but the top-left
-	[VSM-323](https//01.org/jira/browse/VSM-323)	Installer: when installing diamond on each agents, there are a lot of File or Folder not found issues
-	[VSM-306](https//01.org/jira/browse/VSM-306)	when executing buildvsm on ubuntu, the script complains no vsm user created
-	[VSM-263](https//01.org/jira/browse/VSM-263)	The pie chart in "Storage Group Status" page is disappeared.
-	[VSM-320](https//01.org/jira/browse/VSM-320)	if installing from a node instead of the controller, the installation will be stopped at missing deployrc
-	[VSM-176](https//01.org/jira/browse/VSM-176)	SSL certificate password is stored in a plain text file
-	[VSM-230](https//01.org/jira/browse/VSM-230)	when presenting pool to openstack, cache tiering pools should be listed.
-	[VSM-26](https//01.org/jira/browse/VSM-26)	[CDEK-1664] VSM | Not possible to replace node if ceph contain only 3 nodes.
-	[VSM-51](https//01.org/jira/browse/VSM-51)	Install Fails for VSM 0.8.0 Engineering Build Release
-	[VSM-236](https//01.org/jira/browse/VSM-236)	no way to check manifest correctness after editing them
-	[VSM-29](https//01.org/jira/browse/VSM-29)	VSM-agent process causes high i/o on os disk
-	[VSM-216](https//01.org/jira/browse/VSM-216)	Add storage group requires at least 3 nodes
-	[VSM-33](https//01.org/jira/browse/VSM-33)	negative update time in RBD list
-	[VSM-113](https//01.org/jira/browse/VSM-113)	[CDEK-1835] VSM | /var/log/httpd/error_log - constantly ongoing messages [error] <Response [200]>
-	[VSM-179](https//01.org/jira/browse/VSM-179)	keep ceph.conf up to date when executing "remove server" operations.
-	[VSM-177](https//01.org/jira/browse/VSM-177)	wrong /etc/fstab entry for osd device mount point
-	[VSM-233](https//01.org/jira/browse/VSM-233)	console blocks when running automatic installation procedure
-	[VSM-239](https//01.org/jira/browse/VSM-239)	with automatic deployment, the execution is blocked at asking if start mysql service
-	[VSM-166](https//01.org/jira/browse/VSM-166)	cluster_manifest sanity check program gives incorrect advice for auth_keys
-	[VSM-207](https//01.org/jira/browse/VSM-207)	can't assume eth0 device name
-	[VSM-224](https//01.org/jira/browse/VSM-224)	Controller node error in /var/log/httpd/error_log - constantly ongoing messages [error] <Response [200]>
-	[VSM-121](https//01.org/jira/browse/VSM-121)	Storage node unable to connect to controller although network is OK and all setting correct
-	[VSM-244](https//01.org/jira/browse/VSM-244)	Internal server error when installing v1.1
-	[VSM-123](https//01.org/jira/browse/VSM-123)	Storage node will not be able to contact controller node to install if http proxy set
-	[VSM-171](https//01.org/jira/browse/VSM-171)	[CDEK1672] VSM_CLI | list shows Admin network in Public IP section
-	[VSM-168](https//01.org/jira/browse/VSM-168)	[CDEK1800] VSM_CLI | remove mds - doesn't update vsm database
-	[VSM-193](https//01.org/jira/browse/VSM-193)	hard-coded cluster id
-	[VSM-260](https//01.org/jira/browse/VSM-260)	the check_network in server_manifest will be wrong when it has a single network card
-	[VSM-317](https//01.org/jira/browse/VSM-317)	the update time in MDS block is empty
-	[VSM-249](https//01.org/jira/browse/VSM-249)	can not open dashboard and get the debug infomation "Invalid block tag: 'horizon_nav'"
-	[VSM-299](https//01.org/jira/browse/VSM-299)	when after installed vsm, but no ceph cluster deployed, there is still show 3 storage groups
-	[VSM-310](https//01.org/jira/browse/VSM-310)	with Firefox, for all tables, the vertical separator between the first and second column gets disappered
-	[VSM-313](https//01.org/jira/browse/VSM-313)	the logo is disappeared when running on IE 11
-	[VSM-314](https//01.org/jira/browse/VSM-314)	there is no progress indicator when an operation is not returned.
-	[VSM-316](https//01.org/jira/browse/VSM-316)	the button style in "device management" page is different from others.
-	[VSM-311](https//01.org/jira/browse/VSM-311)	The blocks in dashboard are exceed out of the width of heading
-	[VSM-315](https//01.org/jira/browse/VSM-315)	"add server" doesn't work in alpha 2


Known issues
-----------------
-	[VSM-332](https//01.org/jira/browse/VSM-332) 	sometimes diamond service start failed 
-	[VSM-330](https//01.org/jira/browse/VSM-330) 	When upgrading from Firefly to Giant, the upgrade complains missing python-rados package 




2.0.0 (build 149)
------------------------------------
Special Notes
---------------
-	this is a 2.0 alpha 2 release, we did some initial tests on it. 
-	29 new features are added, and 47 bugs are fixed till this release.


New Features
---------------
-	[VSM-63](https//01.org/jira/browse/VSM-63)	Filter/Identify OSDs that are not up and in
-	[VSM-61](https//01.org/jira/browse/VSM-61)	Openstack Prod release alignment with VSM
-	[VSM-55](https//01.org/jira/browse/VSM-55)	Paginate OSD pages
-	[VSM-10](https//01.org/jira/browse/VSM-10)	VSM1.0 -[CDEK-1190] VSM "Create cluster" cannot select storage nodes or monito
-	[VSM-304](https//01.org/jira/browse/VSM-304)	Support to present pool to Openstack Juno All in one
-	[VSM-282](https//01.org/jira/browse/VSM-282)	current installer scripts only support ip address based, it's also required to support host name based
-	[VSM-256](https//01.org/jira/browse/VSM-256)	current logic enforces 3 replicas, somethings user may require to loose or tighten the enforcement.
-	[VSM-257](https//01.org/jira/browse/VSM-257)	reorganize functions inside installer to make it's possible to install controller or agent separately
-	[VSM-243](https//01.org/jira/browse/VSM-243)	the "create cluster" button doesn't take in effect after click on ubuntu 14
-	[VSM-235](https//01.org/jira/browse/VSM-235)	make scripts can support both rpm and deb packages
-	[VSM-222](https//01.org/jira/browse/VSM-222)	It's necessary to import a VSM created cluster by VSM itself.
-	[VSM-221](https//01.org/jira/browse/VSM-221)	upgrade vsm dependent openstack packages to juno
-	[VSM-212](https//01.org/jira/browse/VSM-212)	request to support ceph hammer release
-	[VSM-209](https//01.org/jira/browse/VSM-209)	support multiple subnets
-	[VSM-189](https//01.org/jira/browse/VSM-189)	“Add Server” progress
-	[VSM-163](https//01.org/jira/browse/VSM-163)	server_manifest does not check for local host in /etc/hosts
-	[VSM-154](https//01.org/jira/browse/VSM-154)	Request to have a new column on storage-group-status page to have number of OSD's in each storage group.
-	[VSM-143](https//01.org/jira/browse/VSM-143)	On OSD Status page, limit to 100 OSDs per page
-	[VSM-144](https//01.org/jira/browse/VSM-144)	On OSD Status page, sort OSDs by status, server, % capacity used
-	[VSM-130](https//01.org/jira/browse/VSM-130)	OpenStack Juno Support
-	[VSM-94](https//01.org/jira/browse/VSM-94)	Implement Pass-through Parameters
-	[VSM-85](https//01.org/jira/browse/VSM-85)	Storage Group Status improvements
-	[VSM-89](https//01.org/jira/browse/VSM-89)	Full OS disk indication
-	[VSM-84](https//01.org/jira/browse/VSM-84)	Improved server status reporting
-	[VSM-83](https//01.org/jira/browse/VSM-83)	Restart stopped monitor
-	[VSM-69](https//01.org/jira/browse/VSM-69)	Override default PG per OSD value
-	[VSM-73](https//01.org/jira/browse/VSM-73)	Zone monitor warning
-	[VSM-46](https//01.org/jira/browse/VSM-46)	overlay vsm with existing ceph cluster
-	[VSM-23](https//01.org/jira/browse/VSM-23)	Create User UI should prompt more information


Resolved bugs
----------------
-	[VSM-305](https//01.org/jira/browse/VSM-305)	presenting pool should keep backward comatibility, say working with juno, icehouse, havana
-	[VSM-300](https//01.org/jira/browse/VSM-300)	if no cluster is created, when open "server management"\"manage servers", the Ui becomes messy
-	[VSM-298](https//01.org/jira/browse/VSM-298)	on dashboard, when adding new monitors, the monitor block doesn't update accordingly
-	[VSM-297](https//01.org/jira/browse/VSM-297)	on dashboard, the storage group balls have no data
-	[VSM-293](https//01.org/jira/browse/VSM-293)	wrong version of vsm displayed in the dashboard
-	[VSM-295](https//01.org/jira/browse/VSM-295)	the installation fails at downloading dependent packages if http proxy is required
-	[VSM-292](https//01.org/jira/browse/VSM-292)	the background of tool tip is not clear to view
-	[VSM-286](https//01.org/jira/browse/VSM-286)	present pools to openstack again after you have presented pools, the attach status is always starting
-	[VSM-285](https//01.org/jira/browse/VSM-285)	present multi pools to openstack cinder, the cinder.conf is not complete
-	[VSM-287](https//01.org/jira/browse/VSM-287)	messy login window if accessing https://<ip>/dashboard
-	[VSM-284](https//01.org/jira/browse/VSM-284)	at cluster status monitor, it's expected to provide complete summary instead the partial information from dashboardard
-	[VSM-283](https//01.org/jira/browse/VSM-283)	after restart ceph cluster, the osd tree becomes messy
-	[VSM-280](https//01.org/jira/browse/VSM-280)	"Internal Server Error" when click on "Data Device Status"
-	[VSM-278](https//01.org/jira/browse/VSM-278)	after I add a server by clicking 'add server',the osd tree become messy
-	[VSM-279](https//01.org/jira/browse/VSM-279)	click 'restart osd' or 'restore osd',the osd tree will become messy
-	[VSM-281](https//01.org/jira/browse/VSM-281)	on dashboard, the cluster status like "warning" shouldn't be clickable
-	[VSM-276](https//01.org/jira/browse/VSM-276)	Allow agent to be deployed on nodes where no ceph role assigned
-	[VSM-277](https//01.org/jira/browse/VSM-277)	click on "add storage group" will tigger "something went wrong" error on UI
-	[VSM-272](https//01.org/jira/browse/VSM-272)	on OS with newer rabbitmq version like 3.4, message queue can't be accessed
-	[VSM-273](https//01.org/jira/browse/VSM-273)	"Import Error name Login" received when try to login to web console
-	[VSM-275](https//01.org/jira/browse/VSM-275)	the overview page is messy with Firefox
-	[VSM-270](https//01.org/jira/browse/VSM-270)	reinstall the keystone when deploy the vsm
-	[VSM-266](https//01.org/jira/browse/VSM-266)	Dashboard UI correction
-	[VSM-265](https//01.org/jira/browse/VSM-265)	Click Manage VSM\"Add/Remove User"\"Change Password", no page shows up
-	[VSM-264](https//01.org/jira/browse/VSM-264)	on "PG Status" page, the text layout is messy.
-	[VSM-267](https//01.org/jira/browse/VSM-267)	The logo is not fully shown.
-	[VSM-268](https//01.org/jira/browse/VSM-268)	Can't create EC pool
-	[VSM-262](https//01.org/jira/browse/VSM-262)	when clicking on "device management", the page shows "something went wrong"
-	[VSM-258](https//01.org/jira/browse/VSM-258)	wrong dependencies url
-	[VSM-259](https//01.org/jira/browse/VSM-259)	script 'vsm-agent' missing LSB tags and overrides
-	[VSM-253](https//01.org/jira/browse/VSM-253)	A lot of buttons is invalid such as “addmonitor”,“removemonitor”,“addserver”,“removeserver”,“restore osd”,“remove osd” and so on
-	[VSM-254](https//01.org/jira/browse/VSM-254)	the successful tip boxes can't shut down such as "Success: Successfully created storage pool: "
-	[VSM-255](https//01.org/jira/browse/VSM-255)	when creating ceph cluster with one zone defined, the ceph cluster keeps in health_warn status
-	[VSM-252](https//01.org/jira/browse/VSM-252)	Most of the interface's auto refresh function is invalid
-	[VSM-251](https//01.org/jira/browse/VSM-251)	after clicked clusterManagement->create cluster->create cluster,there is not mds created.
-	[VSM-250](https//01.org/jira/browse/VSM-250)	Error when packing
-	[VSM-245](https//01.org/jira/browse/VSM-245)	error creating cluster
-	[VSM-231](https//01.org/jira/browse/VSM-231)	VSM | Not possible to choose the machines during cluster creation
-	[VSM-229](https//01.org/jira/browse/VSM-229)	Error state displayed on green color
-	[VSM-225](https//01.org/jira/browse/VSM-225)	VSM Creates Very Small pg_num and pg._num Size for EC Pool
-	[VSM-218](https//01.org/jira/browse/VSM-218)	on centos 7, the web layout is messy
-	[VSM-195](https//01.org/jira/browse/VSM-195)	if no cluster initialized, the UI shouldn’t knock at ‘manage servers’.
-	[VSM-194](https//01.org/jira/browse/VSM-194)	User experience: OSD Status and Manage Devices.
-	[VSM-180](https//01.org/jira/browse/VSM-180)	When a cluster is destroyed and recreated, VSM controller increments the cluster id (aka database rowid)
-	[VSM-153](https//01.org/jira/browse/VSM-153)	after clicked vsm->settings->update,there is no successful tip
-	[VSM-68](https//01.org/jira/browse/VSM-68)	Veriffy there are enough discrete servers and/or zones to support a VSM requested replication level
-	[VSM-5](https//01.org/jira/browse/VSM-5)	KB used in "Pool status" panel not consistent with "ceph df" in backend


Known issues
-----------------
-	[VSM-313](https//01.org/jira/browse/VSM-313)	the logo is disappeared when running on IE 11



2.0.0 (build 123)
------------------------------------

Special Notes
---------------
-	this is alpha 1 release for 2.0, which is not well verified yet, just for early preview.


1.1_1
------------------------------------

Special Notes
---------------
-	this is a bugfix release for 1.1, which fixed the issues found in VSM-242 ("Allow user to modify ceph.conf outside VSM"). Also adding an new script uninstall.sh to help uninstall VSM in the case user expects to restart installation again.


New Features
---------------
-	[VSM-209](https://01.org/jira/browse/VSM-209)	support multiple subnets


Resolved bugs
----------------
-	[VSM-260](https://01.org/jira/browse/VSM-260)	the check_network in server_manifest will be wrong when it has a single network card


Known issues
-----------------
-	



1.1
------------------------------------

Special Notes
---------------
-	starting from v1.1, the vsm dependencies are maintained on [vsm-dependencies repository](http://github.com/01org/vsm-dependencies) for tracking and trouble shooting.
-	starting from v1.1, an automatic deployment tool is provided to deploy whole vsm controller and agents from one placement.

	
New Features
---------------
-	[VSM-156](https://01.org/jira/browse/VSM-156)	add sanity check tool to help identify potential issues before or after deployment
-	[VSM-159](https://01.org/jira/browse/VSM-159)	add issue reporting tool
-	[VSM-184](https://01.org/jira/browse/VSM-184)	add automated script to help deploy VSM on multiple nodes
-	[VSM-242](https://01.org/jira/browse/VSM-242)	Allow user to modify ceph.conf outside VSM

Resolved bugs
----------------
-	[VSM-4](https://01.org/jira/browse/VSM-4)	Average Response Time" missing in dashboard Overview panel "VSM Status" section. 
-	[VSM-15](https://01.org/jira/browse/VSM-15)	VSM-backup prompt info not correct
-	[VSM-25](https://01.org/jira/browse/VSM-25) VSM Dashboard | Capacity of hard drives is wrong and percentage used capacity is not correct.
-	[VSM-26](https://01.org/jira/browse/VSM-26)	[CDEK-1664] VSM | Not possible to replace node if ceph contain only 3 nodes.
-	[VSM-29](https://01.org/jira/browse/VSM-29)	vsm-agent process causes high i/o on os disk
-	[VSM-33](https://01.org/jira/browse/VSM-33)	negative update time in RBD list
-	[VSM-51](https://01.org/jira/browse/VSM-51)	Install Fails for VSM 0.8.0 Engineering Build Release
-	[VSM-113](https://01.org/jira/browse/VSM-113)	[CDEK-1835] VSM | /var/log/httpd/error_log - constantly ongoing messages [error] <Response [200]>
-	[VSM-121](https://01.org/jira/browse/VSM-121)	Storage node unable to connect to controller although network is OK and all setting correct
-	[VSM-123](https://01.org/jira/browse/VSM-123)	Storage node will not be able to contact controller node to install if http proxy set
-	[VSM-124](https://01.org/jira/browse/VSM-124)	[CDEK-1852] VSM | adding possibility to manipulate ceph values in cluster.manifest file
-	[VSM-166](https://01.org/jira/browse/VSM-166)	cluster_manifest sanity check program gives incorrect advice for auth_keys
-	[VSM-168](https://01.org/jira/browse/VSM-168)	[CDEK1800] VSM_CLI | remove mds - doesn't update vsm database
-	[VSM-171](https://01.org/jira/browse/VSM-171)	[CDEK1672] VSM_CLI | list shows Admin network in Public IP section
-	[VSM-176](https://01.org/jira/browse/VSM-176)	SSL certificate password is stored in a plain text file
-	[VSM-177](https://01.org/jira/browse/VSM-177)	wrong /etc/fstab entry for osd device mount point
-	[VSM-179](https://01.org/jira/browse/VSM-179)	keep ceph.conf up to date when executing "remove server" operations.
-	[VSM-193](https://01.org/jira/browse/VSM-193)	hard-coded cluster id
-	[VSM-207](https://01.org/jira/browse/VSM-207)	can't assume eth0 device name 
-	[VSM-216](https://01.org/jira/browse/VSM-216)	Add storage group requires at least 3 nodes
-	[VSM-217](https://01.org/jira/browse/VSM-217) Problem with replication size on "pool" created on newly added storage group.
-	[VSM-224](https://01.org/jira/browse/VSM-224)	Controller node error in /var/log/httpd/error_log - constantly ongoing messages [error] <Response [200]>
-	[VSM-230](https://01.org/jira/browse/VSM-230)	when presenting pool to openstack, cache tiering pools should be listed. 
-	[VSM-233](https://01.org/jira/browse/VSM-233) console blocks when running automatic installation procedure
-	[VSM-236](https://01.org/jira/browse/VSM-236) no way to check manifest correctness after editing them
-	[VSM-239](https://01.org/jira/browse/VSM-239) with automatic deployment, the execution is blocked at asking if start mysql service
-	[VSM-244](https://01.org/jira/browse/VSM-244) Internal server error when installing v1.1


Known issues
-----------------
-	


1.0
------------------------------------

Special Notes

    For installation, please check the INSTALL.md on current release branch instead of the one on master branch.

New Features

    Openstack Icehouse support

Fixed bugs

    VSM-187 GUI shows always replication 3 when replicated pool is other than "Same as Primary"
    VSM-183 ct_target_max_mem_mb and ct_target_max_capacity_gb sets the same value in create cache tier
    VSM-182 add osd_heartbeat_grace and osd_heartbeat_interval to cluster.manifest
    VSM-173 Can select same storage group in create replicated pool -- which should not

Known issues

    VSM-191 VSM does not display the replica storage group.
    VSM-192 force nonempty.
    VSM-188 Missing column in manage pool page.

