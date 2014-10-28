
/* Copyright 2014 Intel Corporation, All Rights Reserved.

 Licensed under the Apache License, Version 2.0 (the"License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing,
 software distributed under the License is distributed on an
 "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 KIND, either express or implied. See the License for the
 specific language governing permissions and limitations
 under the License.
 */

var Horizon=function(){var horizon={},initFunctions=[];horizon.addInitFunction=function(fn){initFunctions.push(fn);};horizon.init=function(){for(var i=0;i<initFunctions.length;i+=1){initFunctions[i]();}
initFunctions=[];};return horizon;};var horizon=new Horizon();horizon.conf={debug:null,static_url:null,ajax:{queue_limit:null},spinner_options:{inline:{lines:10,length:5,width:2,radius:3,color:'#000',speed:0.8,trail:50,zIndex:100},modal:{lines:10,length:15,width:4,radius:10,color:'#000',speed:0.8,trail:50}}};horizon.conf.debug=false;horizon.conf.static_url="/static/";horizon.conf.ajax={queue_limit:10};horizon.conf.auto_fade_alerts={delay:3000,fade_duration:1500,types:['alert-success','alert-info']};