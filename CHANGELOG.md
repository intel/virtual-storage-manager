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

