$(".update").click(function(){
 	token = $("input[name=csrfmiddlewaretoken]").val();

 	var trID = $(this).parent().parent()[0].id;
    var keyName = $(this).parent().parent().attr('name');
    var keyValue = $(this).parent().parent().find('.new_value').val();
    var strJSONData = JSON.stringify({"keyName":keyName,"keyValue":keyValue});

    $.ajax({
        data: strJSONData,
        type: "post",
        dataType: "json",
        url: "/dashboard/vsm/settings/update",
        success: function (data) {
            if(data.status == "success"){
            	$("#"+trID)[0].children[1].innerHTML = keyValue;
                showTip("success","set "+keyName+"="+keyValue+" successfully");
            }
            else{
                showTip("error","set "+keyName+"="+keyValue+" error");
            }
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
             showTip("error","set "+keyName+"="+keyValue+" error");
        },
        headers: {
          "X-CSRFToken": token
        },
        complete: function(){

        }
    });
});


