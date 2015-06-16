/**
 * Created by root on 15-6-17.
 */
$(function(){
	//load css
	InitCtrlCSS();
})

function InitCtrlCSS(){
	var ctrlText = $("input[type='password']");
	for(var i=0;i<ctrlText.length;i++){
		ctrlText[i].className = "form-control";
	}
}

$("#btnUpdateUser").click(function(){
	var pwd = $("#id_password").val();
	var confirm_pwd = $("#id_confirm_password").val();

	//Check the password
	if(CheckPwdReg(pwd,confirm_pwd) == false){
		return false;
	}

	//Send the pwd and update
	var data = {
		"id":$("#id_id").val(),
		"pwd":pwd
	}
	var postData = JSON.stringify(data);
	token = $("input[name=csrfmiddlewaretoken]").val();

	$.ajax({
		type: "post",
		url: "/dashboard/vsm/usermgmt/update_pwd/",
		data: postData,
		dataType:"json",
		success: function(data){
			console.log(data);
			window.location.href="/dashboard/vsm/usermgmt/";
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

function CheckPwdReg(pwd,confirm_pwd){
	$("#divWarningInfo").empty();
	$("#divWarningInfo").hide();

	//the password should not empty
	if(pwd.length == 0 || confirm_pwd.length == 0){
		$("#divWarningInfo").show();
  		$("#divWarningInfo")[0].innerHTML = "Password is empty.";
  		return false;
	}

	//Comfirm the password
	if(pwd!=confirm_pwd){
  		$("#divWarningInfo").show();
  		$("#divWarningInfo")[0].innerHTML = "Passwords do not match.";
  		return false;
    }

	var pwdCharList = pwd.split("");
	console.log(pwdCharList);

	//check the password character length
	var IsLengthOK = false;
	if(pwdCharList.length>=8){
		IsLengthOK = true;
	}

	//Check number
	var IsNumOK = false;
	var numReg = new RegExp("^[0-9]*$");
	for(var i=0;i<pwdCharList.length;i++){
		if(numReg.test(pwdCharList[i])){
			IsNumOK = true;
			break;
		}
	}

	//check uppercase character:
	//^[A-Z]+ means a string
	var IsUppercaseOK = false;
	var uppercaseReg = new RegExp("^[A-Z]$");
	for(var i=0;i<pwdCharList.length;i++){
		if(uppercaseReg.test(pwdCharList[i])){
			IsUppercaseOK = true;
			break;
		}
	}

	//check the special character:
	//@#$%^&*().:;~\|[]{}
	var IsSpecialOK = false;
	var specialCharList = ["@","#","$","%","^","&","*","()",".",":",";","~","\\",".","|","[","]","{","}"];
	console.log(specialCharList);
	for(var i=0;i<pwdCharList.length;i++){
		var pwdChar = pwdCharList[i];
		for(var j=0;j<specialCharList.length;j++){
			if(pwdChar == specialCharList[j]){
				IsSpecialOK = true;
			}
		}

		if(IsSpecialOK == true){
			break;
		}
	}

	var warningInfo = "";
	if(IsLengthOK == false){
		warningInfo +="The password should contain at least 8 characters<br>";
	}

	if(IsNumOK == false){
		warningInfo +="The password should contain at least a number.<br>";
	}

	if(IsUppercaseOK == false){
		warningInfo +="The password should contain at least a uppercase character.<br>";
	}

	if(IsSpecialOK == false){
		warningInfo +="The password should contain at least a special character.<br>";
	}

	if(warningInfo.length != 0){
		$("#divWarningInfo").show();
  		$("#divWarningInfo")[0].innerHTML = warningInfo;
  		return false;
	}

	return true;
}