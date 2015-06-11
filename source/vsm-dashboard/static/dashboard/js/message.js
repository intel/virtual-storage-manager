function showTip(tag,msg){
	var style = "alert-info";
	switch(tag){
		case "info":
			style="alert-info"
			break;
		case "warning":
			style="alert-warning"
			break;
		case "success":
			style="alert-success"
			break;
		case "error":
			style="alert-danger "
			break;
	}

	var html = "";
	html += "<div class='alert " + style + " fade in'>";
	html += "	<button type='button' class='close' data-dismiss='alert' aria-label='Close'>";
	html += "		<span aria-hidden='true'>&times;</span>";
	html += "	</button>";
	html += " 	<p><strong>";
	html += msg;
	html += "	</strong><p>";
	html += "</div>";
	$(".messages").append(html);
}


function showMessage (tag,msg) {
	var style = "alert-info";
	switch(tag){
		case "info":
			style="alert-info"
			break;
		case "warning":
			style="alert-warning"
			break;
		case "success":
			style="alert-success"
			break;
		case "error":
			style="alert-danger "
			break;
	}

	var html = "";
	html += "<div class='alert " + style +" alert-dismissible fade in' role='alert'>";
    html += "	<button type='button' class='close' data-dismiss='alert' aria-label='Close'>";
    html += "		<span aria-hidden='true'>x</span>";
    html += "	</button>";
    html += msg;
    html += "</div>";

  	return html;
}