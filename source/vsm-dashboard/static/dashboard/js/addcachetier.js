$(function(){
	InitCtrlCSS();
	ModifyLayout();
});

function InitCtrlCSS(){
	var ctrlSelect = $("select");
	for(var i=0;i<ctrlSelect.length;i++){
		ctrlSelect[i].className = "form-control";
	}

	var ctrlText = $("input[type='text']");
	for(var i=0;i<ctrlText.length;i++){
		ctrlText[i].className = "form-control";
	}

    var ctrlText = $("input[type='number']");
    for(var i=0;i<ctrlText.length;i++){
            ctrlText[i].className = "form-control";
    }
}

function ModifyLayout(){
	$("input[id=id_force_nonempty]").appendTo($("label[for=id_force_nonempty]"));
}

function SwithForceNoneEmpty(checked){
	if(checked)
		$("#divForceNonEmpty")[0].style.display = "";
	else
		$("#divForceNonEmpty")[0].style.display = "none";
}


$("#btnAddCacheTier").click(function(){

	var CachePoolID = $("#selCacheTierPool").val();
	var StoragePoolID = $("#selStorageTierPool").val();

	if(CachePoolID == StoragePoolID){
		showTip("error","Failed to add cache tier: cache_pool, storage_pool cannot be the same!")
		return  false;
	}

	if($("#chkForceNonempty")[0].checked == true){
		//Check the field is should not null
		if(   $("#txtHitSetCount").val() == ""
		   || $("#txtHitSetPeriod").val() == ""
		   || $("#txtTargetMaximumMemory").val() == ""
		   || $("#txtTargetDirtyRatio").val() == ""
		   || $("#txtTargetFullRatio").val() == ""
		   || $("#txtTargetMaximumObjects").val() == ""
		   || $("#txtTargetMinimumFlushAge").val() == ""
		   || $("#txtTargetMinimumEvictAge").val() == "" ){
			showTip("error","The field is marked as '*' should not be empty");
			return  false;
		}
	}


	var data = {
		"cache_tier":{
			"storage_pool_id":StoragePoolID,
			"cache_pool_id":CachePoolID,
			"cache_mode":$("#selCacheMode").val(),
			'force_nonempty': $("#chkForceNonempty")[0].checked,
			"options":{
				"hit_set_type":"",
				'hit_set_count':"",
				'hit_set_period_s':"",
				'target_max_mem_mb':"",
				'target_dirty_ratio':"",
				'target_full_ratio':"",
				'target_max_objects':"",
				'target_min_flush_age_m':"",
				'target_min_evict_age_m':"",
			}
		}
	}

	if($("#chkForceNonempty")[0].checked == true){
		data.cache_tier.options.hit_set_type = $("#selHitSetType").val();
		data.cache_tier.options.hit_set_count = $("#txtHitSetCount").val();
		data.cache_tier.options.hit_set_period_s = $("#txtHitSetPeriod").val();
		data.cache_tier.options.target_max_mem_mb = $("#txtTargetMaximumMemory").val();
		data.cache_tier.options.target_dirty_ratio = $("#txtTargetDirtyRatio").val();
		data.cache_tier.options.target_full_ratio = $("#txtTargetFullRatio").val();
		data.cache_tier.options.target_max_objects = $("#txtTargetMaximumObjects").val();
		data.cache_tier.options.target_min_flush_age_m = $("#txtTargetMinimumFlushAge").val();
		data.cache_tier.options.target_min_evict_age_m = $("#txtTargetMinimumEvictAge").val();
	}
	
	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();
	console.log(token)
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/poolsmanagement/add_cache_tier_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				window.location.href="/dashboard/vsm/poolsmanagement/";
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				if(XMLHttpRequest.status == 500)
                	showTip("error","INTERNAL SERVER ERROR")
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
})