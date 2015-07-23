
$(document).ready(function(){
	InitCSS();
});

function InitCSS() {
	$(".help-block").remove();

	var ctrlText = $("input[type='text']");
	for (var i = 0; i < ctrlText.length; i++) {
		ctrlText[i].className = "form-control";
	}

	var ctrlText = $("input[type='password']");
	for (var i = 0; i < ctrlText.length; i++) {
		ctrlText[i].className = "form-control";
	}

	$(".form-control-feedback.glyphicon.glyphicon-eye-open").hide();
}