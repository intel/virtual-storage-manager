/**
 * Created by shouanxx on 5/5/2015.
 */
$(function(){
	//wip-195: if the cluster count is 0, the server and device are disabled
	CheckDeviceServerEnable();
});


function CheckDeviceServerEnable(){
	$.ajax({
		data:"",
		type:"get",
		dataType:"json",
		url:"/dashboard/vsm/ClusterCount",
		success:function(data){
			if(data.count==0){
				var alist = document.getElementsByTagName("a");
				for(var i=0; i<alist.length;i++){
					if(alist[i].innerText == "Manage Servers"
					|| alist[i].innerText == "Manage Devices" ){
						alist[i].href = "#";
					}
				}
			}
		},
	})
}