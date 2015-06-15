$(function(){
	InitCtrlCSS();
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
}

$("#btnAddCacheTier").click(function(){
	var CachePoolID = $("#id_cache_tier_pool").val();
	var StoragePoolID = $("#id_storage_tier_pool").val();

	if(CachePoolID == StoragePoolID){
		showTip("error","Failed to add cache tier: cache_pool, storage_pool cannot be the same!")
		return  false;
	}

	var data = {
		"cache_tier":{
			"storage_pool_id":StoragePoolID,
			"cache_pool_id":CachePoolID,
			"cache_mode":$("#id_cache_mode").val(),
			'force_nonempty': $("#id_force_nonempty")[0].checked,
			"options":{
				"hit_set_type":$("#id_hit_set_type").val(),
				'hit_set_count':$("#id_hit_set_count").val(),
				'hit_set_period_s':$("#id_hit_set_period_s").val(),
				'target_max_mem_mb':$("#id_target_max_mem_mb").val(),
				'target_dirty_ratio':$("#id_target_dirty_ratio").val(),
				'target_full_ratio':$("#id_target_full_ratio").val(),
				'target_max_objects':$("#id_target_max_objects").val(),
				'target_min_flush_age_m':$("#id_target_min_flush_age_m").val(),
				'target_min_evict_age_m':$("#id_target_min_evict_age_m").val(),
			}
		}
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
				showTip("error","Some error")
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
})

$("#btnRemoveCacheTier").click(function(){
	var CachePoolID = $("#id_cache_tier_pool").val();
	var data = {
       	'cache_tier': {
            'cache_pool_id': CachePoolID
        }
    }

    var postData = JSON.stringify(data);
    token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/poolsmanagement/remove_cache_tier_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				window.location.href="/dashboard/vsm/poolsmanagement/";
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				showTip("error","Some error")
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });

    return false;
})


$("#btnAddReplicatedPool").click(function(){
	var data = {
			"pool":{
				"name":$("#id_name").val(),
				"storageGroupId":$("#id_storage_group").val(),
				"replicatedStorageGroupId":$("#id_replicated_storage_group").val(),
				'replicationFactor': $("#id_replication_factor").val(),
				'max_pg_num_per_osd': $("#id_max_pg_num_per_osd").val(),
				'tag': $("#id_tag").val(),
				'clusterId': "0",
				'createdBy': "VSM",
				'enablePoolQuota': $("#id_enable_pool_quota")[0].checked,
				'poolQuota': $("#id_pool_quota").val(),
			}
	}

	var postData = JSON.stringify(data);
    token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/poolsmanagement/create_replicated_pool_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				window.location.href="/dashboard/vsm/poolsmanagement/";
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				showTip("error","Some error")
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });
});

$("#btnCreateErasureCodedPool").click(function(){
	var data = {
		"pool": {
            'name': $("#id_name").val(),
            'storageGroupId': $("#id_storage_group").val(),
            'tag': $("#id_tag").val(),
            'clusterId': '0',
            'createdBy': 'VSM',
            'ecProfileId': $("#id_ec_profile").val(),
            'ecFailureDomain': $("#id_ec_failure_domain").val(),
            'enablePoolQuota': $("#id_enable_pool_quota")[0].checked,
            'poolQuota': $("#id_pool_quota").val(),
        }
	}

	var postData = JSON.stringify(data);
    token = $("input[name=csrfmiddlewaretoken]").val();
	$.ajax({
		type: "post",
		url: "/dashboard/vsm/poolsmanagement/create_ec_pool_action/",
		data: postData,
		dataType:"json",
		success: function(data){
				console.log(data);
				window.location.href="/dashboard/vsm/poolsmanagement/";
		   	},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
				showTip("error","Some error")
			},
		headers: {
			"X-CSRFToken": token
			},
		complete: function(){

		}
    });

});