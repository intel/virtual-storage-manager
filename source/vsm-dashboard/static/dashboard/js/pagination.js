//function searchToObject(){
//    var pairs = window.location.search.substring(1).split("&");
//    var obj = {};
//    var pair, i;
//    for(i in pairs){
//        if(paris[i] === "")continue;
//        pair = pairs[i].split("=");
//        obj[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1]);
//    }
//    return obj;
//}

var back = "";

if(window.location.search){
    //document.body.scrollTop = 9999;
    //var search = searchToObject();
    back = "<a href='javascript:history.back(-1)'>back</a>&nbsp;&nbsp;";
}
var marker = $('#rbd_list tbody tr').last().find('td').first().html();
var next_page_url = location.pathname + "?marker=" + marker;
if(marker > 0) {
    $("tfoot tr td").append("<div class='page'>" + back + "<a href='" + next_page_url + "'>next</a></div>");
} else if(marker == "No items to display.") {
    $("tfoot tr td").append("<div class='page'>" + back + "</div>");
}