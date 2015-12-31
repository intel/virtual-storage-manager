function GenerateDialog(title,body,showSubmit,submitName){
	var html = "";
	html += "<div class='modal-dialog' style='z-index:1045'>";
	html += "	<div class='modal-content' >";
	html += "		<div class='modal-header'>";
	html += "			<button type='button' class='close' data-dismiss='modal' aria-label='Close'><span aria-hidden='true'>&times;</span></button>";
	html += "			<h4 class='modal-title' id='myModalLabel'>";
	html += title;
	html += "			</h4>";
	html += "		</div>";
	html += "		<div class='modal-body'>";
	html += body;
	html += "		</div>";
	html += "		<div class='modal-footer'>";
	html += "			<button id='btnDialogCancel' type='button' class='btn btn-default' data-dismiss='modal'>Close</button>";
	
	if(showSubmit==true){
		html += "<button id='btnDialogSubmit' type='button' class='btn btn-primary'>";
		html += submitName;
		html += "</button>";
	}
		
	html += "		</div>";
	html += "	</div>";
	html += "</div>";


	var dialogWrapper = $("#modal_wrapper")[0];
	dialogWrapper.id = "modal_wrapper";
	dialogWrapper.className = "modal";
	dialogWrapper.innerHTML = html;

	return $("#modal_wrapper");
}
