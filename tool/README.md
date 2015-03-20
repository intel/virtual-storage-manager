# Auto-deploy #
> 

## Aims: ##
> To teach you how to use the install.sh script to deploy vsm automatically.

## Note: ##
> The servers should have been set mutual trust.

## Steps: ##
1. Changing the "hostrc" file, set the storage_ip_list and the controller_ip.
   
2. Under the tool/manifest folder, you should create the folders named by the ip of controller
 and storage node.
 
3. Copy the cluster.manifest.sample to the folder named by the ip of controller node. Change
 the filename from cluster.manifest.sample to cluster.manifest. Last, You should change the file as required.

4. Copy the server.manifest.sample to the folders named by the ip of storage nodes. Change the
 filename from server.manifest.sample to server.manifest. Last, You should change the file as required.

5. Put the vsmrepo folder with vsm rpms parallel with the tool folder manually if you don't
 make vsm from the source.

6. You can put the dependence folder named vsmrepo uder the tool folder. If you don't do that,
 it will try to connect the internet to download these dependence packages.

## Commands: ##
[root@localhost tool]# bash +x install.sh --help

Usage: install.sh

Auto deploy vsm:
    The tool can help you to deploy the vsm envirement automatically.
    Please run such as bash +x install.sh

Options:
  --help | -h
    Print usage information.
  --manifest [manifest directory] | -m [manifest directory]
    The directory to store the server.manifest and cluster.manifest.
  --version [master] | -v [master]
    The version of vsm dependences to download(Default=master).
  --ip [storage ip]
    For future.



