//flag the tab
var _CURRENT_TAB = "";

$(function(){
    //InitCtrlCSS();
    //_CURRENT_TAB = $(".nav-tabs>li>a")[0].innerHTML;
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

function SwitchTab(obj,tabname){
    //flag the tab
    _CURRENT_TAB = tabname;

    //show the current table
    $(".table-config").hide();
    $("#t"+tabname).show();

    //change the current section
    $(".nav-tabs>li").each(function(){
        this.className = "";
    })
    obj.className = "active";
}

function SelectAllCheckbox(obj,name){
    var checked = obj.checked;
    $("input[name="+name+"]").each(function(){
        this.checked = checked;
    })
}

$("#btnCreateConfiguration").click(function(){
    //Check the field is should not null
    if(   $("#id_name").val() == ""
       || $("#id_section").val() == ""
       || $("#id_default_value").val() == ""
       || $("#id_current_value").val() == "" ){
        showTip("error","The field is marked as '*' should not be empty");
        return  false;
    }

    var postData = {
        "name":$("#id_name").val(),
        "section":$("#id_section").val(),
        "default_value":$("#id_default_value").val(),
        "current_value":$("#id_current_value").val(),
    }

    //execuate post
    Post("create_action",postData);
})

$("#btnUpdateConfiguration").click(function(){
     //Check the field is should not null
    if(   $("#id_name").val() == ""
       || $("#id_section").val() == ""
       || $("#id_default_value").val() == ""
       || $("#id_current_value").val() == "" ){
        showTip("error","The field is marked as '*' should not be empty");
        return  false;
    }

    var postData = {
        "id":$("#hfConfigID").val(),
        "name":$("#id_name").val(),
        "section":$("#id_section").val(),
        "default_value":$("#id_default_value").val(),
        "current_value":$("#id_current_value").val(),
    }

    //execuate post
    Post("update_action",postData);
});


function DeleteConfig(section_name){
    var config_id_list = [];
    $("input[name="+_CURRENT_TAB+"]").each(function(){
        if(this.checked == true){
            if(this.value!="on")
                config_id_list.push(this.value);
        }
    }); 

    //execuate post
    Post("delete_action",config_id_list);  
}


function Post(method,data){
    token = $("input[name=csrfmiddlewaretoken]").val();
    $.ajax({
        data: JSON.stringify(data),
        type: "post",
        dataType: "json",
        url: "/dashboard/vsm/configuration/"+method+"/",
        success: function (data) {
            if(data.status == "OK"){
                window.location.href="/dashboard/vsm/configuration/";
            }
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
}

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

$(".enable_or_disable").click(function(){
    //console.log('clicked checkbox:', this);
    if (this.checked){
        this.parentNode.children[0].value = 0;
        this.parentNode.children[0].disabled= true;
    }
    else{
        this.parentNode.children[0].value = this.parentNode.parentNode.children[1].innerHTML;
        this.parentNode.children[0].disabled = false;
    }
});




