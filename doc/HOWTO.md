#HOWTO
The document includes some best known methods for handling some problems or troubles.

##How to import existing cluster
0. applicable to 2.1 alpha 1.
1. deploy a ceph cluster external (maybe there is already one running)
2. deploy VSM with agents deployed on each ceph node with appropriate role defined.
3. in VSM web ui:
	1. navigate to "Cluster Management\Import Cluster"
	2. you should see all ceph nodes listed.
	3. click "import cluster", then we will see an new page where it asks for crushmap and ceph.conf

4. there are two approaches to get crushmap:
	1. paste crushmap directly into the text box under "Crushmap"
	2. click "Auto Detect", then a dialog will pop up, you'd select one monitor host, and point where is the monitor keyring file on the monitor host.

5. for ceph.conf, **we see some ceph.conf doesn't include osd information, if this is the case, you'd manually add them into ceph.conf.**
6. when crushmap and ceph.conf are ready, click "validate" to see if all can pass. If yes, you could click "submit", if succeed, the message tip will show up to say the import is successful.
7. wait for a few minutes before the status gets synced, then you will see the cluster status.
