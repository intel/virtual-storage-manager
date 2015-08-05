VSM - Virtual Storage Manager 
=============================
Travis CI: [![Build Status](https://travis-ci.org/01org/virtual-storage-manager.svg?branch=master)](https://travis-ci.org/01org/virtual-storage-manager)

![](https://github.com/01org/virtual-storage-manager/blob/master/vsm_0.jpg "Virtual Storage Manager")

Virtual Storage Manager (VSM) is software that Intel has developed to help manage Ceph clusters.  VSM simplifies 
the creation and day-to-day management of Ceph cluster for cloud and datacenter storage administrators. 

VSM enables OEMs and system integrators to ensure consistent cluster configuration through the use of pre-defined,
standard cluster configurations, and as a result improves ease of cluster installation and operational reliability,
and reduces maintenance and support costs.

VSM supports the creation of clusters containing a mix of hard disk drives (HDDs), Solid State storage, and SSD-cached
HDDs, and simplifies management of the Ceph cluster using a system to organize servers and storage devices according
to performance characteristics, intended use, and failure domain.

The VSM web-based user interface provides the operator with the ability to monitor overall cluster status, manage
cluster hardware and storage capacity, inspect detailed operation status of Ceph subsystems, and attach Ceph pools
to OpenStack Cinder.

VSM has been developed in Python using OpenStack Horizon as the starting point for the application framework, and 
has a familiar look and feel for both software developers and OpenStack administrators. 



Important Notice and Contact Information
----------------------------------------

a) Open source VSM does not have a full-time support team and so would not be generally suitable for production use unless you can support it or have support from a third party. Before you use VSM, please understand the need to invest enough effort to learn how to use it effectively and to address possible bugs.

b) To help VSM develop further, please become an active member of the community and consider giving back by making 
contributions. We intend to make all open source VSM feature proposals public, and do all development publicly.

For other questions, contact yaguang.wang@intel.com or ferber.dan@intel.com


Licensing
---------

a) Intel source code is being released under the Apache 2.0 license.

b) Additional libraries used with VSM have their own licensing; refer to NOTICE for details.


Installation & Usage
--------------------

Please refer to INSTALL.md or INSTALL.pdf to know how to install VSM, and [wiki page](https://github.com/01org/virtual-storage-manager/wiki/Getting-Started-with-VSM) to know how to get started.

Contributing
------------

Please refer to [wiki page](https://github.com/01org/virtual-storage-manager/wiki/VSM-Development) to know how to 
get involved.


Resources
---------

Wiki: (https://github.com/01org/virtual-storage-manager/wiki)

Issue tracking: (https://01.org/jira/browse/VSM)

Mailing list: (http://vsm-discuss.33411.n7.nabble.com/)


*Other names and brands may be claimed as the property of others.


