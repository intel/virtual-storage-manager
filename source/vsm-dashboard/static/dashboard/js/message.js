//info warning success error
function showMessage(tag,message){
	var style = "alert-info";
	switch(tag){}{
		case "info":
			style = "alert-info";
			break;
		case "warning":
			style = "alert-warning";
			break;
		case "success":
			style = "alert-success";
			break;
		case "error":
			style = "alert-error";
			break;
	}
	var html = " <div class='alert alert-block "+style+" fade in>";
    html += "<a class='close' data-dismiss='alert' href='#''>&times;</a>";
    html += "<p><strong>"+message+"<strong/></p>";
    html += "</div>";

    $(".messages")[0].innerHTML(html);
}