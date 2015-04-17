(function(){'use strict';horizonApp.controller('DummyCtrl',function(){});}());(function(){'use strict';horizonApp.directive('notBlank',function(){return{require:'ngModel',link:function(scope,elm,attrs,ctrl){ctrl.$parsers.unshift(function(viewValue){if(viewValue.length){ctrl.$setValidity('notBlank',true);return viewValue;}
ctrl.$setValidity('notBlank',false);return undefined;});}};});}());(function(){'use strict';angular.module('hz.conf',[]).constant('hzConfig',{debug:null,static_url:null,ajax:{queue_limit:null},spinner_options:{inline:{lines:10,length:5,width:2,radius:3,color:'#000',speed:0.8,trail:50,zIndex:100},modal:{lines:10,length:15,width:4,radius:10,color:'#000',speed:0.8,trail:50},line_chart:{lines:10,length:15,width:4,radius:11,color:'#000',speed:0.8,trail:50}}});}());(function(){'use strict';function utils(hzConfig,$log,$rootScope,$compile){return{log:function(msg,lvl){if(hzConfig.debug){($log[lvl]||$log.log)(msg);}},capitalize:function(string){return string.charAt(0).toUpperCase()+string.slice(1);},humanizeNumbers:function(number){return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g,",");},truncate:function(string,size,includeEllipsis){if(string.length>size){if(includeEllipsis){return string.substring(0,(size-3))+"&hellip;";}
return string.substring(0,size);}
return string;},loadAngular:function(element){try{$compile(element)($rootScope);$rootScope.$apply();}catch(err){}}};}
angular.module('hz.utils.hzUtils',['hz.conf']).service('hzUtils',['hzConfig','$log','$rootScope','$compile',utils]);angular.module('hz.utils',['hz.utils.hzUtils']);}());(function(){'use strict';horizonApp.controller('hzMetadataWidgetCtrl',['$scope','$window','$filter',function($scope,$window,$filter){function Item(parent){Object.defineProperty(this,'parent',{value:typeof parent!=='undefined'?parent:null});this.children=[];this.visible=false;this.expanded=false;this.label='';this.description='';this.level=parent?parent.level+1:0;this.addedCount=0;this.custom=false;this.leaf=null;this.added=false;}
Item.prototype.fromNamespace=function(namespace){this.label=namespace.display_name;this.description=namespace.description;if(namespace.objects){angular.forEach(namespace.objects,function(object){this.children.push(new Item(this).fromObject(object));},this);}
if(namespace.properties){angular.forEach(namespace.properties,function(property,key){this.children.push(new Item(this).fromProperty(key,property));},this);}
this.sortChildren();return this;};Item.prototype.fromObject=function(object){this.label=object.name;this.description=object.description;if(object.properties){angular.forEach(object.properties,function(property,key){this.children.push(new Item(this).fromProperty(key,property));},this);}
this.sortChildren();return this;};Item.prototype.fromProperty=function(name,property){this.leaf=property||{};this.label=this.leaf.title||'';this.description=this.leaf.description||'';this.leaf.name=name;this.leaf.value=this.leaf.default||null;return this;};Item.prototype.customProperty=function(name){this.fromProperty(name,{title:name});this.leaf.type='string';this.custom=true;return this;};Item.prototype.expand=function(){this.expanded=true;angular.forEach(this.children,function(child){child.visible=true;},this);};Item.prototype.collapse=function(){this.expanded=false;angular.forEach(this.children,function(child){child.collapse();child.visible=false;},this);};Item.prototype.sortChildren=function(){this.children.sort(function(a,b){return a.label.localeCompare(b.label);});};Item.prototype.markAsAdded=function(){this.added=true;if(this.parent){this.parent.addedCount+=1;if(this.parent.addedCount===this.parent.children.length){this.parent.added=true;}}
angular.forEach(this.children,function(item){item.markAsAdded();},this);};Item.prototype.unmarkAsAdded=function(caller){this.added=false;if(this.parent){this.parent.addedCount-=1;this.parent.expand();this.parent.unmarkAsAdded(this);}
if(!caller){angular.forEach(this.children,function(item){item.unmarkAsAdded();},this);}};Item.prototype.path=function(path){path=typeof path!=='undefined'?path:[];if(this.parent)this.parent.path(path);path.push(this.label);return path;};var filter=$filter('filter');function loadNamespaces(namespaces){var items=[];angular.forEach(namespaces,function(namespace){var item=new Item().fromNamespace(namespace);item.visible=true;items.push(item);});items.sort(function(a,b){return a.label.localeCompare(b.label);});return items;}
function flattenTree(tree,items){items=typeof items!=='undefined'?items:[];angular.forEach(tree,function(item){items.push(item);flattenTree(item.children,items);});return items;}
function loadExisting(available,existing){var itemsMapping={};angular.forEach(available,function(item){if(item.leaf&&item.leaf.name in existing){itemsMapping[item.leaf.name]=item;}});angular.forEach(existing,function(value,key){var item=itemsMapping[key];if(typeof item==='undefined'){item=new Item().customProperty(key);available.push(item);}
switch(item.leaf.type){case'integer':item.leaf.value=parseInt(value);break;case'number':item.leaf.value=parseFloat(value);break;case'array':item.leaf.value=value.replace(/^<in> /,'');break;default:item.leaf.value=value;}
item.markAsAdded();});}
$scope.onItemClick=function(e,item){$scope.selected=item;if(!item.expanded){item.expand();}else{item.collapse();}};$scope.onItemAdd=function(e,item){$scope.selected=item;item.markAsAdded();};$scope.onItemDelete=function(e,item){if(!item.custom){$scope.selected=item;item.unmarkAsAdded();}else{$scope.selected=null;var i=$scope.flatTree.indexOf(item);if(i>-1){$scope.flatTree.splice(i,1);}}};$scope.onCustomItemAdd=function(e){var item,name=$scope.customItem.value;if($scope.customItem.found.length>0){item=$scope.customItem.found[0];item.markAsAdded();$scope.selected=item;}else{item=new Item().customProperty(name);item.markAsAdded();$scope.selected=item;$scope.flatTree.push(item);}
$scope.customItem.valid=false;$scope.customItem.value='';};$scope.formatErrorMessage=function(item,error){var _=$window.gettext;if(error.min)return _('Min')+' '+item.leaf.minimum;if(error.max)return _('Max')+' '+item.leaf.maximum;if(error.minlength)return _('Min length')+' '+item.leaf.minLength;if(error.maxlength)return _('Max length')+' '+item.leaf.maxLength;if(error.pattern){if(item.leaf.type==='integer')return _('Integer required');else return _('Pattern mismatch');}
if(error.required){switch(item.leaf.type){case'integer':return _('Integer required');case'number':return _('Decimal required');default:return _('Required');}}};$scope.saveMetadata=function(){var metadata=[];var added=filter($scope.flatTree,{'added':true,'leaf':'!!'});angular.forEach(added,function(item){metadata.push({key:item.leaf.name,value:(item.leaf.type=='array'?'<in> ':'')+item.leaf.value});});$scope.metadata=JSON.stringify(metadata);};$scope.$watch('customItem.value',function(){$scope.customItem.found=filter($scope.flatTree,{'leaf.name':$scope.customItem.value},true);$scope.customItem.valid=$scope.customItem.value&&$scope.customItem.found.length===0;});var tree=loadNamespaces($window.available_metadata.namespaces);$scope.flatTree=flattenTree(tree);$scope.decriptionText='';$scope.metadata='';$scope.selected=null;$scope.customItem={value:'',focused:false,valid:false,found:[]};loadExisting($scope.flatTree,$window.existing_metadata);}]);}());;(function($){var bootstrapWizardCreate=function(element,options){var element=$(element);var obj=this;var baseItemSelector='li:has([data-toggle="tab"])';var $settings=$.extend({},$.fn.bootstrapWizard.defaults,options);var $activeTab=null;var $navigation=null;this.rebindClick=function(selector,fn)
{selector.unbind('click',fn).bind('click',fn);}
this.fixNavigationButtons=function(){if(!$activeTab.length){$navigation.find('a:first').tab('show');$activeTab=$navigation.find(baseItemSelector+':first');}
$($settings.previousSelector,element).toggleClass('disabled',(obj.firstIndex()>=obj.currentIndex()));$($settings.nextSelector,element).toggleClass('disabled',(obj.currentIndex()>=obj.navigationLength()));obj.rebindClick($($settings.nextSelector,element),obj.next);obj.rebindClick($($settings.previousSelector,element),obj.previous);obj.rebindClick($($settings.lastSelector,element),obj.last);obj.rebindClick($($settings.firstSelector,element),obj.first);if($settings.onTabShow&&typeof $settings.onTabShow==='function'&&$settings.onTabShow($activeTab,$navigation,obj.currentIndex())===false){return false;}};this.next=function(e){if(element.hasClass('last')){return false;}
if($settings.onNext&&typeof $settings.onNext==='function'&&$settings.onNext($activeTab,$navigation,obj.nextIndex())===false){return false;}
$index=obj.nextIndex();if($index>obj.navigationLength()){}else{$navigation.find(baseItemSelector+':eq('+$index+') a').tab('show');}};this.previous=function(e){if(element.hasClass('first')){return false;}
if($settings.onPrevious&&typeof $settings.onPrevious==='function'&&$settings.onPrevious($activeTab,$navigation,obj.previousIndex())===false){return false;}
$index=obj.previousIndex();if($index<0){}else{$navigation.find(baseItemSelector+':eq('+$index+') a').tab('show');}};this.first=function(e){if($settings.onFirst&&typeof $settings.onFirst==='function'&&$settings.onFirst($activeTab,$navigation,obj.firstIndex())===false){return false;}
if(element.hasClass('disabled')){return false;}
$navigation.find(baseItemSelector+':eq(0) a').tab('show');};this.last=function(e){if($settings.onLast&&typeof $settings.onLast==='function'&&$settings.onLast($activeTab,$navigation,obj.lastIndex())===false){return false;}
if(element.hasClass('disabled')){return false;}
$navigation.find(baseItemSelector+':eq('+obj.navigationLength()+') a').tab('show');};this.currentIndex=function(){return $navigation.find(baseItemSelector).index($activeTab);};this.firstIndex=function(){return 0;};this.lastIndex=function(){return obj.navigationLength();};this.getIndex=function(e){return $navigation.find(baseItemSelector).index(e);};this.nextIndex=function(){return $navigation.find(baseItemSelector).index($activeTab)+1;};this.previousIndex=function(){return $navigation.find(baseItemSelector).index($activeTab)-1;};this.navigationLength=function(){return $navigation.find(baseItemSelector).length-1;};this.activeTab=function(){return $activeTab;};this.nextTab=function(){return $navigation.find(baseItemSelector+':eq('+(obj.currentIndex()+1)+')').length?$navigation.find(baseItemSelector+':eq('+(obj.currentIndex()+1)+')'):null;};this.previousTab=function(){if(obj.currentIndex()<=0){return null;}
return $navigation.find(baseItemSelector+':eq('+parseInt(obj.currentIndex()-1)+')');};this.show=function(index){return element.find(baseItemSelector+':eq('+index+') a').tab('show');};this.disable=function(index){$navigation.find(baseItemSelector+':eq('+index+')').addClass('disabled');};this.enable=function(index){$navigation.find(baseItemSelector+':eq('+index+')').removeClass('disabled');};this.hide=function(index){$navigation.find(baseItemSelector+':eq('+index+')').hide();};this.display=function(index){$navigation.find(baseItemSelector+':eq('+index+')').show();};this.remove=function(args){var $index=args[0];var $removeTabPane=typeof args[1]!='undefined'?args[1]:false;var $item=$navigation.find(baseItemSelector+':eq('+$index+')');if($removeTabPane){var $href=$item.find('a').attr('href');$($href).remove();}
$item.remove();};var innerTabClick=function(e){var clickedIndex=$navigation.find(baseItemSelector).index($(e.currentTarget).parent(baseItemSelector));if($settings.onTabClick&&typeof $settings.onTabClick==='function'&&$settings.onTabClick($activeTab,$navigation,obj.currentIndex(),clickedIndex)===false){return false;}};var innerTabShown=function(e){$element=$(e.target).parent();var nextTab=$navigation.find(baseItemSelector).index($element);if($element.hasClass('disabled')){return false;}
if($settings.onTabChange&&typeof $settings.onTabChange==='function'&&$settings.onTabChange($activeTab,$navigation,obj.currentIndex(),nextTab)===false){return false;}
$activeTab=$element;obj.fixNavigationButtons();};this.resetWizard=function(){$('a[data-toggle="tab"]',$navigation).off('click',innerTabClick);$('a[data-toggle="tab"]',$navigation).off('shown shown.bs.tab',innerTabShown);$navigation=element.find('ul:first',element);$activeTab=$navigation.find(baseItemSelector+'.active',element);$('a[data-toggle="tab"]',$navigation).on('click',innerTabClick);$('a[data-toggle="tab"]',$navigation).on('shown shown.bs.tab',innerTabShown);obj.fixNavigationButtons();};$navigation=element.find('ul:first',element);$activeTab=$navigation.find(baseItemSelector+'.active',element);if(!$navigation.hasClass($settings.tabClass)){$navigation.addClass($settings.tabClass);}
if($settings.onInit&&typeof $settings.onInit==='function'){$settings.onInit($activeTab,$navigation,0);}
if($settings.onShow&&typeof $settings.onShow==='function'){$settings.onShow($activeTab,$navigation,obj.nextIndex());}
$('a[data-toggle="tab"]',$navigation).on('click',innerTabClick);$('a[data-toggle="tab"]',$navigation).on('shown shown.bs.tab',innerTabShown);};$.fn.bootstrapWizard=function(options){if(typeof options=='string'){var args=Array.prototype.slice.call(arguments,1)
if(args.length===1){args.toString();}
return this.data('bootstrapWizard')[options](args);}
return this.each(function(index){var element=$(this);if(element.data('bootstrapWizard'))return;var wizard=new bootstrapWizardCreate(element,options);element.data('bootstrapWizard',wizard);wizard.fixNavigationButtons();});};$.fn.bootstrapWizard.defaults={tabClass:'nav nav-pills',nextSelector:'.wizard li.next',previousSelector:'.wizard li.previous',firstSelector:'.wizard li.first',lastSelector:'.wizard li.last',onShow:null,onInit:null,onNext:null,onPrevious:null,onLast:null,onFirst:null,onTabChange:null,onTabClick:null,onTabShow:null};})(jQuery);+function($){'use strict';var Affix=function(element,options){this.options=$.extend({},Affix.DEFAULTS,options)
this.$target=$(this.options.target).on('scroll.bs.affix.data-api',$.proxy(this.checkPosition,this)).on('click.bs.affix.data-api',$.proxy(this.checkPositionWithEventLoop,this))
this.$element=$(element)
this.affixed=this.unpin=this.pinnedOffset=null
this.checkPosition()}
Affix.VERSION='3.2.0'
Affix.RESET='affix affix-top affix-bottom'
Affix.DEFAULTS={offset:0,target:window}
Affix.prototype.getPinnedOffset=function(){if(this.pinnedOffset)return this.pinnedOffset
this.$element.removeClass(Affix.RESET).addClass('affix')
var scrollTop=this.$target.scrollTop()
var position=this.$element.offset()
return(this.pinnedOffset=position.top-scrollTop)}
Affix.prototype.checkPositionWithEventLoop=function(){setTimeout($.proxy(this.checkPosition,this),1)}
Affix.prototype.checkPosition=function(){if(!this.$element.is(':visible'))return
var scrollHeight=$(document).height()
var scrollTop=this.$target.scrollTop()
var position=this.$element.offset()
var offset=this.options.offset
var offsetTop=offset.top
var offsetBottom=offset.bottom
if(typeof offset!='object')offsetBottom=offsetTop=offset
if(typeof offsetTop=='function')offsetTop=offset.top(this.$element)
if(typeof offsetBottom=='function')offsetBottom=offset.bottom(this.$element)
var affix=this.unpin!=null&&(scrollTop+this.unpin<=position.top)?false:offsetBottom!=null&&(position.top+this.$element.height()>=scrollHeight-offsetBottom)?'bottom':offsetTop!=null&&(scrollTop<=offsetTop)?'top':false
if(this.affixed===affix)return
if(this.unpin!=null)this.$element.css('top','')
var affixType='affix'+(affix?'-'+affix:'')
var e=$.Event(affixType+'.bs.affix')
this.$element.trigger(e)
if(e.isDefaultPrevented())return
this.affixed=affix
this.unpin=affix=='bottom'?this.getPinnedOffset():null
this.$element.removeClass(Affix.RESET).addClass(affixType).trigger($.Event(affixType.replace('affix','affixed')))
if(affix=='bottom'){this.$element.offset({top:scrollHeight-this.$element.height()-offsetBottom})}}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.affix')
var options=typeof option=='object'&&option
if(!data)$this.data('bs.affix',(data=new Affix(this,options)))
if(typeof option=='string')data[option]()})}
var old=$.fn.affix
$.fn.affix=Plugin
$.fn.affix.Constructor=Affix
$.fn.affix.noConflict=function(){$.fn.affix=old
return this}
$(window).on('load',function(){$('[data-spy="affix"]').each(function(){var $spy=$(this)
var data=$spy.data()
data.offset=data.offset||{}
if(data.offsetBottom)data.offset.bottom=data.offsetBottom
if(data.offsetTop)data.offset.top=data.offsetTop
Plugin.call($spy,data)})})}(jQuery);+function($){'use strict';var dismiss='[data-dismiss="alert"]'
var Alert=function(el){$(el).on('click',dismiss,this.close)}
Alert.VERSION='3.2.0'
Alert.prototype.close=function(e){var $this=$(this)
var selector=$this.attr('data-target')
if(!selector){selector=$this.attr('href')
selector=selector&&selector.replace(/.*(?=#[^\s]*$)/,'')}
var $parent=$(selector)
if(e)e.preventDefault()
if(!$parent.length){$parent=$this.hasClass('alert')?$this:$this.parent()}
$parent.trigger(e=$.Event('close.bs.alert'))
if(e.isDefaultPrevented())return
$parent.removeClass('in')
function removeElement(){$parent.detach().trigger('closed.bs.alert').remove()}
$.support.transition&&$parent.hasClass('fade')?$parent.one('bsTransitionEnd',removeElement).emulateTransitionEnd(150):removeElement()}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.alert')
if(!data)$this.data('bs.alert',(data=new Alert(this)))
if(typeof option=='string')data[option].call($this)})}
var old=$.fn.alert
$.fn.alert=Plugin
$.fn.alert.Constructor=Alert
$.fn.alert.noConflict=function(){$.fn.alert=old
return this}
$(document).on('click.bs.alert.data-api',dismiss,Alert.prototype.close)}(jQuery);+function($){'use strict';var Button=function(element,options){this.$element=$(element)
this.options=$.extend({},Button.DEFAULTS,options)
this.isLoading=false}
Button.VERSION='3.2.0'
Button.DEFAULTS={loadingText:'loading...'}
Button.prototype.setState=function(state){var d='disabled'
var $el=this.$element
var val=$el.is('input')?'val':'html'
var data=$el.data()
state=state+'Text'
if(data.resetText==null)$el.data('resetText',$el[val]())
$el[val](data[state]==null?this.options[state]:data[state])
setTimeout($.proxy(function(){if(state=='loadingText'){this.isLoading=true
$el.addClass(d).attr(d,d)}else if(this.isLoading){this.isLoading=false
$el.removeClass(d).removeAttr(d)}},this),0)}
Button.prototype.toggle=function(){var changed=true
var $parent=this.$element.closest('[data-toggle="buttons"]')
if($parent.length){var $input=this.$element.find('input')
if($input.prop('type')=='radio'){if($input.prop('checked')&&this.$element.hasClass('active'))changed=false
else $parent.find('.active').removeClass('active')}
if(changed)$input.prop('checked',!this.$element.hasClass('active')).trigger('change')}
if(changed)this.$element.toggleClass('active')}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.button')
var options=typeof option=='object'&&option
if(!data)$this.data('bs.button',(data=new Button(this,options)))
if(option=='toggle')data.toggle()
else if(option)data.setState(option)})}
var old=$.fn.button
$.fn.button=Plugin
$.fn.button.Constructor=Button
$.fn.button.noConflict=function(){$.fn.button=old
return this}
$(document).on('click.bs.button.data-api','[data-toggle^="button"]',function(e){var $btn=$(e.target)
if(!$btn.hasClass('btn'))$btn=$btn.closest('.btn')
Plugin.call($btn,'toggle')
e.preventDefault()})}(jQuery);+function($){'use strict';var Carousel=function(element,options){this.$element=$(element).on('keydown.bs.carousel',$.proxy(this.keydown,this))
this.$indicators=this.$element.find('.carousel-indicators')
this.options=options
this.paused=this.sliding=this.interval=this.$active=this.$items=null
this.options.pause=='hover'&&this.$element.on('mouseenter.bs.carousel',$.proxy(this.pause,this)).on('mouseleave.bs.carousel',$.proxy(this.cycle,this))}
Carousel.VERSION='3.2.0'
Carousel.DEFAULTS={interval:5000,pause:'hover',wrap:true}
Carousel.prototype.keydown=function(e){switch(e.which){case 37:this.prev();break
case 39:this.next();break
default:return}
e.preventDefault()}
Carousel.prototype.cycle=function(e){e||(this.paused=false)
this.interval&&clearInterval(this.interval)
this.options.interval&&!this.paused&&(this.interval=setInterval($.proxy(this.next,this),this.options.interval))
return this}
Carousel.prototype.getItemIndex=function(item){this.$items=item.parent().children('.item')
return this.$items.index(item||this.$active)}
Carousel.prototype.to=function(pos){var that=this
var activeIndex=this.getItemIndex(this.$active=this.$element.find('.item.active'))
if(pos>(this.$items.length-1)||pos<0)return
if(this.sliding)return this.$element.one('slid.bs.carousel',function(){that.to(pos)})
if(activeIndex==pos)return this.pause().cycle()
return this.slide(pos>activeIndex?'next':'prev',$(this.$items[pos]))}
Carousel.prototype.pause=function(e){e||(this.paused=true)
if(this.$element.find('.next, .prev').length&&$.support.transition){this.$element.trigger($.support.transition.end)
this.cycle(true)}
this.interval=clearInterval(this.interval)
return this}
Carousel.prototype.next=function(){if(this.sliding)return
return this.slide('next')}
Carousel.prototype.prev=function(){if(this.sliding)return
return this.slide('prev')}
Carousel.prototype.slide=function(type,next){var $active=this.$element.find('.item.active')
var $next=next||$active[type]()
var isCycling=this.interval
var direction=type=='next'?'left':'right'
var fallback=type=='next'?'first':'last'
var that=this
if(!$next.length){if(!this.options.wrap)return
$next=this.$element.find('.item')[fallback]()}
if($next.hasClass('active'))return(this.sliding=false)
var relatedTarget=$next[0]
var slideEvent=$.Event('slide.bs.carousel',{relatedTarget:relatedTarget,direction:direction})
this.$element.trigger(slideEvent)
if(slideEvent.isDefaultPrevented())return
this.sliding=true
isCycling&&this.pause()
if(this.$indicators.length){this.$indicators.find('.active').removeClass('active')
var $nextIndicator=$(this.$indicators.children()[this.getItemIndex($next)])
$nextIndicator&&$nextIndicator.addClass('active')}
var slidEvent=$.Event('slid.bs.carousel',{relatedTarget:relatedTarget,direction:direction})
if($.support.transition&&this.$element.hasClass('slide')){$next.addClass(type)
$next[0].offsetWidth
$active.addClass(direction)
$next.addClass(direction)
$active.one('bsTransitionEnd',function(){$next.removeClass([type,direction].join(' ')).addClass('active')
$active.removeClass(['active',direction].join(' '))
that.sliding=false
setTimeout(function(){that.$element.trigger(slidEvent)},0)}).emulateTransitionEnd($active.css('transition-duration').slice(0,-1)*1000)}else{$active.removeClass('active')
$next.addClass('active')
this.sliding=false
this.$element.trigger(slidEvent)}
isCycling&&this.cycle()
return this}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.carousel')
var options=$.extend({},Carousel.DEFAULTS,$this.data(),typeof option=='object'&&option)
var action=typeof option=='string'?option:options.slide
if(!data)$this.data('bs.carousel',(data=new Carousel(this,options)))
if(typeof option=='number')data.to(option)
else if(action)data[action]()
else if(options.interval)data.pause().cycle()})}
var old=$.fn.carousel
$.fn.carousel=Plugin
$.fn.carousel.Constructor=Carousel
$.fn.carousel.noConflict=function(){$.fn.carousel=old
return this}
$(document).on('click.bs.carousel.data-api','[data-slide], [data-slide-to]',function(e){var href
var $this=$(this)
var $target=$($this.attr('data-target')||(href=$this.attr('href'))&&href.replace(/.*(?=#[^\s]+$)/,''))
if(!$target.hasClass('carousel'))return
var options=$.extend({},$target.data(),$this.data())
var slideIndex=$this.attr('data-slide-to')
if(slideIndex)options.interval=false
Plugin.call($target,options)
if(slideIndex){$target.data('bs.carousel').to(slideIndex)}
e.preventDefault()})
$(window).on('load',function(){$('[data-ride="carousel"]').each(function(){var $carousel=$(this)
Plugin.call($carousel,$carousel.data())})})}(jQuery);+function($){'use strict';var Collapse=function(element,options){this.$element=$(element)
this.options=$.extend({},Collapse.DEFAULTS,options)
this.transitioning=null
if(this.options.parent)this.$parent=$(this.options.parent)
if(this.options.toggle)this.toggle()}
Collapse.VERSION='3.2.0'
Collapse.DEFAULTS={toggle:true}
Collapse.prototype.dimension=function(){var hasWidth=this.$element.hasClass('width')
return hasWidth?'width':'height'}
Collapse.prototype.show=function(){if(this.transitioning||this.$element.hasClass('in'))return
var startEvent=$.Event('show.bs.collapse')
this.$element.trigger(startEvent)
if(startEvent.isDefaultPrevented())return
var actives=this.$parent&&this.$parent.find('> .panel > .in')
if(actives&&actives.length){var hasData=actives.data('bs.collapse')
if(hasData&&hasData.transitioning)return
Plugin.call(actives,'hide')
hasData||actives.data('bs.collapse',null)}
var dimension=this.dimension()
this.$element.removeClass('collapse').addClass('collapsing')[dimension](0)
this.transitioning=1
var complete=function(){this.$element.removeClass('collapsing').addClass('collapse in')[dimension]('')
this.transitioning=0
this.$element.trigger('shown.bs.collapse')}
if(!$.support.transition)return complete.call(this)
var scrollSize=$.camelCase(['scroll',dimension].join('-'))
this.$element.one('bsTransitionEnd',$.proxy(complete,this)).emulateTransitionEnd(350)[dimension](this.$element[0][scrollSize])}
Collapse.prototype.hide=function(){if(this.transitioning||!this.$element.hasClass('in'))return
var startEvent=$.Event('hide.bs.collapse')
this.$element.trigger(startEvent)
if(startEvent.isDefaultPrevented())return
var dimension=this.dimension()
this.$element[dimension](this.$element[dimension]())[0].offsetHeight
this.$element.addClass('collapsing').removeClass('collapse').removeClass('in')
this.transitioning=1
var complete=function(){this.transitioning=0
this.$element.trigger('hidden.bs.collapse').removeClass('collapsing').addClass('collapse')}
if(!$.support.transition)return complete.call(this)
this.$element
[dimension](0).one('bsTransitionEnd',$.proxy(complete,this)).emulateTransitionEnd(350)}
Collapse.prototype.toggle=function(){this[this.$element.hasClass('in')?'hide':'show']()}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.collapse')
var options=$.extend({},Collapse.DEFAULTS,$this.data(),typeof option=='object'&&option)
if(!data&&options.toggle&&option=='show')option=!option
if(!data)$this.data('bs.collapse',(data=new Collapse(this,options)))
if(typeof option=='string')data[option]()})}
var old=$.fn.collapse
$.fn.collapse=Plugin
$.fn.collapse.Constructor=Collapse
$.fn.collapse.noConflict=function(){$.fn.collapse=old
return this}
$(document).on('click.bs.collapse.data-api','[data-toggle="collapse"]',function(e){var href
var $this=$(this)
var target=$this.attr('data-target')||e.preventDefault()||(href=$this.attr('href'))&&href.replace(/.*(?=#[^\s]+$)/,'')
var $target=$(target)
var data=$target.data('bs.collapse')
var option=data?'toggle':$this.data()
var parent=$this.attr('data-parent')
var $parent=parent&&$(parent)
if(!data||!data.transitioning){if($parent)$parent.find('[data-toggle="collapse"][data-parent="'+parent+'"]').not($this).addClass('collapsed')
$this[$target.hasClass('in')?'addClass':'removeClass']('collapsed')}
Plugin.call($target,option)})}(jQuery);+function($){'use strict';var backdrop='.dropdown-backdrop'
var toggle='[data-toggle="dropdown"]'
var Dropdown=function(element){$(element).on('click.bs.dropdown',this.toggle)}
Dropdown.VERSION='3.2.0'
Dropdown.prototype.toggle=function(e){var $this=$(this)
if($this.is('.disabled, :disabled'))return
var $parent=getParent($this)
var isActive=$parent.hasClass('open')
clearMenus()
if(!isActive){if('ontouchstart'in document.documentElement&&!$parent.closest('.navbar-nav').length){$('<div class="dropdown-backdrop"/>').insertAfter($(this)).on('click',clearMenus)}
var relatedTarget={relatedTarget:this}
$parent.trigger(e=$.Event('show.bs.dropdown',relatedTarget))
if(e.isDefaultPrevented())return
$this.trigger('focus')
$parent.toggleClass('open').trigger('shown.bs.dropdown',relatedTarget)}
return false}
Dropdown.prototype.keydown=function(e){if(!/(38|40|27)/.test(e.keyCode))return
var $this=$(this)
e.preventDefault()
e.stopPropagation()
if($this.is('.disabled, :disabled'))return
var $parent=getParent($this)
var isActive=$parent.hasClass('open')
if(!isActive||(isActive&&e.keyCode==27)){if(e.which==27)$parent.find(toggle).trigger('focus')
return $this.trigger('click')}
var desc=' li:not(.divider):visible a'
var $items=$parent.find('[role="menu"]'+desc+', [role="listbox"]'+desc)
if(!$items.length)return
var index=$items.index($items.filter(':focus'))
if(e.keyCode==38&&index>0)index--
if(e.keyCode==40&&index<$items.length-1)index++
if(!~index)index=0
$items.eq(index).trigger('focus')}
function clearMenus(e){if(e&&e.which===3)return
$(backdrop).remove()
$(toggle).each(function(){var $parent=getParent($(this))
var relatedTarget={relatedTarget:this}
if(!$parent.hasClass('open'))return
$parent.trigger(e=$.Event('hide.bs.dropdown',relatedTarget))
if(e.isDefaultPrevented())return
$parent.removeClass('open').trigger('hidden.bs.dropdown',relatedTarget)})}
function getParent($this){var selector=$this.attr('data-target')
if(!selector){selector=$this.attr('href')
selector=selector&&/#[A-Za-z]/.test(selector)&&selector.replace(/.*(?=#[^\s]*$)/,'')}
var $parent=selector&&$(selector)
return $parent&&$parent.length?$parent:$this.parent()}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.dropdown')
if(!data)$this.data('bs.dropdown',(data=new Dropdown(this)))
if(typeof option=='string')data[option].call($this)})}
var old=$.fn.dropdown
$.fn.dropdown=Plugin
$.fn.dropdown.Constructor=Dropdown
$.fn.dropdown.noConflict=function(){$.fn.dropdown=old
return this}
$(document).on('click.bs.dropdown.data-api',clearMenus).on('click.bs.dropdown.data-api','.dropdown form',function(e){e.stopPropagation()}).on('click.bs.dropdown.data-api',toggle,Dropdown.prototype.toggle).on('keydown.bs.dropdown.data-api',toggle+', [role="menu"], [role="listbox"]',Dropdown.prototype.keydown)}(jQuery);+function($){'use strict';var Tab=function(element){this.element=$(element)}
Tab.VERSION='3.2.0'
Tab.prototype.show=function(){var $this=this.element
var $ul=$this.closest('ul:not(.dropdown-menu)')
var selector=$this.data('target')
if(!selector){selector=$this.attr('href')
selector=selector&&selector.replace(/.*(?=#[^\s]*$)/,'')}
if($this.parent('li').hasClass('active'))return
var previous=$ul.find('.active:last a')[0]
var e=$.Event('show.bs.tab',{relatedTarget:previous})
$this.trigger(e)
if(e.isDefaultPrevented())return
var $target=$(selector)
this.activate($this.closest('li'),$ul)
this.activate($target,$target.parent(),function(){$this.trigger({type:'shown.bs.tab',relatedTarget:previous})})}
Tab.prototype.activate=function(element,container,callback){var $active=container.find('> .active')
var transition=callback&&$.support.transition&&$active.hasClass('fade')
function next(){$active.removeClass('active').find('> .dropdown-menu > .active').removeClass('active')
element.addClass('active')
if(transition){element[0].offsetWidth
element.addClass('in')}else{element.removeClass('fade')}
if(element.parent('.dropdown-menu')){element.closest('li.dropdown').addClass('active')}
callback&&callback()}
transition?$active.one('bsTransitionEnd',next).emulateTransitionEnd(150):next()
$active.removeClass('in')}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.tab')
if(!data)$this.data('bs.tab',(data=new Tab(this)))
if(typeof option=='string')data[option]()})}
var old=$.fn.tab
$.fn.tab=Plugin
$.fn.tab.Constructor=Tab
$.fn.tab.noConflict=function(){$.fn.tab=old
return this}
$(document).on('click.bs.tab.data-api','[data-toggle="tab"], [data-toggle="pill"]',function(e){e.preventDefault()
Plugin.call($(this),'show')})}(jQuery);+function($){'use strict';function transitionEnd(){var el=document.createElement('bootstrap')
var transEndEventNames={WebkitTransition:'webkitTransitionEnd',MozTransition:'transitionend',OTransition:'oTransitionEnd otransitionend',transition:'transitionend'}
for(var name in transEndEventNames){if(el.style[name]!==undefined){return{end:transEndEventNames[name]}}}
return false}
$.fn.emulateTransitionEnd=function(duration){var called=false
var $el=this
$(this).one('bsTransitionEnd',function(){called=true})
var callback=function(){if(!called)$($el).trigger($.support.transition.end)}
setTimeout(callback,duration)
return this}
$(function(){$.support.transition=transitionEnd()
if(!$.support.transition)return
$.event.special.bsTransitionEnd={bindType:$.support.transition.end,delegateType:$.support.transition.end,handle:function(e){if($(e.target).is(this))return e.handleObj.handler.apply(this,arguments)}}})}(jQuery);+function($){'use strict';function ScrollSpy(element,options){var process=$.proxy(this.process,this)
this.$body=$('body')
this.$scrollElement=$(element).is('body')?$(window):$(element)
this.options=$.extend({},ScrollSpy.DEFAULTS,options)
this.selector=(this.options.target||'')+' .nav li > a'
this.offsets=[]
this.targets=[]
this.activeTarget=null
this.scrollHeight=0
this.$scrollElement.on('scroll.bs.scrollspy',process)
this.refresh()
this.process()}
ScrollSpy.VERSION='3.2.0'
ScrollSpy.DEFAULTS={offset:10}
ScrollSpy.prototype.getScrollHeight=function(){return this.$scrollElement[0].scrollHeight||Math.max(this.$body[0].scrollHeight,document.documentElement.scrollHeight)}
ScrollSpy.prototype.refresh=function(){var offsetMethod='offset'
var offsetBase=0
if(!$.isWindow(this.$scrollElement[0])){offsetMethod='position'
offsetBase=this.$scrollElement.scrollTop()}
this.offsets=[]
this.targets=[]
this.scrollHeight=this.getScrollHeight()
var self=this
this.$body.find(this.selector).map(function(){var $el=$(this)
var href=$el.data('target')||$el.attr('href')
var $href=/^#./.test(href)&&$(href)
return($href&&$href.length&&$href.is(':visible')&&[[$href[offsetMethod]().top+offsetBase,href]])||null}).sort(function(a,b){return a[0]-b[0]}).each(function(){self.offsets.push(this[0])
self.targets.push(this[1])})}
ScrollSpy.prototype.process=function(){var scrollTop=this.$scrollElement.scrollTop()+this.options.offset
var scrollHeight=this.getScrollHeight()
var maxScroll=this.options.offset+scrollHeight-this.$scrollElement.height()
var offsets=this.offsets
var targets=this.targets
var activeTarget=this.activeTarget
var i
if(this.scrollHeight!=scrollHeight){this.refresh()}
if(scrollTop>=maxScroll){return activeTarget!=(i=targets[targets.length-1])&&this.activate(i)}
if(activeTarget&&scrollTop<=offsets[0]){return activeTarget!=(i=targets[0])&&this.activate(i)}
for(i=offsets.length;i--;){activeTarget!=targets[i]&&scrollTop>=offsets[i]&&(!offsets[i+1]||scrollTop<=offsets[i+1])&&this.activate(targets[i])}}
ScrollSpy.prototype.activate=function(target){this.activeTarget=target
$(this.selector).parentsUntil(this.options.target,'.active').removeClass('active')
var selector=this.selector+'[data-target="'+target+'"],'+
this.selector+'[href="'+target+'"]'
var active=$(selector).parents('li').addClass('active')
if(active.parent('.dropdown-menu').length){active=active.closest('li.dropdown').addClass('active')}
active.trigger('activate.bs.scrollspy')}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.scrollspy')
var options=typeof option=='object'&&option
if(!data)$this.data('bs.scrollspy',(data=new ScrollSpy(this,options)))
if(typeof option=='string')data[option]()})}
var old=$.fn.scrollspy
$.fn.scrollspy=Plugin
$.fn.scrollspy.Constructor=ScrollSpy
$.fn.scrollspy.noConflict=function(){$.fn.scrollspy=old
return this}
$(window).on('load.bs.scrollspy.data-api',function(){$('[data-spy="scroll"]').each(function(){var $spy=$(this)
Plugin.call($spy,$spy.data())})})}(jQuery);+function($){'use strict';var Modal=function(element,options){this.options=options
this.$body=$(document.body)
this.$element=$(element)
this.$backdrop=this.isShown=null
this.scrollbarWidth=0
if(this.options.remote){this.$element.find('.modal-content').load(this.options.remote,$.proxy(function(){this.$element.trigger('loaded.bs.modal')},this))}}
Modal.VERSION='3.2.0'
Modal.DEFAULTS={backdrop:true,keyboard:true,show:true}
Modal.prototype.toggle=function(_relatedTarget){return this.isShown?this.hide():this.show(_relatedTarget)}
Modal.prototype.show=function(_relatedTarget){var that=this
var e=$.Event('show.bs.modal',{relatedTarget:_relatedTarget})
this.$element.trigger(e)
if(this.isShown||e.isDefaultPrevented())return
this.isShown=true
this.checkScrollbar()
this.$body.addClass('modal-open')
this.setScrollbar()
this.escape()
this.$element.on('click.dismiss.bs.modal','[data-dismiss="modal"]',$.proxy(this.hide,this))
this.backdrop(function(){var transition=$.support.transition&&that.$element.hasClass('fade')
if(!that.$element.parent().length){that.$element.appendTo(that.$body)}
that.$element.show().scrollTop(0)
if(transition){that.$element[0].offsetWidth}
that.$element.addClass('in').attr('aria-hidden',false)
that.enforceFocus()
var e=$.Event('shown.bs.modal',{relatedTarget:_relatedTarget})
transition?that.$element.find('.modal-dialog').one('bsTransitionEnd',function(){that.$element.trigger('focus').trigger(e)}).emulateTransitionEnd(300):that.$element.trigger('focus').trigger(e)})}
Modal.prototype.hide=function(e){if(e)e.preventDefault()
e=$.Event('hide.bs.modal')
this.$element.trigger(e)
if(!this.isShown||e.isDefaultPrevented())return
this.isShown=false
this.$body.removeClass('modal-open')
this.resetScrollbar()
this.escape()
$(document).off('focusin.bs.modal')
this.$element.removeClass('in').attr('aria-hidden',true).off('click.dismiss.bs.modal')
$.support.transition&&this.$element.hasClass('fade')?this.$element.one('bsTransitionEnd',$.proxy(this.hideModal,this)).emulateTransitionEnd(300):this.hideModal()}
Modal.prototype.enforceFocus=function(){$(document).off('focusin.bs.modal').on('focusin.bs.modal',$.proxy(function(e){if(this.$element[0]!==e.target&&!this.$element.has(e.target).length){this.$element.trigger('focus')}},this))}
Modal.prototype.escape=function(){if(this.isShown&&this.options.keyboard){this.$element.on('keyup.dismiss.bs.modal',$.proxy(function(e){e.which==27&&this.hide()},this))}else if(!this.isShown){this.$element.off('keyup.dismiss.bs.modal')}}
Modal.prototype.hideModal=function(){var that=this
this.$element.hide()
this.backdrop(function(){that.$element.trigger('hidden.bs.modal')})}
Modal.prototype.removeBackdrop=function(){this.$backdrop&&this.$backdrop.remove()
this.$backdrop=null}
Modal.prototype.backdrop=function(callback){var that=this
var animate=this.$element.hasClass('fade')?'fade':''
if(this.isShown&&this.options.backdrop){var doAnimate=$.support.transition&&animate
this.$backdrop=$('<div class="modal-backdrop '+animate+'" />').appendTo(this.$body)
this.$element.on('click.dismiss.bs.modal',$.proxy(function(e){if(e.target!==e.currentTarget)return
this.options.backdrop=='static'?this.$element[0].focus.call(this.$element[0]):this.hide.call(this)},this))
if(doAnimate)this.$backdrop[0].offsetWidth
this.$backdrop.addClass('in')
if(!callback)return
doAnimate?this.$backdrop.one('bsTransitionEnd',callback).emulateTransitionEnd(150):callback()}else if(!this.isShown&&this.$backdrop){this.$backdrop.removeClass('in')
var callbackRemove=function(){that.removeBackdrop()
callback&&callback()}
$.support.transition&&this.$element.hasClass('fade')?this.$backdrop.one('bsTransitionEnd',callbackRemove).emulateTransitionEnd(150):callbackRemove()}else if(callback){callback()}}
Modal.prototype.checkScrollbar=function(){if(document.body.clientWidth>=window.innerWidth)return
this.scrollbarWidth=this.scrollbarWidth||this.measureScrollbar()}
Modal.prototype.setScrollbar=function(){var bodyPad=parseInt((this.$body.css('padding-right')||0),10)
if(this.scrollbarWidth)this.$body.css('padding-right',bodyPad+this.scrollbarWidth)}
Modal.prototype.resetScrollbar=function(){this.$body.css('padding-right','')}
Modal.prototype.measureScrollbar=function(){var scrollDiv=document.createElement('div')
scrollDiv.className='modal-scrollbar-measure'
this.$body.append(scrollDiv)
var scrollbarWidth=scrollDiv.offsetWidth-scrollDiv.clientWidth
this.$body[0].removeChild(scrollDiv)
return scrollbarWidth}
function Plugin(option,_relatedTarget){return this.each(function(){var $this=$(this)
var data=$this.data('bs.modal')
var options=$.extend({},Modal.DEFAULTS,$this.data(),typeof option=='object'&&option)
if(!data)$this.data('bs.modal',(data=new Modal(this,options)))
if(typeof option=='string')data[option](_relatedTarget)
else if(options.show)data.show(_relatedTarget)})}
var old=$.fn.modal
$.fn.modal=Plugin
$.fn.modal.Constructor=Modal
$.fn.modal.noConflict=function(){$.fn.modal=old
return this}
$(document).on('click.bs.modal.data-api','[data-toggle="modal"]',function(e){var $this=$(this)
var href=$this.attr('href')
var $target=$($this.attr('data-target')||(href&&href.replace(/.*(?=#[^\s]+$)/,'')))
var option=$target.data('bs.modal')?'toggle':$.extend({remote:!/#/.test(href)&&href},$target.data(),$this.data())
if($this.is('a'))e.preventDefault()
$target.one('show.bs.modal',function(showEvent){if(showEvent.isDefaultPrevented())return
$target.one('hidden.bs.modal',function(){$this.is(':visible')&&$this.trigger('focus')})})
Plugin.call($target,option,this)})}(jQuery);+function($){'use strict';var Tooltip=function(element,options){this.type=this.options=this.enabled=this.timeout=this.hoverState=this.$element=null
this.init('tooltip',element,options)}
Tooltip.VERSION='3.2.0'
Tooltip.DEFAULTS={animation:true,placement:'top',selector:false,template:'<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>',trigger:'hover focus',title:'',delay:0,html:false,container:false,viewport:{selector:'body',padding:0}}
Tooltip.prototype.init=function(type,element,options){this.enabled=true
this.type=type
this.$element=$(element)
this.options=this.getOptions(options)
this.$viewport=this.options.viewport&&$(this.options.viewport.selector||this.options.viewport)
var triggers=this.options.trigger.split(' ')
for(var i=triggers.length;i--;){var trigger=triggers[i]
if(trigger=='click'){this.$element.on('click.'+this.type,this.options.selector,$.proxy(this.toggle,this))}else if(trigger!='manual'){var eventIn=trigger=='hover'?'mouseenter':'focusin'
var eventOut=trigger=='hover'?'mouseleave':'focusout'
this.$element.on(eventIn+'.'+this.type,this.options.selector,$.proxy(this.enter,this))
this.$element.on(eventOut+'.'+this.type,this.options.selector,$.proxy(this.leave,this))}}
this.options.selector?(this._options=$.extend({},this.options,{trigger:'manual',selector:''})):this.fixTitle()}
Tooltip.prototype.getDefaults=function(){return Tooltip.DEFAULTS}
Tooltip.prototype.getOptions=function(options){options=$.extend({},this.getDefaults(),this.$element.data(),options)
if(options.delay&&typeof options.delay=='number'){options.delay={show:options.delay,hide:options.delay}}
return options}
Tooltip.prototype.getDelegateOptions=function(){var options={}
var defaults=this.getDefaults()
this._options&&$.each(this._options,function(key,value){if(defaults[key]!=value)options[key]=value})
return options}
Tooltip.prototype.enter=function(obj){var self=obj instanceof this.constructor?obj:$(obj.currentTarget).data('bs.'+this.type)
if(!self){self=new this.constructor(obj.currentTarget,this.getDelegateOptions())
$(obj.currentTarget).data('bs.'+this.type,self)}
clearTimeout(self.timeout)
self.hoverState='in'
if(!self.options.delay||!self.options.delay.show)return self.show()
self.timeout=setTimeout(function(){if(self.hoverState=='in')self.show()},self.options.delay.show)}
Tooltip.prototype.leave=function(obj){var self=obj instanceof this.constructor?obj:$(obj.currentTarget).data('bs.'+this.type)
if(!self){self=new this.constructor(obj.currentTarget,this.getDelegateOptions())
$(obj.currentTarget).data('bs.'+this.type,self)}
clearTimeout(self.timeout)
self.hoverState='out'
if(!self.options.delay||!self.options.delay.hide)return self.hide()
self.timeout=setTimeout(function(){if(self.hoverState=='out')self.hide()},self.options.delay.hide)}
Tooltip.prototype.show=function(){var e=$.Event('show.bs.'+this.type)
if(this.hasContent()&&this.enabled){this.$element.trigger(e)
var inDom=$.contains(document.documentElement,this.$element[0])
if(e.isDefaultPrevented()||!inDom)return
var that=this
var $tip=this.tip()
var tipId=this.getUID(this.type)
this.setContent()
$tip.attr('id',tipId)
this.$element.attr('aria-describedby',tipId)
if(this.options.animation)$tip.addClass('fade')
var placement=typeof this.options.placement=='function'?this.options.placement.call(this,$tip[0],this.$element[0]):this.options.placement
var autoToken=/\s?auto?\s?/i
var autoPlace=autoToken.test(placement)
if(autoPlace)placement=placement.replace(autoToken,'')||'top'
$tip.detach().css({top:0,left:0,display:'block'}).addClass(placement).data('bs.'+this.type,this)
this.options.container?$tip.appendTo(this.options.container):$tip.insertAfter(this.$element)
var pos=this.getPosition()
var actualWidth=$tip[0].offsetWidth
var actualHeight=$tip[0].offsetHeight
if(autoPlace){var orgPlacement=placement
var $parent=this.$element.parent()
var parentDim=this.getPosition($parent)
placement=placement=='bottom'&&pos.top+pos.height+actualHeight-parentDim.scroll>parentDim.height?'top':placement=='top'&&pos.top-parentDim.scroll-actualHeight<0?'bottom':placement=='right'&&pos.right+actualWidth>parentDim.width?'left':placement=='left'&&pos.left-actualWidth<parentDim.left?'right':placement
$tip.removeClass(orgPlacement).addClass(placement)}
var calculatedOffset=this.getCalculatedOffset(placement,pos,actualWidth,actualHeight)
this.applyPlacement(calculatedOffset,placement)
var complete=function(){that.$element.trigger('shown.bs.'+that.type)
that.hoverState=null}
$.support.transition&&this.$tip.hasClass('fade')?$tip.one('bsTransitionEnd',complete).emulateTransitionEnd(150):complete()}}
Tooltip.prototype.applyPlacement=function(offset,placement){var $tip=this.tip()
var width=$tip[0].offsetWidth
var height=$tip[0].offsetHeight
var marginTop=parseInt($tip.css('margin-top'),10)
var marginLeft=parseInt($tip.css('margin-left'),10)
if(isNaN(marginTop))marginTop=0
if(isNaN(marginLeft))marginLeft=0
offset.top=offset.top+marginTop
offset.left=offset.left+marginLeft
$.offset.setOffset($tip[0],$.extend({using:function(props){$tip.css({top:Math.round(props.top),left:Math.round(props.left)})}},offset),0)
$tip.addClass('in')
var actualWidth=$tip[0].offsetWidth
var actualHeight=$tip[0].offsetHeight
if(placement=='top'&&actualHeight!=height){offset.top=offset.top+height-actualHeight}
var delta=this.getViewportAdjustedDelta(placement,offset,actualWidth,actualHeight)
if(delta.left)offset.left+=delta.left
else offset.top+=delta.top
var arrowDelta=delta.left?delta.left*2-width+actualWidth:delta.top*2-height+actualHeight
var arrowPosition=delta.left?'left':'top'
var arrowOffsetPosition=delta.left?'offsetWidth':'offsetHeight'
$tip.offset(offset)
this.replaceArrow(arrowDelta,$tip[0][arrowOffsetPosition],arrowPosition)}
Tooltip.prototype.replaceArrow=function(delta,dimension,position){this.arrow().css(position,delta?(50*(1-delta/dimension)+'%'):'')}
Tooltip.prototype.setContent=function(){var $tip=this.tip()
var title=this.getTitle()
$tip.find('.tooltip-inner')[this.options.html?'html':'text'](title)
$tip.removeClass('fade in top bottom left right')}
Tooltip.prototype.hide=function(){var that=this
var $tip=this.tip()
var e=$.Event('hide.bs.'+this.type)
this.$element.removeAttr('aria-describedby')
function complete(){if(that.hoverState!='in')$tip.detach()
that.$element.trigger('hidden.bs.'+that.type)}
this.$element.trigger(e)
if(e.isDefaultPrevented())return
$tip.removeClass('in')
$.support.transition&&this.$tip.hasClass('fade')?$tip.one('bsTransitionEnd',complete).emulateTransitionEnd(150):complete()
this.hoverState=null
return this}
Tooltip.prototype.fixTitle=function(){var $e=this.$element
if($e.attr('title')||typeof($e.attr('data-original-title'))!='string'){$e.attr('data-original-title',$e.attr('title')||'').attr('title','')}}
Tooltip.prototype.hasContent=function(){return this.getTitle()}
Tooltip.prototype.getPosition=function($element){$element=$element||this.$element
var el=$element[0]
var isBody=el.tagName=='BODY'
return $.extend({},(typeof el.getBoundingClientRect=='function')?el.getBoundingClientRect():null,{scroll:isBody?document.documentElement.scrollTop||document.body.scrollTop:$element.scrollTop(),width:isBody?$(window).width():$element.outerWidth(),height:isBody?$(window).height():$element.outerHeight()},isBody?{top:0,left:0}:$element.offset())}
Tooltip.prototype.getCalculatedOffset=function(placement,pos,actualWidth,actualHeight){return placement=='bottom'?{top:pos.top+pos.height,left:pos.left+pos.width/2-actualWidth/2}:placement=='top'?{top:pos.top-actualHeight,left:pos.left+pos.width/2-actualWidth/2}:placement=='left'?{top:pos.top+pos.height/2-actualHeight/2,left:pos.left-actualWidth}:{top:pos.top+pos.height/2-actualHeight/2,left:pos.left+pos.width}}
Tooltip.prototype.getViewportAdjustedDelta=function(placement,pos,actualWidth,actualHeight){var delta={top:0,left:0}
if(!this.$viewport)return delta
var viewportPadding=this.options.viewport&&this.options.viewport.padding||0
var viewportDimensions=this.getPosition(this.$viewport)
if(/right|left/.test(placement)){var topEdgeOffset=pos.top-viewportPadding-viewportDimensions.scroll
var bottomEdgeOffset=pos.top+viewportPadding-viewportDimensions.scroll+actualHeight
if(topEdgeOffset<viewportDimensions.top){delta.top=viewportDimensions.top-topEdgeOffset}else if(bottomEdgeOffset>viewportDimensions.top+viewportDimensions.height){delta.top=viewportDimensions.top+viewportDimensions.height-bottomEdgeOffset}}else{var leftEdgeOffset=pos.left-viewportPadding
var rightEdgeOffset=pos.left+viewportPadding+actualWidth
if(leftEdgeOffset<viewportDimensions.left){delta.left=viewportDimensions.left-leftEdgeOffset}else if(rightEdgeOffset>viewportDimensions.width){delta.left=viewportDimensions.left+viewportDimensions.width-rightEdgeOffset}}
return delta}
Tooltip.prototype.getTitle=function(){var title
var $e=this.$element
var o=this.options
title=$e.attr('data-original-title')||(typeof o.title=='function'?o.title.call($e[0]):o.title)
return title}
Tooltip.prototype.getUID=function(prefix){do prefix+=~~(Math.random()*1000000)
while(document.getElementById(prefix))
return prefix}
Tooltip.prototype.tip=function(){return(this.$tip=this.$tip||$(this.options.template))}
Tooltip.prototype.arrow=function(){return(this.$arrow=this.$arrow||this.tip().find('.tooltip-arrow'))}
Tooltip.prototype.validate=function(){if(!this.$element[0].parentNode){this.hide()
this.$element=null
this.options=null}}
Tooltip.prototype.enable=function(){this.enabled=true}
Tooltip.prototype.disable=function(){this.enabled=false}
Tooltip.prototype.toggleEnabled=function(){this.enabled=!this.enabled}
Tooltip.prototype.toggle=function(e){var self=this
if(e){self=$(e.currentTarget).data('bs.'+this.type)
if(!self){self=new this.constructor(e.currentTarget,this.getDelegateOptions())
$(e.currentTarget).data('bs.'+this.type,self)}}
self.tip().hasClass('in')?self.leave(self):self.enter(self)}
Tooltip.prototype.destroy=function(){clearTimeout(this.timeout)
this.hide().$element.off('.'+this.type).removeData('bs.'+this.type)}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.tooltip')
var options=typeof option=='object'&&option
if(!data&&option=='destroy')return
if(!data)$this.data('bs.tooltip',(data=new Tooltip(this,options)))
if(typeof option=='string')data[option]()})}
var old=$.fn.tooltip
$.fn.tooltip=Plugin
$.fn.tooltip.Constructor=Tooltip
$.fn.tooltip.noConflict=function(){$.fn.tooltip=old
return this}}(jQuery);+function($){'use strict';var Popover=function(element,options){this.init('popover',element,options)}
if(!$.fn.tooltip)throw new Error('Popover requires tooltip.js')
Popover.VERSION='3.2.0'
Popover.DEFAULTS=$.extend({},$.fn.tooltip.Constructor.DEFAULTS,{placement:'right',trigger:'click',content:'',template:'<div class="popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'})
Popover.prototype=$.extend({},$.fn.tooltip.Constructor.prototype)
Popover.prototype.constructor=Popover
Popover.prototype.getDefaults=function(){return Popover.DEFAULTS}
Popover.prototype.setContent=function(){var $tip=this.tip()
var title=this.getTitle()
var content=this.getContent()
$tip.find('.popover-title')[this.options.html?'html':'text'](title)
$tip.find('.popover-content').empty()[this.options.html?(typeof content=='string'?'html':'append'):'text'](content)
$tip.removeClass('fade top bottom left right in')
if(!$tip.find('.popover-title').html())$tip.find('.popover-title').hide()}
Popover.prototype.hasContent=function(){return this.getTitle()||this.getContent()}
Popover.prototype.getContent=function(){var $e=this.$element
var o=this.options
return $e.attr('data-content')||(typeof o.content=='function'?o.content.call($e[0]):o.content)}
Popover.prototype.arrow=function(){return(this.$arrow=this.$arrow||this.tip().find('.arrow'))}
Popover.prototype.tip=function(){if(!this.$tip)this.$tip=$(this.options.template)
return this.$tip}
function Plugin(option){return this.each(function(){var $this=$(this)
var data=$this.data('bs.popover')
var options=typeof option=='object'&&option
if(!data&&option=='destroy')return
if(!data)$this.data('bs.popover',(data=new Popover(this,options)))
if(typeof option=='string')data[option]()})}
var old=$.fn.popover
$.fn.popover=Plugin
$.fn.popover.Constructor=Popover
$.fn.popover.noConflict=function(){$.fn.popover=old
return this}}(jQuery);horizon.addInitFunction(function(){var allPanelGroupBodies=$('.nav_accordion > dd > div > ul');allPanelGroupBodies.each(function(index,value){var activePanels=$(this).find('li > a.active');if(activePanels.length===0){$(this).slideUp(0);}});var activePanel=$('.nav_accordion > dd > div > ul > li > a.active');activePanel.closest('div').find('h4').addClass('active');$('.nav_accordion > dt').click(function(){var myDashHeader=$(this);var myDashWasActive=myDashHeader.hasClass("active");var allDashboardHeaders=$('.nav_accordion > dt');allDashboardHeaders.removeClass("active");var allDashboardBodies=$('.nav_accordion > dd');allDashboardBodies.slideUp();if(!myDashWasActive){myDashHeader.addClass("active");var myDashBody=myDashHeader.next();myDashBody.slideDown();var activeDashPanel=myDashBody.find("div > ul > li > a.active");if(activeDashPanel.length===0){var activePanel=myDashBody.find("div:first > ul");activePanel.slideDown();activePanel.closest('div').find("h4").addClass("active");var nonActivePanels=myDashBody.find("div:not(:first) > ul");nonActivePanels.slideUp();}
else
{activeDashPanel.closest('div').find("h4").addClass("active");allPanelGroupBodies.each(function(index,value){var activePanels=$(value).find('li > a.active');if(activePanels.length===0){$(this).slideUp();}});}}
return false;});$('.nav_accordion > dd > div > h4').click(function(){var myPanelGroupHeader=$(this);myPanelGroupWasActive=myPanelGroupHeader.hasClass("active");var allPanelGroupHeaders=$('.nav_accordion > dd > div > h4');allPanelGroupHeaders.removeClass("active");allPanelGroupBodies.slideUp();if(!myPanelGroupWasActive){myPanelGroupHeader.addClass("active");myPanelGroupHeader.closest('div').find('ul').slideDown();}});$('.nav_accordion > dd > ul > li > a').click(function(){horizon.modals.modal_spinner(gettext("Loading"));});});horizon.ajax={_queue:[],_active:[],get_messages:function(request){return request.getResponseHeader("X-Horizon-Messages");},queue:function(opts){var complete=opts.complete,active=horizon.ajax._active;opts.complete=function(){var index=$.inArray(request,active);if(index>-1){active.splice(index,1);}
horizon.ajax.next();if(complete){complete.apply(this,arguments);}};function request(){return $.ajax(opts);}
horizon.ajax._queue.push(request);horizon.ajax.next();},next:function(){var queue=horizon.ajax._queue,limit=horizon.conf.ajax.queue_limit,request;if(queue.length&&(!limit||horizon.ajax._active.length<limit)){request=queue.pop();horizon.ajax._active.push(request);return request();}}};horizon.forms={handle_snapshot_source:function(){$("div.table_wrapper, #modal_wrapper").on("change","select#id_snapshot_source",function(evt){var $option=$(this).find("option:selected");var $form=$(this).closest('form');var $volName=$form.find('input#id_name');if($volName.val()===""){$volName.val($option.data("name"));}
var $volSize=$form.find('input#id_size');var volSize=parseInt($volSize.val(),10)||-1;var dataSize=parseInt($option.data("size"),10)||-1;if(volSize<dataSize){$volSize.val(dataSize);}});},handle_volume_source:function(){$("div.table_wrapper, #modal_wrapper").on("change","select#id_volume_source",function(evt){var $option=$(this).find("option:selected");var $form=$(this).closest('form');var $volName=$form.find('input#id_name');if($volName.val()===""){$volName.val($option.data("name"));}
var $volSize=$form.find('input#id_size');var volSize=parseInt($volSize.val(),10)||-1;var dataSize=parseInt($option.data("size"),10)||-1;if(volSize<dataSize){$volSize.val(dataSize);}});},handle_image_source:function(){$("div.table_wrapper, #modal_wrapper").on("change","select#id_image_source",function(evt){var $option=$(this).find("option:selected");var $form=$(this).closest('form');var $volName=$form.find('input#id_name');if($volName.val()===""){$volName.val($option.data("name"));}
var $volSize=$form.find('input#id_size');var volSize=parseInt($volSize.val(),10)||-1;var dataSize=parseInt($option.data("size"),10)||-1;var minDiskSize=parseInt($option.data("min_disk"),10)||-1;var defaultVolSize=dataSize;if(minDiskSize>defaultVolSize){defaultVolSize=minDiskSize;}
if(volSize<defaultVolSize){$volSize.val(defaultVolSize);}});},handle_object_upload_source:function(){$("div.table_wrapper, #modal_wrapper").on("change","input#id_object_file",function(evt){if(typeof($(this).attr("filename"))==='undefined'){$(this).attr("filename","");}
var $form=$(this).closest("form");var $obj_name=$form.find("input#id_name");var $fullPath=$(this).val();var $startIndex=($fullPath.indexOf('\\')>=0?$fullPath.lastIndexOf('\\'):$fullPath.lastIndexOf('/'));var $filename=$fullPath.substring($startIndex);if($filename.indexOf('\\')===0||$filename.indexOf('/')===0){$filename=$filename.substring(1);}
if(typeof($obj_name.val())==='undefined'||$(this).attr("filename").localeCompare($obj_name.val())===0){$obj_name.val($filename);$(this).attr("filename",$filename);$obj_name.trigger('input');}});},datepicker:function(){var startDate=$('input#id_start').datepicker({language:horizon.datepickerLocale}).on('changeDate',function(ev){if(ev.dates[0].valueOf()>endDate.dates[0].valueOf()){var newDate=new Date(ev.dates[0]);newDate.setDate(newDate.getDate()+1);endDate.setDate(newDate);$('input#id_end')[0].focus();}
startDate.hide();endDate.setStartDate(ev.dates[0]);endDate.update();}).data('datepicker');var endDate=$('input#id_end').datepicker({language:horizon.datepickerLocale,startDate:startDate?startDate.dates[0]:null}).on('changeDate',function(ev){endDate.hide();}).data('datepicker');$("input#id_start").mousedown(function(){endDate.hide();});$("input#id_end").mousedown(function(){startDate.hide();});}};horizon.forms.bind_add_item_handlers=function(el){var $selects=$(el).find('select[data-add-item-url]');$selects.each(function(){var $this=$(this);$button=$("<a href='"+$this.attr("data-add-item-url")+"' "+"data-add-to-field='"+$this.attr("id")+"' "+"class='btn ajax-add ajax-modal btn-default'>+</a>");$this.after($button);});};horizon.forms.prevent_multiple_submission=function(el){var $form=$(el).find("form");$form.submit(function(){var button=$(this).find('[type="submit"]');if(button.hasClass('btn-primary')&&!button.hasClass('always-enabled')){$(this).submit(function(){return false;});button.removeClass('primary').addClass('disabled');button.attr('disabled','disabled');}
return true;});};horizon.forms.add_password_fields_reveal_buttons=function(el){var _change_input_type=function($input,type){var $new_input=$input.clone();$new_input.attr('type',type);$input.replaceWith($new_input);return $new_input;};$(el).find('input[type="password"]').each(function(i,input){var $input=$(input);$input.closest('.form-group').addClass("has-feedback");$('<span>').addClass("form-control-feedback glyphicon glyphicon-eye-open").insertAfter($input).click(function(){var $icon=$(this);if($input.attr('type')==='password'){$icon.removeClass('glyphicon-eye-open');$icon.addClass('glyphicon-eye-close');$input=_change_input_type($input,'text');}else{$icon.removeClass('glyphicon-eye-close');$icon.addClass('glyphicon-eye-open');$input=_change_input_type($input,'password');}});});};horizon.forms.init_examples=function(el){var $el=$(el);$el.find("#create_image_form input#id_copy_from").attr("placeholder","http://example.com/image.iso");$el.find(".table_search input").attr("placeholder",gettext("Filter"));};horizon.addInitFunction(function(){horizon.forms.prevent_multiple_submission($('body'));horizon.modals.addModalInitFunction(horizon.forms.prevent_multiple_submission);horizon.forms.bind_add_item_handlers($("body"));horizon.modals.addModalInitFunction(horizon.forms.bind_add_item_handlers);horizon.forms.init_examples($("body"));horizon.modals.addModalInitFunction(horizon.forms.init_examples);horizon.forms.handle_snapshot_source();horizon.forms.handle_volume_source();horizon.forms.handle_image_source();horizon.forms.handle_object_upload_source();horizon.forms.datepicker();horizon.forms.add_password_fields_reveal_buttons($("body"));horizon.modals.addModalInitFunction(horizon.forms.add_password_fields_reveal_buttons);$("body").on("click","form button.btn-danger",function(evt){horizon.datatables.confirm(this);evt.preventDefault();});$(document).on("change",'select.switchable',function(evt){var $fieldset=$(evt.target).closest('fieldset'),$switchables=$fieldset.find('.switchable');$switchables.each(function(index,switchable){var $switchable=$(switchable),slug=$switchable.data('slug'),visible=$switchable.is(':visible'),val=$switchable.val();function handle_switched_field(index,input){var $input=$(input),data=$input.data(slug+"-"+val);if(typeof data==="undefined"||!visible){$input.closest('.form-group').hide();}else{$('label[for='+$input.attr('id')+']').html(data);$input.closest('.form-group').show();}}
$fieldset.find('.switched[data-switch-on*="'+slug+'"]').each(handle_switched_field);$fieldset.siblings().find('.switched[data-switch-on*="'+slug+'"]').each(handle_switched_field);});});$('select.switchable').trigger('change');horizon.modals.addModalInitFunction(function(modal){$(modal).find('select.switchable').trigger('change');});function update_volume_source_displayed_fields(field){var $this=$(field),base_type=$this.val();$this.find("option").each(function(){if(this.value!==base_type){$("#id_"+this.value).closest(".form-group").hide();}else{$("#id_"+this.value).closest(".form-group").show();}});}
$(document).on('change','#id_volume_source_type',function(evt){update_volume_source_displayed_fields(this);});$('#id_volume_source_type').change();horizon.modals.addModalInitFunction(function(modal){$(modal).find("#id_volume_source_type").change();});$(document).tooltip({selector:"div.form-group .help-icon",placement:function(tip,input){return $(input).closest("form[class*='split']").length?"bottom":'right';},title:function(){return $(this).closest('div.form-group').children('.help-block').text();}});$(document).on('mousedown keydown','.form-group select',function(evt){$(this).tooltip('hide');});$(document).on('keydown.esc_btn',function(evt){if(evt.keyCode===27){$('.tooltip').hide();}});$('p.help-block').hide();});horizon.formset_table=(function(){'use strict';var module={};module.reenumerate_rows=function(table,prefix){var count=0;var input_name_re=new RegExp('^'+prefix+'-(\\d+|__prefix__)-');var input_id_re=new RegExp('^id_'+prefix+'-(\\d+|__prefix__)-');table.find('tbody tr').each(function(){$(this).find('input').each(function(){var input=$(this);input.attr('name',input.attr('name').replace(input_name_re,prefix+'-'+count+'-'));input.attr('id',input.attr('id').replace(input_id_re,'id_'+prefix+'-'+count+'-'));});count+=1;});$('#id_'+prefix+'-TOTAL_FORMS').val(count);};module.delete_row=function(e){$(this).closest('tr').hide();$(this).prev('input[name$="-DELETE"]').attr('checked',true);};module.replace_delete=function(where){where.find('input[name$="-DELETE"]').hide().after($('<a href="#" class="close">×</a>').click(module.delete_row));};module.add_row=function(table,prefix,empty_row_html){var new_row=$(empty_row_html);module.replace_delete(new_row);table.find('tbody').append(new_row);module.reenumerate_rows(table,prefix);};module.init=function(prefix,empty_row_html,add_label){var table=$('table#'+prefix);module.replace_delete(table);if(add_label){var button=$('<a href="#" class="btn btn-primary btn-sm pull-right">'+
add_label+'</a>');table.find('tfoot td').append(button);button.click(function(){module.add_row(table,prefix,empty_row_html);});}
var initial_forms=+$('#id_'+prefix+'-INITIAL_FORMS').val();var total_forms=+$('#id_'+prefix+'-TOTAL_FORMS').val();if(table.find('tbody tr').length>1&&table.find('tbody td.error').length===0&&total_forms>initial_forms){table.find('tbody tr').each(function(index){if(index>=initial_forms){$(this).remove();}});module.reenumerate_rows(table,prefix);$('#id_'+prefix+'-INITIAL_FORMS').val($('#id_'+prefix+'-TOTAL_FORMS').val());}
table.find('td.error[title]').tooltip();};return module;}());horizon.instances={user_decided_length:false,networks_selected:[],networks_available:[],getConsoleLog:function(via_user_submit){var form_element=$("#tail_length"),data;if(!via_user_submit){via_user_submit=false;}
if(this.user_decided_length){data=$(form_element).serialize();}else{data="length=35";}
$.ajax({url:$(form_element).attr('action'),data:data,method:'get',success:function(response_body){$('pre.logs').text(response_body);},error:function(response){if(via_user_submit){horizon.clearErrorMessages();horizon.alert('error',gettext('There was a problem communicating with the server, please try again.'));}}});},get_network_element:function(network_id){return $('li > label[for^="id_network_'+network_id+'"]');},init_network_list:function(){horizon.instances.networks_selected=[];horizon.instances.networks_available=[];$(this.get_network_element("")).each(function(){var $this=$(this);var $input=$this.children("input");var name=horizon.escape_html($this.text().replace(/^\s+/,""));var network_property={"name":name,"id":$input.attr("id"),"value":$input.attr("value")};if($input.is(":checked")){horizon.instances.networks_selected.push(network_property);}else{horizon.instances.networks_available.push(network_property);}});},generate_network_element:function(name,id,value){var $li=$('<li>');$li.attr('name',value).html(name+'<em class="network_id">('+value+')</em><a href="#" class="btn btn-primary"></a>');return $li;},generate_networklist_html:function(){var self=this;var updateForm=function(){var lists=$("#networkListId li").attr('data-index',100);var active_networks=$("#selected_network > li").map(function(){return $(this).attr("name");});$("#networkListId input:checkbox").removeAttr('checked');active_networks.each(function(index,value){$("#networkListId input:checkbox[value="+value+"]").prop('checked',true).parents("li").attr('data-index',index);});$("#networkListId ul").html(lists.sort(function(a,b){if($(a).data("index")<$(b).data("index")){return-1;}
if($(a).data("index")>$(b).data("index")){return 1;}
return 0;}));};$("#networkListSortContainer").show();$("#networkListIdContainer").hide();self.init_network_list();$("#available_network").empty();$.each(self.networks_available,function(index,value){$("#available_network").append(self.generate_network_element(value.name,value.id,value.value));});$("#selected_network").empty();$.each(self.networks_selected,function(index,value){$("#selected_network").append(self.generate_network_element(value.name,value.id,value.value));});$(".networklist > li > a.btn").click(function(e){var $this=$(this);e.preventDefault();e.stopPropagation();if($this.parents("ul#available_network").length>0){$this.parent().appendTo($("#selected_network"));}else if($this.parents("ul#selected_network").length>0){$this.parent().appendTo($("#available_network"));}
updateForm();});if($("#networkListId > div.form-group.error").length>0){var errortext=$("#networkListId > div.form-group.error").find("span.help-block").text();$("#selected_network_label").before($('<div class="dynamic-error">').html(errortext));}
$(".networklist").sortable({connectWith:"ul.networklist",placeholder:"ui-state-highlight",distance:5,start:function(e,info){$("#selected_network").addClass("dragging");},stop:function(e,info){$("#selected_network").removeClass("dragging");updateForm();}}).disableSelection();},workflow_init:function(modal){horizon.instances.generate_networklist_html();}};horizon.addInitFunction(function(){$(document).on('submit','#tail_length',function(evt){horizon.instances.user_decided_length=true;horizon.instances.getConsoleLog(true);evt.preventDefault();});function update_launch_source_displayed_fields(field){var $this=$(field),base_type=$this.val();$this.closest(".form-group").nextAll().hide();switch(base_type){case"image_id":$("#id_image_id").closest(".form-group").show();break;case"instance_snapshot_id":$("#id_instance_snapshot_id").closest(".form-group").show();break;case"volume_id":$("#id_volume_id, #id_delete_on_terminate").closest(".form-group").show();break;case"volume_image_id":$("#id_image_id, #id_volume_size, #id_device_name, #id_delete_on_terminate").closest(".form-group").show();break;case"volume_snapshot_id":$("#id_volume_snapshot_id, #id_device_name, #id_delete_on_terminate").closest(".form-group").show();break;}}
$(document).on('change','.workflow #id_source_type',function(evt){update_launch_source_displayed_fields(this);});$('.workflow #id_source_type').change();horizon.modals.addModalInitFunction(function(modal){$(modal).find("#id_source_type").change();});function update_device_size(){var volume_size=horizon.Quota.getSelectedFlavor().disk;var image=horizon.Quota.getSelectedImage();if(image!==undefined){if(image.min_disk>volume_size){volume_size=image.min_disk;}}
if(volume_size<1){volume_size=1;}
$("#id_volume_size").val(volume_size);}
$(document).on('change','.workflow #id_flavor',function(evt){update_device_size();});$(document).on('change','.workflow #id_image_id',function(evt){update_device_size();});horizon.instances.decrypt_password=function(encrypted_password,private_key){var crypt=new JSEncrypt();crypt.setKey(private_key);return crypt.decrypt(encrypted_password);};$(document).on('change','#id_private_key_file',function(evt){var file=evt.target.files[0];var reader=new FileReader();if(file){reader.onloadend=function(event){$("#id_private_key").val(event.target.result);};reader.onerror=function(event){horizon.clearErrorMessages();horizon.alert('error',gettext('Could not read the file'));};reader.readAsText(file);}
else{horizon.clearErrorMessages();horizon.alert('error',gettext('Could not decrypt the password'));}});$(document).on('show','#password_instance_modal',function(evt){$("#id_decrypted_password").css("font-family","monospace");$("#id_decrypted_password").css("cursor","text");$("#id_encrypted_password").css("cursor","text");$("#id_keypair_name").css("cursor","text");});$(document).on('click','#decryptpassword_button',function(evt){encrypted_password=$("#id_encrypted_password").val();private_key=$('#id_private_key').val();if(!private_key){evt.preventDefault();$(this).closest('.modal').modal('hide');}
else{if(private_key.length>0){evt.preventDefault();decrypted_password=horizon.instances.decrypt_password(encrypted_password,private_key);if(decrypted_password===false||decrypted_password===null){horizon.clearErrorMessages();horizon.alert('error',gettext('Could not decrypt the password'));}
else{$("#id_decrypted_password").val(decrypted_password);$("#decryptpassword_button").hide();}}}});});horizon.alert=function(type,message,extra_tags){safe=false;if(typeof(extra_tags)!=="undefined"&&$.inArray('safe',extra_tags.split(' '))!==-1){safe=true;}
var type_display={'danger':gettext("Danger: "),'warning':gettext("Warning: "),'info':gettext("Notice: "),'success':gettext("Success: "),'error':gettext("Error: ")}[type];if(type==='error'){type='danger';}
var template=horizon.templates.compiled_templates["#alert_message_template"],params={"type":type,"type_display":type_display,"message":message,"safe":safe};return $(template.render(params)).hide().prependTo("#main_content .messages").fadeIn(100);};horizon.clearErrorMessages=function(){$('#main_content .messages .alert.alert-danger').remove();};horizon.clearSuccessMessages=function(){$('#main_content .messages .alert.alert-success').remove();};horizon.clearAllMessages=function(){horizon.clearErrorMessages();horizon.clearSuccessMessages();};horizon.autoDismissAlerts=function(){var $alerts=$('#main_content .messages .alert');$alerts.each(function(index,alert){var $alert=$(this),types=$alert.attr('class').split(' '),intersection=$.grep(types,function(value){return $.inArray(value,horizon.conf.auto_fade_alerts.types)!==-1;});if(intersection.length>0){setTimeout(function(){$alert.fadeOut(horizon.conf.auto_fade_alerts.fade_duration);},horizon.conf.auto_fade_alerts.delay);}});};horizon.addInitFunction(function(){$(document).ajaxComplete(function(event,request,settings){var message_array=$.parseJSON(horizon.ajax.get_messages(request));$(message_array).each(function(index,item){horizon.alert(item[0],item[1],item[2]);});});$('a.ajax-modal').click(function(){horizon.clearAllMessages();});$(".alert").alert();horizon.autoDismissAlerts();});horizon.modals={_request:null,spinner:null,_init_functions:[]};horizon.modals.addModalInitFunction=function(f){horizon.modals._init_functions.push(f);};horizon.modals.initModal=function(modal){$(horizon.modals._init_functions).each(function(index,f){f(modal);});};horizon.modals.create=function(title,body,confirm,cancel){if(!cancel){cancel=gettext("Cancel");}
var template=horizon.templates.compiled_templates["#modal_template"],params={title:title,body:body,confirm:confirm,cancel:cancel},modal=$(template.render(params)).appendTo("#modal_wrapper");return modal;};horizon.modals.success=function(data,textStatus,jqXHR){var modal;$('#modal_wrapper').append(data);modal=$('.modal:last');modal.modal();$(modal).trigger("new_modal",modal);return modal;};horizon.modals.modal_spinner=function(text){var template=horizon.templates.compiled_templates["#spinner-modal"];horizon.modals.spinner=$(template.render({text:text}));horizon.modals.spinner.appendTo("#modal_wrapper");horizon.modals.spinner.modal({backdrop:'static'});horizon.modals.spinner.find(".modal-body").spin(horizon.conf.spinner_options.modal);};horizon.modals.init_wizard=function(){var _max_visited_step=0;var _validate_steps=function(start,end){var $form=$('.workflow > form'),response={};if(typeof end==='undefined'){end=start;}
$form.find('td.actions div.alert-danger').remove();$form.find('.form-group.error').each(function(){var $group=$(this);$group.removeClass('error');$group.find('span.help-block.error').remove();});$.ajax({type:'POST',url:$form.attr('action'),headers:{'X-Horizon-Validate-Step-Start':start,'X-Horizon-Validate-Step-End':end},data:$form.serialize(),dataType:'json',async:false,success:function(data){response=data;}});if(response.has_errors){var first_field=true;$.each(response.errors,function(step_slug,step_errors){var step_id=response.workflow_slug+'__'+step_slug,$fieldset=$form.find('#'+step_id);$.each(step_errors,function(field,errors){var $field;if(field==='__all__'){$.each(errors,function(index,error){$fieldset.find('td.actions').prepend('<div class="alert alert-message alert-danger">'+
error+'</div>');});$fieldset.find('input,  select, textarea').first().focus();return;}
$field=$fieldset.find('[name="'+field+'"]');$field.closest('.form-group').addClass('error');$.each(errors,function(index,error){$field.before('<span class="help-block error">'+
error+'</span>');});if(first_field){$field.focus();first_field=false;}});});return false;}};$('.workflow.wizard').bootstrapWizard({tabClass:'wizard-tabs',nextSelector:'.button-next',previousSelector:'.button-previous',onTabShow:function(tab,navigation,index){var $navs=navigation.find('li');var total=$navs.length;var current=index;var $footer=$('.modal-footer');_max_visited_step=Math.max(_max_visited_step,current);if(current+1>=total){$footer.find('.button-next').hide();$footer.find('.button-final').show();}else{$footer.find('.button-next').show();$footer.find('.button-final').hide();}
$navs.each(function(i){$this=$(this);if(i<=_max_visited_step){$this.addClass('done');}else{$this.removeClass('done');}});},onNext:function($tab,$nav,index){return _validate_steps(index-1);},onTabClick:function($tab,$nav,current,index){return(index<=current||_validate_steps(current,index-1)!==false);}});};horizon.addInitFunction(function(){$('#modal_wrapper').on('new_modal',function(evt,modal){horizon.modals.initModal(modal);});$(document).on('click','.modal .cancel',function(evt){$(this).closest('.modal').modal('hide');evt.preventDefault();});$(document).on('submit','.modal form',function(evt){var $form=$(this),form=this,$button=$form.find(".modal-footer .btn-primary"),update_field_id=$form.attr("data-add-to-field"),headers={},modalFileUpload=$form.attr("enctype")==="multipart/form-data",formData,ajaxOpts,featureFileList,featureFormData;if(modalFileUpload){featureFileList=$("<input type='file'/>").get(0).files!==undefined;featureFormData=window.FormData!==undefined;if(!featureFileList||!featureFormData){return;}else{formData=new window.FormData(form);}}else{formData=$form.serialize();}
evt.preventDefault();$button.prop("disabled",true);if(update_field_id){headers["X-Horizon-Add-To-Field"]=update_field_id;}
ajaxOpts={type:"POST",url:$form.attr('action'),headers:headers,data:formData,beforeSend:function(){$("#modal_wrapper .modal").last().modal("hide");$('.ajax-modal, .dropdown-toggle').attr('disabled',true);horizon.modals.modal_spinner(gettext("Working"));},complete:function(){horizon.modals.spinner.modal('hide');$("#modal_wrapper .modal").last().modal("show");$button.prop("disabled",false);},success:function(data,textStatus,jqXHR){var redirect_header=jqXHR.getResponseHeader("X-Horizon-Location"),add_to_field_header=jqXHR.getResponseHeader("X-Horizon-Add-To-Field"),json_data,field_to_update;if(redirect_header===null){$('.ajax-modal, .dropdown-toggle').removeAttr("disabled");}
$form.closest(".modal").modal("hide");if(redirect_header){location.href=redirect_header;}
else if(add_to_field_header){json_data=$.parseJSON(data);field_to_update=$("#"+add_to_field_header);field_to_update.append("<option value='"+json_data[0]+"'>"+json_data[1]+"</option>");field_to_update.change();field_to_update.val(json_data[0]);}else{horizon.modals.success(data,textStatus,jqXHR);}},error:function(jqXHR,status,errorThrown){if(jqXHR.getResponseHeader('logout')){location.href=jqXHR.getResponseHeader("X-Horizon-Location");}else{$('.ajax-modal, .dropdown-toggle').removeAttr("disabled");$form.closest(".modal").modal("hide");horizon.alert("danger",gettext("There was an error submitting the form. Please try again."));}}};if(modalFileUpload){ajaxOpts.contentType=false;ajaxOpts.processData=false;}
$.ajax(ajaxOpts);});$(document).on('show.bs.modal','.modal',function(evt){if($(evt.target).hasClass("modal")){var scrollShift=$('body').scrollTop()||$('html').scrollTop(),$this=$(this),topVal=$this.css('top');$this.css('top',scrollShift+parseInt(topVal,10));}
$("select",evt.target).keyup(function(e){if(e.keyCode===27){e.target.blur();e.stopPropagation();}});});horizon.modals.addModalInitFunction(function(modal){$(modal).find(":text, select, textarea").filter(":visible:first").focus();});horizon.modals.addModalInitFunction(horizon.datatables.validate_button);horizon.modals.addModalInitFunction(horizon.utils.loadAngular);$(document).on('click','.ajax-modal',function(evt){var $this=$(this);if(horizon.modals._request&&typeof(horizon.modals._request.abort)!==undefined){horizon.modals._request.abort();}
horizon.modals._request=$.ajax($this.attr('href'),{beforeSend:function(){horizon.modals.modal_spinner(gettext("Loading"));},complete:function(){horizon.modals._request=null;horizon.modals.spinner.modal('hide');},error:function(jqXHR,status,errorThrown){if(jqXHR.status===401){var redir_url=jqXHR.getResponseHeader("X-Horizon-Location");if(redir_url){location.href=redir_url;}else{location.reload(true);}}
else{if(!horizon.ajax.get_messages(jqXHR)){horizon.alert("danger",gettext("An error occurred. Please try again later."));}}},success:function(data,textStatus,jqXHR){var update_field_id=$this.attr('data-add-to-field'),modal,form;modal=horizon.modals.success(data,textStatus,jqXHR);if(update_field_id){form=modal.find("form");if(form.length){form.attr("data-add-to-field",update_field_id);}}}});evt.preventDefault();});$(document).on("show.bs.modal",".modal",function(){var modal_stack=$("#modal_wrapper .modal");modal_stack.splice(modal_stack.length-1,1);modal_stack.modal("hide");});$(document).on('hidden.bs.modal','.modal',function(){var $this=$(this),modal_stack=$("#modal_wrapper .modal");if($this[0]===modal_stack.last()[0]||$this.hasClass("loading")){$this.remove();if(!$this.hasClass("loading")){$("#modal_wrapper .modal").last().modal("show");}}});});horizon.Quota={is_flavor_quota:false,user_value_progress_bars:[],auto_value_progress_bars:[],flavor_progress_bars:[],user_value_form_inputs:[],selected_flavor:null,flavors:[],init:function(){this.user_value_progress_bars=$('div[data-progress-indicator-for]');this.auto_value_progress_bars=$('div[data-progress-indicator-step-by]');this.user_value_form_inputs=$($.map(this.user_value_progress_bars,function(elm){return('#'+$(elm).attr('data-progress-indicator-for'));}));this._initialCreation(this.user_value_progress_bars);this._initialCreation(this.auto_value_progress_bars);this._initialCreation(this.flavor_progress_bars);this._initialAnimations();this._attachInputHandlers();},belowMinimum:function(minimum,actual){return parseInt(minimum,10)>parseInt(actual,10);},imageFitsFlavor:function(image,flavor){if(image===undefined){return true;}else{overDisk=horizon.Quota.belowMinimum(image.min_disk,flavor.disk);overRAM=horizon.Quota.belowMinimum(image.min_ram,flavor.ram);return!(overDisk||overRAM);}},noteDisabledFlavors:function(allDisabled){if($('#some_flavors_disabled').length===0){message=allDisabled?horizon.Quota.allFlavorsDisabledMessage:horizon.Quota.disabledFlavorMessage;$('#id_flavor').parent().append("<span id='some_flavors_disabled'>"+
message+'</span>');}},resetFlavors:function(){if($('#some_flavors_disabled')){$('#some_flavors_disabled').remove();$('#id_flavor option').each(function(){$(this).attr('disabled',false);});}},findImageById:function(id){_image=undefined;$.each(horizon.Quota.images,function(i,image){if(image.id===id){_image=image;}});return _image;},getSelectedImage:function(){selected=$('#id_image_id option:selected').val();return horizon.Quota.findImageById(selected);},disableFlavorsForImage:function(image){image=horizon.Quota.getSelectedImage();to_disable=[];horizon.Quota.resetFlavors();$.each(horizon.Quota.flavors,function(i,flavor){if(!horizon.Quota.imageFitsFlavor(image,flavor)){to_disable.push(flavor.name);}});flavors=$('#id_flavor option');$.each(to_disable,function(i,flavor_name){flavors.each(function(){if($(this).text()===flavor_name){$(this).attr('disabled','disabled');}});});if(to_disable.length>0){selected=($('#id_flavor option').filter(':selected'))[0];if(to_disable.length<flavors.length&&selected.disabled){flavors.each(function(index,element){if(!element.disabled){$('#id_flavor').val(element.value);$('#id_flavor').change();return false;}});}
horizon.Quota.noteDisabledFlavors(to_disable.length===flavors.length);}},initWithImages:function(images,disabledMessage,allDisabledMessage){this.images=images;this.disabledFlavorMessage=disabledMessage;this.allFlavorsDisabledMessage=allDisabledMessage;horizon.Quota.disableFlavorsForImage();},initWithFlavors:function(flavors){this.is_flavor_quota=true;this.flavor_progress_bars=$('div[data-progress-indicator-flavor]');this.flavors=flavors;this.init();this.showFlavorDetails();this.updateFlavorUsage();},getSelectedFlavor:function(){if(this.is_flavor_quota){this.selected_flavor=$.grep(this.flavors,function(flavor){return flavor.id===$("#id_flavor").children(":selected").val();})[0];}else{this.selected_flavor=null;}
return this.selected_flavor;},showFlavorDetails:function(){this.getSelectedFlavor();if(this.selected_flavor){var name=horizon.utils.truncate(this.selected_flavor.name,14,true);var vcpus=horizon.utils.humanizeNumbers(this.selected_flavor.vcpus);var disk=horizon.utils.humanizeNumbers(this.selected_flavor.disk);var ephemeral=horizon.utils.humanizeNumbers(this.selected_flavor["OS-FLV-EXT-DATA:ephemeral"]);var disk_total=this.selected_flavor.disk+this.selected_flavor["OS-FLV-EXT-DATA:ephemeral"];var disk_total_display=horizon.utils.humanizeNumbers(disk_total);var ram=horizon.utils.humanizeNumbers(this.selected_flavor.ram);$("#flavor_name").html(name);$("#flavor_vcpus").text(vcpus);$("#flavor_disk").text(disk);$("#flavor_ephemeral").text(ephemeral);$("#flavor_disk_total").text(disk_total_display);$("#flavor_ram").text(ram);}},updateFlavorUsage:function(){if(!this.is_flavor_quota){return;}
var scope=this;var instance_count=(parseInt($("#id_count").val(),10)||1);var update_amount=0;this.getSelectedFlavor();$(this.flavor_progress_bars).each(function(index,element){var element_id=$(element).attr('id');var progress_stat=element_id.match(/^quota_(.+)/)[1];if(progress_stat===undefined){return;}else if(progress_stat==='instances'){update_amount=instance_count;}else if(scope.selected_flavor){update_amount=(scope.selected_flavor[progress_stat]*instance_count);}
scope.updateUsageFor(element,update_amount);});},updateUsageFor:function(progress_element,increment_by){progress_element=$(progress_element);var quota_limit=parseInt(progress_element.attr('data-quota-limit'),10);var quota_used=parseInt(progress_element.attr('data-quota-used'),10);var percentage_to_update=((increment_by/quota_limit)*100);var percentage_used=((quota_used/quota_limit)*100);this.update($(progress_element).attr('id'),percentage_to_update);},drawUsed:function(element,used){var w="100%";var h=20;var lvl_curve=4;var bkgrnd="#F2F2F2";var frgrnd="#006CCF";var full="#D0342B";var addition="#00D300";var nearlyfull="orange";var bar=d3.select("#"+element).append("svg:svg").attr("class","chart").attr("width",w).attr("height",h).style("background-color","white").append("g");bar.append("rect").attr("y",0).attr("width",w).attr("height",h).attr("rx",lvl_curve).attr("ry",lvl_curve).style("fill",bkgrnd).style("stroke","#CCCCCC").style("stroke-width",1);bar.append("rect").attr("y",0).attr("class","newbar").attr("width",0).attr("height",h).attr("rx",lvl_curve).attr("ry",lvl_curve).style("fill",function(){return addition;});var used_bar=bar.insert("rect").attr("class","usedbar").attr("y",0).attr("id","test").attr("width",0).attr("height",h).attr("rx",lvl_curve).attr("ry",lvl_curve).style("fill",function(){return frgrnd;}).attr("d",used).transition().duration(500).attr("width",used+"%").style("fill",function(){if(used>=100){return full;}
else if(used>=80){return nearlyfull;}
else{return frgrnd;}});},update:function(element,value){var full="#D0342B";var addition="#00D300";var already_used=parseInt(d3.select("#"+element).select(".usedbar").attr("d"));d3.select("#"+element).select(".newbar").transition().duration(500).attr("width",function(){if((value+already_used)>=100){return"100%";}else{return(value+already_used)+"%";}}).style("fill",function(){if(value>(100-already_used)){return full;}else{return addition;}});},_attachInputHandlers:function(){var scope=this;if(this.is_flavor_quota){var eventCallback=function(evt){scope.showFlavorDetails();scope.updateFlavorUsage();};var imageChangeCallback=function(event){scope.disableFlavorsForImage();};$('#id_flavor').on('change',eventCallback);$('#id_count').on('keyup',eventCallback);$('#id_image_id').on('change',imageChangeCallback);}
$(this.user_value_form_inputs).each(function(index,element){$(element).on('keyup',function(evt){var progress_element=$('div[data-progress-indicator-for='+$(evt.target).attr('id')+']');var integers_in_input=$(evt.target).val().match(/\d+/g);var user_integer;if(integers_in_input===null){user_integer=0;}else if(integers_in_input.length>1){user_integer=integers_in_input.join('');}else if(integers_in_input.length===1){user_integer=integers_in_input[0];}
var progress_amount=parseInt(user_integer,10);scope.updateUsageFor(progress_element,progress_amount);});});},_initialAnimations:function(){var scope=this;$(this.auto_value_progress_bars).each(function(index,element){var auto_progress=$(element);var update_amount=parseInt(auto_progress.attr('data-progress-indicator-step-by'),10);scope.updateUsageFor(auto_progress,update_amount);});},_initialCreation:function(bars){var scope=this;$(bars).each(function(index,element){var progress_element=$(element);var quota_limit=parseInt(progress_element.attr('data-quota-limit'),10);var quota_used=parseInt(progress_element.attr('data-quota-used'),10);var percentage_used=0;if(!isNaN(quota_limit)&&!isNaN(quota_used)){percentage_used=(quota_used/quota_limit)*100;}
scope.drawUsed($(element).attr('id'),percentage_used);});}};horizon.datatables={update:function(){var $rows_to_update=$('tr.status_unknown.ajax-update');if($rows_to_update.length){var interval=$rows_to_update.attr('data-update-interval'),$table=$rows_to_update.closest('table'),decay_constant=$table.attr('decay_constant');if($rows_to_update.find('.actions_column .btn-group.open').length){setTimeout(horizon.datatables.update,interval);$table.removeAttr('decay_constant');return;}
$rows_to_update.each(function(index,row){var $row=$(this),$table=$row.closest('table.datatable');horizon.ajax.queue({url:$row.attr('data-update-url'),error:function(jqXHR,textStatus,errorThrown){switch(jqXHR.status){case 404:var $footer,row_count,footer_text,colspan,template,params,$empty_row;row_count=horizon.datatables.update_footer_count($table,-1);if(row_count===0){colspan=$table.find('th[colspan]').attr('colspan');template=horizon.templates.compiled_templates["#empty_row_template"];params={"colspan":colspan,no_items_label:gettext("No items to display.")};empty_row=template.render(params);$row.replaceWith(empty_row);}else{$row.remove();}
$table.trigger("update");horizon.datatables.update_actions();break;default:horizon.utils.log(gettext("An error occurred while updating."));$row.removeClass("ajax-update");$row.find("i.ajax-updating").remove();break;}},success:function(data,textStatus,jqXHR){var $new_row=$(data);if($new_row.hasClass('status_unknown')){var spinner_elm=$new_row.find("td.status_unknown:last");var imagePath=$new_row.find('.btn-action-required').length>0?"dashboard/img/action_required.png":"dashboard/img/loading.gif";imagePath=STATIC_URL+imagePath;spinner_elm.prepend($("<div>").addClass("loading_gif").append($("<img>").attr("src",imagePath)));}
if($new_row.html()!==$row.html()){if($row.find('.table-row-multi-select:checkbox').is(':checked')){$new_row.find('.table-row-multi-select:checkbox').prop('checked',true);}
$row.replaceWith($new_row);$table.trigger("update");$table.removeAttr('decay_constant');if($table.attr('id')in horizon.datatables.qs){horizon.datatables.qs[$table.attr('id')].cache();}}},complete:function(jqXHR,textStatus){horizon.datatables.validate_button();if(decay_constant===undefined){decay_constant=1;}else{decay_constant++;}
$table.attr('decay_constant',decay_constant);next_poll=interval*decay_constant;if(next_poll>30*1000){next_poll=30*1000;}
setTimeout(horizon.datatables.update,next_poll);}});});}},update_actions:function(){var $actions_to_update=$('.btn-launch.ajax-update, .btn-create.ajax-update');$actions_to_update.each(function(index,action){var $action=$(this);horizon.ajax.queue({url:$action.attr('data-update-url'),error:function(jqXHR,textStatus,errorThrown){horizon.utils.log(gettext("An error occurred while updating."));},success:function(data,textStatus,jqXHR){var $new_action=$(data);if($new_action.html()!=$action.html()){$action.replaceWith($new_action);}}});});},validate_button:function(){$("form").each(function(i){var checkboxes=$(this).find(".table-row-multi-select:checkbox");var action_buttons=$(this).find(".table_actions button.btn-danger");action_buttons.toggleClass("disabled",!checkboxes.filter(":checked").length);});},initialize_checkboxes_behavior:function(){$('div.table_wrapper, #modal_wrapper').on('click','table thead .multi_select_column .table-row-multi-select:checkbox',function(evt){var $this=$(this),$table=$this.closest('table'),is_checked=$this.prop('checked'),checkboxes=$table.find('tbody .table-row-multi-select:visible:checkbox');checkboxes.prop('checked',is_checked);});$("div.table_wrapper, #modal_wrapper").on("click",'table tbody .table-row-multi-select:checkbox',function(evt){var $table=$(this).closest('table');var $multi_select_checkbox=$table.find('thead .multi_select_column .table-row-multi-select:checkbox');var any_unchecked=$table.find("tbody .table-row-multi-select:checkbox").not(":checked");$multi_select_checkbox.prop('checked',any_unchecked.length===0);});$("div.table_wrapper, #modal_wrapper").on("click",'.table-row-multi-select:checkbox',function(evt){var $form=$(this).closest("form");var any_checked=$form.find("tbody .table-row-multi-select:checkbox").is(":checked");if(any_checked){$form.find(".table_actions button.btn-danger").removeClass("disabled");}else{$form.find(".table_actions button.btn-danger").addClass("disabled");}});}};horizon.datatables.confirm=function(action){var $action=$(action),$modal_parent=$(action).closest('.modal'),name_array=[],closest_table_id,action_string,name_string,title,body,modal,form;if($action.hasClass("disabled")){return;}
action_string=$action.text();name_string="";closest_table_id=$(action).closest("table").attr("id");if($("#"+closest_table_id+" tr[data-display]").length>0){var actions_div=$(action).closest("div");if(actions_div.hasClass("table_actions")||actions_div.hasClass("table_actions_menu")){$("#"+closest_table_id+" tr[data-display]").has(".table-row-multi-select:checkbox:checked").each(function(){name_array.push(" \""+$(this).attr("data-display")+"\"");});name_array.join(", ");name_string=name_array.toString();}else{name_string=" \""+$(action).closest("tr").attr("data-display")+"\"";}
name_string=interpolate(gettext("You have selected %s. "),[name_string]);}
title=interpolate(gettext("Confirm %s"),[action_string]);body=name_string+gettext("Please confirm your selection. This action cannot be undone.");modal=horizon.modals.create(title,body,action_string);modal.modal();if($modal_parent.length){var child_backdrop=modal.next('.modal-backdrop');child_backdrop.css('z-index',$modal_parent.css('z-index')+10);modal.css('z-index',child_backdrop.css('z-index')+10);}
modal.find('.btn-primary').click(function(evt){form=$action.closest('form');form.append("<input type='hidden' name='"+$action.attr('name')+"' value='"+$action.attr('value')+"'/>");form.submit();modal.modal('hide');horizon.modals.modal_spinner(gettext("Working"));return false;});return modal;};$.tablesorter.addParser({id:'sizeSorter',is:function(s){return false;},format:function(s){var sizes={BYTE:0,B:0,KB:1,MB:2,GB:3,TB:4,PB:5};var regex=/([\d\.,]+)\s*(byte|B|KB|MB|GB|TB|PB)+/i;var match=s.match(regex);if(match&&match.length===3){return parseFloat(match[1])*Math.pow(1024,sizes[match[2].toUpperCase()]);}
return parseInt(s,10);},type:'numeric'});$.tablesorter.addParser({id:'timesinceSorter',is:function(s){return false;},format:function(s,table,cell,cellIndex){return $(cell).find('span').data('seconds');},type:'numeric'});$.tablesorter.addParser({id:"timestampSorter",is:function(){return false;},format:function(s){s=s.replace(/\-/g," ").replace(/:/g," ");s=s.replace("T"," ").replace("Z"," ");s=s.split(" ");return new Date(s[0],s[1],s[2],s[3],s[4],s[5]).getTime();},type:"numeric"});$.tablesorter.addParser({id:'naturalSort',is:function(s){return false;},format:function(s){result=parseInt(s);if(isNaN(result)){m=s.match(/\d+/);if(m&&m.length){return parseInt(m[0]);}else{return s.charCodeAt(0);}}else{return result;}},type:'numeric'});$.tablesorter.addParser({id:'IPv4Address',is:function(s,table,cell){var a=$(cell).find('li').first().text().split('.');if(a.length!==4){return false;}
for(var i=0;i<a.length;i++){if(isNaN(a[i])){return false;}
if((a[i]&0xFF)!=a[i]){return false;}}
return true;},format:function(s,table,cell){var result=0;var a=$(cell).find('li').first().text().split('.');var last_index=a.length-1;for(var i=0;i<a.length;i++){var shift=8*(last_index-i);result+=((parseInt(a[i],10)<<shift)>>>0);}
return result;},type:'numeric'});horizon.datatables.disable_buttons=function(){$("table .table_actions").on("click",".btn.disabled",function(event){event.preventDefault();event.stopPropagation();});};horizon.datatables.update_footer_count=function(el,modifier){var $el=$(el),$browser,$footer,row_count,footer_text_template,footer_text;if(!modifier){modifier=0;}
$browser=$el.closest("#browser_wrapper");if($browser.length){$footer=$browser.find('.tfoot span.content_table_count');}
else{$footer=$el.find('tfoot span.table_count');}
row_count=$el.find('tbody tr:visible').length+modifier-$el.find('.empty').length;footer_text_template=ngettext("Displaying %s item","Displaying %s items",row_count);footer_text=interpolate(footer_text_template,[row_count]);$footer.text(footer_text);return row_count;};horizon.datatables.add_no_results_row=function(table){template=horizon.templates.compiled_templates["#empty_row_template"];if(!table.find("tbody tr:visible").length&&typeof(template)!=="undefined"){colspan=table.find("th[colspan]").attr('colspan');params={"colspan":colspan,no_items_label:gettext("No items to display.")};table.find("tbody").append(template.render(params));}};horizon.datatables.remove_no_results_row=function(table){table.find("tr.empty").remove();};horizon.datatables.fix_row_striping=function(table){table.trigger('applyWidgetId',['zebra']);};horizon.datatables.set_table_sorting=function(parent){$(parent).find("table.datatable").each(function(){var $table=$(this),header_options={};if($table.find('tbody tr').not('.empty').length>1){$table.find("thead th[class!='table_header']").each(function(i,val){$th=$(this);if(!$th.hasClass('sortable')){header_options[i]={sorter:false};}else if($th.data('type')==='size'){header_options[i]={sorter:'sizeSorter'};}else if($th.data('type')==='ip'){header_options[i]={sorter:'IPv4Address'};}else if($th.data('type')==='timesince'){header_options[i]={sorter:'timesinceSorter'};}else if($th.data('type')==='timestamp'){header_options[i]={sorter:'timestampSorter'};}else if($th.data('type')=='naturalSort'){header_options[i]={sorter:'naturalSort'};}});$table.tablesorter({headers:header_options,widgets:['zebra'],selectorHeaders:"thead th[class!='table_header']",cancelSelection:false});}});};horizon.datatables.add_table_checkboxes=function(parent){$(parent).find('table thead .multi_select_column').each(function(index,thead){if(!$(thead).find('.table-row-multi-select:checkbox').length&&$(thead).parents('table').find('tbody .table-row-multi-select:checkbox').length){$(thead).append('<input type="checkbox" class="table-row-multi-select">');}});};horizon.datatables.set_table_query_filter=function(parent){horizon.datatables.qs={};$(parent).find('table').each(function(index,elm){var input=$($(elm).find('div.table_search.client input')),table_selector;if(input.length>0){input.on('keypress',function(evt){if(evt.keyCode===13){return false;}});input.next('button.btn span.glyphicon-search').on('click keypress',function(evt){return false;});table_selector='table#'+$(elm).attr('id');var qs=input.quicksearch(table_selector+' tbody tr',{'delay':300,'loader':'span.loading','bind':'keyup click','show':this.show,'hide':this.hide,onBefore:function(){var table=$(table_selector);horizon.datatables.remove_no_results_row(table);},onAfter:function(){var template,table,colspan,params;table=$(table_selector);horizon.datatables.update_footer_count(table);horizon.datatables.add_no_results_row(table);horizon.datatables.fix_row_striping(table);},prepareQuery:function(val){return new RegExp(val,"i");},testQuery:function(query,txt,_row){return query.test($(_row).find('td:not(.hidden):not(.actions_column)').text());}});horizon.datatables.qs[$(elm).attr('id')]=qs;}});};horizon.datatables.set_table_fixed_filter=function(parent){$(parent).find('table.datatable').each(function(index,elm){$(elm).on('click','div.table_filter button',function(evt){var table=$(elm);var category=$(this).val();evt.preventDefault();horizon.datatables.remove_no_results_row(table);table.find('tbody tr').hide();table.find('tbody tr.category-'+category).show();horizon.datatables.update_footer_count(table);horizon.datatables.add_no_results_row(table);horizon.datatables.fix_row_striping(table);});$(elm).find('div.table_filter button').each(function(i,button){if($(button).text().indexOf(' (0)')===-1){$(button).addClass('active');$(button).trigger('click');return false;}});});};horizon.addInitFunction(function(){horizon.datatables.validate_button();horizon.datatables.disable_buttons();$('table.datatable').each(function(idx,el){horizon.datatables.update_footer_count($(el),0);});horizon.datatables.initialize_checkboxes_behavior();horizon.datatables.add_table_checkboxes($('body'));horizon.datatables.set_table_sorting($('body'));horizon.datatables.set_table_query_filter($('body'));horizon.datatables.set_table_fixed_filter($('body'));horizon.modals.addModalInitFunction(horizon.datatables.add_table_checkboxes);horizon.modals.addModalInitFunction(horizon.datatables.set_table_sorting);horizon.modals.addModalInitFunction(horizon.datatables.set_table_query_filter);horizon.modals.addModalInitFunction(horizon.datatables.set_table_fixed_filter);horizon.tabs.addTabLoadFunction(horizon.datatables.add_table_checkboxes);horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_sorting);horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_query_filter);horizon.tabs.addTabLoadFunction(horizon.datatables.set_table_fixed_filter);horizon.tabs.addTabLoadFunction(horizon.datatables.initialize_checkboxes_behavior);horizon.tabs.addTabLoadFunction(horizon.datatables.validate_button);horizon.datatables.update();});horizon.inline_edit={get_cell_id:function(td_element){return[td_element.parents("tr").first().data("object-id"),"__",td_element.data("cell-name")].join('');},get_object_container:function(td_element){if(!window.cell_object_container){window.cell_object_container=[];}
return window.cell_object_container;},get_cell_object:function(td_element){var cell_id=horizon.inline_edit.get_cell_id(td_element);var id="cell__"+cell_id;var container=horizon.inline_edit.get_object_container(td_element);var cell_object;if(container&&container[id]){cell_object=container[id];cell_object.reset_with(td_element);return cell_object;}else{cell_object=new horizon.inline_edit.Cell(td_element);container[id]=cell_object;return cell_object;}},Cell:function(td_element){var self=this;self.reset_with=function(td_element){self.td_element=td_element;self.form_element=td_element.find("input, textarea");self.url=td_element.data('update-url');self.inline_edit_mod=false;self.successful_update=false;};self.reset_with(td_element);self.refresh=function(){horizon.ajax.queue({url:self.url,data:{'inline_edit_mod':self.inline_edit_mod},beforeSend:function(){self.start_loading();},complete:function(){$(".tooltip.fade.top.in").remove();self.stop_loading();if(self.successful_update){var success=$('<div class="success"></div>');self.td_element.find('.inline-edit-status').append(success);var background_color=self.td_element.css('background-color');self.td_element.addClass("no-transition");self.td_element.addClass("success");self.td_element.removeClass("no-transition");self.td_element.removeClass("inline_edit_available");success.fadeOut(1300,function(){self.td_element.addClass("inline_edit_available");self.td_element.removeClass("success");});}},error:function(jqXHR,status,errorThrown){if(jqXHR.status===401){var redir_url=jqXHR.getResponseHeader("X-Horizon-Location");if(redir_url){location.href=redir_url;}else{horizon.alert("error",gettext("Not authorized to do this operation."));}}
else{if(!horizon.ajax.get_messages(jqXHR)){horizon.alert("error",gettext("An error occurred. Please try again later."));}}},success:function(data,textStatus,jqXHR){var td_element=$(data);self.form_element=self.get_form_element(td_element);if(self.inline_edit_mod){var table_cell_wrapper=td_element.find(".table_cell_wrapper");width=self.td_element.outerWidth();height=self.td_element.outerHeight();td_element.width(width);td_element.height(height);td_element.css('margin',0).css('padding',0);table_cell_wrapper.css('margin',0).css('padding',0);if(self.form_element.attr('type')==='checkbox'){var inline_edit_form=td_element.find(".inline-edit-form");inline_edit_form.css('padding-top','11px').css('padding-left','4px');inline_edit_form.width(width-40);}else{self.form_element.width(width-40);self.form_element.height(height-2);self.form_element.css('margin',0).css('padding',0);}}
self.cached_presentation_view=self.td_element;self.rewrite_cell(td_element);if(self.inline_edit_mod){self.form_element.focus();}}});};self.update=function(post_data){horizon.ajax.queue({type:'POST',url:self.url,data:post_data,beforeSend:function(){self.start_loading();},complete:function(){if(!self.successful_update){self.stop_loading();}},error:function(jqXHR,status,errorThrown){if(jqXHR.status===400){if(self.td_element.find(".inline-edit-error .error").length<=0){self.form_element.css('padding-left','20px');self.form_element.width(self.form_element.width()-20);}
error_message=$.parseJSON(jqXHR.responseText).message;var error=$('<div title="'+error_message+'" class="error"></div>');self.td_element.find(".inline-edit-error").html(error);error.tooltip({'placement':'top'});}
else if(jqXHR.status===401){var redir_url=jqXHR.getResponseHeader("X-Horizon-Location");if(redir_url){location.href=redir_url;}else{horizon.alert("error",gettext("Not authorized to do this operation."));}}
else{if(!horizon.ajax.get_messages(jqXHR)){horizon.alert("error",gettext("An error occurred. Please try again later."));}}},success:function(data,textStatus,jqXHR){self.successful_update=true;self.refresh();}});};self.cancel=function(){self.rewrite_cell(self.cached_presentation_view);self.stop_loading();};self.get_form_element=function(td_element){return td_element.find("input, textarea");};self.rewrite_cell=function(td_element){self.td_element.replaceWith(td_element);self.td_element=td_element;};self.start_loading=function(){self.td_element.addClass("no-transition");var spinner=$('<div class="loading"></div>');self.td_element.find('.inline-edit-status').append(spinner);self.td_element.addClass("loading");self.td_element.removeClass("inline_edit_available");self.get_form_element(self.td_element).attr("disabled","disabled");};self.stop_loading=function(){self.td_element.find('div.inline-edit-status div.loading').remove();self.td_element.removeClass("loading");self.td_element.addClass("inline_edit_available");self.get_form_element(self.td_element).removeAttr("disabled");};}};horizon.addInitFunction(function(){$('table').on('click','.ajax-inline-edit',function(evt){var $this=$(this);var td_element=$this.parents('td').first();var cell=horizon.inline_edit.get_cell_object(td_element);cell.inline_edit_mod=true;cell.refresh();evt.preventDefault();});var submit_form=function(evt,el){var $submit=$(el);var td_element=$submit.parents('td').first();var post_data=$submit.parents('form').first().serialize();var cell=horizon.inline_edit.get_cell_object(td_element);cell.update(post_data);evt.preventDefault();};$('table').on('click','.inline-edit-submit',function(evt){submit_form(evt,this);});$('table').on('keypress','.inline-edit-form',function(evt){if(evt.which===13&&!evt.shiftKey){submit_form(evt,this);}});$('table').on('click','.inline-edit-cancel',function(evt){var $cancel=$(this);var td_element=$cancel.parents('td').first();var cell=horizon.inline_edit.get_cell_object(td_element);cell.cancel();evt.preventDefault();});$('table').on('mouseenter','.inline_edit_available',function(evt){$(this).find(".table_cell_action").fadeIn(100);});$('table').on('mouseleave','.inline_edit_available',function(evt){$(this).find(".table_cell_action").fadeOut(200);});});horizon.tabs={_init_load_functions:[]};horizon.tabs.addTabLoadFunction=function(f){horizon.tabs._init_load_functions.push(f);};horizon.tabs.initTabLoad=function(tab){$(horizon.tabs._init_load_functions).each(function(index,f){f(tab);});};horizon.tabs.load_tab=function(evt){var $this=$(this),tab_id=$this.attr('data-target'),tab_pane=$(tab_id);tab_pane.append("<span style='margin-left: 30px;'>"+gettext("Loading")+"&hellip;</span>");tab_pane.spin(horizon.conf.spinner_options.inline);$(tab_pane.data().spinner.el).css('top','9px');$(tab_pane.data().spinner.el).css('left','15px');if(window.location.search.length>0){tab_pane.load(window.location.search+"&tab="+tab_id.replace('#',''),function(){horizon.tabs.initTabLoad(tab_pane);});}else{tab_pane.load("?tab="+tab_id.replace('#',''),function(){horizon.tabs.initTabLoad(tab_pane);});}
$this.attr("data-loaded","true");};horizon.addInitFunction(function(){var data=horizon.cookies.get("tabs")||{};$(".tab-content").find(".js-tab-pane").addClass("tab-pane");horizon.modals.addModalInitFunction(function(el){$(el).find(".js-tab-pane").addClass("tab-pane");});$(document).on("show.bs.tab",".ajax-tabs a[data-loaded='false']",horizon.tabs.load_tab);$(document).on("shown.bs.tab",".nav-tabs a[data-toggle='tab']",function(evt){var $tab=$(evt.target),$content=$($(evt.target).attr('data-target'));$content.find("table.datatable").each(function(){horizon.datatables.update_footer_count($(this));});data[$tab.closest(".nav-tabs").attr("id")]=$tab.attr('data-target');horizon.cookies.put("tabs",data);});$(".nav-tabs[data-sticky-tabs='sticky']").each(function(index,item){var $this=$(this),id=$this.attr("id"),active_tab=data[id];if(active_tab&&window.location.search.indexOf("tab=")<0){$this.find("a[data-target='"+active_tab+"']").tab('show');}});$(document).on("keydown",".tab-pane :input:visible:last",function(evt){var $this=$(this),next_pane=$this.closest(".tab-pane").next(".tab-pane");if(evt.which===9&&!event.shiftKey&&next_pane.length){evt.preventDefault();$(".nav-tabs a[data-target='#"+next_pane.attr("id")+"']").tab('show');}});$(document).on("keydown",".tab-pane :input:visible:first",function(evt){var $this=$(this),prev_pane=$this.closest(".tab-pane").prev(".tab-pane");if(event.shiftKey&&evt.which===9&&prev_pane.length){evt.preventDefault();$(".nav-tabs a[data-target='#"+prev_pane.attr("id")+"']").tab('show');prev_pane.find(":input:last").focus();}});$(document).on("focus",".tab-content :input",function(){var $this=$(this),tab_pane=$this.closest(".tab-pane"),tab_id=tab_pane.attr('id');if(!tab_pane.hasClass("active")){$(".nav-tabs a[data-target='#"+tab_id+"']").tab('show');}});});horizon.templates={template_ids:["#modal_template","#empty_row_template","#alert_message_template","#spinner-modal","#membership_template"],compiled_templates:{}};horizon.templates.compile_templates=function(){$.each(horizon.templates.template_ids,function(ind,template_id){horizon.templates.compiled_templates[template_id]=Hogan.compile($(template_id).html());});};horizon.addInitFunction(function(){horizon.templates.compile_templates();});horizon.user={init:function(){$("#id_password").change(function(){if($("#id_confirm_password").val()!==""){horizon.user.check_passwords_match();}});$("#id_confirm_password").change(function(){horizon.user.check_passwords_match();});},check_passwords_match:function(){var row=$("label[for='id_confirm_password']");var error_id="id_confirm_password_error";var msg="<span id='"+error_id+"' class='help-block'>"+gettext("Passwords do not match.")+"</span>";var password=$("#id_password").val();var confirm_password=$("#id_confirm_password").val();if(password!==confirm_password&&$("#"+error_id).length===0){$(row).parent().addClass("error");$(row).after(msg);}else if(password===confirm_password){$(row).parent().removeClass("error");$("#"+error_id).remove();}}};horizon.membership={current_membership:[],data:[],roles:[],has_roles:[],default_role_id:[],get_field_id:function(id_string){return id_string.slice(id_string.lastIndexOf("_")+1);},get_role_element:function(step_slug,role_id){return $('select[id^="id_'+step_slug+'_role_'+role_id+'"]');},get_member_element:function(step_slug,data_id){return $('li[data-'+step_slug+'-id$='+data_id+']').parent();},init_properties:function(step_slug){horizon.membership.has_roles[step_slug]=$("."+step_slug+"_membership").data('show-roles')!=="False";horizon.membership.default_role_id[step_slug]=$('#id_default_'+step_slug+'_role').attr('value');horizon.membership.init_data_list(step_slug);horizon.membership.init_role_list(step_slug);horizon.membership.init_current_membership(step_slug);},init_data_list:function(step_slug){horizon.membership.data[step_slug]=[];angular.forEach($(this.get_role_element(step_slug,"")).find("option"),function(option){horizon.membership.data[step_slug][option.value]=option.text;});},init_role_list:function(step_slug){horizon.membership.roles[step_slug]=[];angular.forEach($('label[for^="id_'+step_slug+'_role_"]'),function(role){var id=horizon.membership.get_field_id($(role).attr('for'));horizon.membership.roles[step_slug][id]=$(role).text();});},init_current_membership:function(step_slug){horizon.membership.current_membership[step_slug]=[];var members_list=[];var role_name,role_id,selected_members;angular.forEach(this.get_role_element(step_slug,''),function(value,key){role_id=horizon.membership.get_field_id($(value).attr('id'));role_name=$('label[for="id_'+step_slug+'_role_'+role_id+'"]').text();selected_members=$(value).find("option:selected");members_list=[];if(selected_members){angular.forEach(selected_members,function(member){members_list.push(member.value);});}
horizon.membership.current_membership[step_slug][role_id]=members_list;});},get_member_roles:function(step_slug,data_id){var roles=[];for(var role in horizon.membership.current_membership[step_slug]){if($.inArray(data_id,horizon.membership.current_membership[step_slug][role])!==-1){roles.push(role);}}
return roles;},update_role_lists:function(step_slug,role_id,new_list){this.get_role_element(step_slug,role_id).val(new_list);horizon.membership.current_membership[step_slug][role_id]=new_list;},remove_member:function(step_slug,data_id,role_id,role_list){var index=role_list.indexOf(data_id);if(index>=0){role_list.splice(index,1);horizon.membership.update_role_lists(step_slug,role_id,role_list);}},remove_member_from_role:function(step_slug,data_id,role_id){var role,membership=horizon.membership.current_membership[step_slug];if(role_id){horizon.membership.remove_member(step_slug,data_id,role_id,membership[role_id]);}
else{for(role in membership){if(membership.hasOwnProperty(role)){horizon.membership.remove_member(step_slug,data_id,role,membership[role]);}}}},add_member_to_role:function(step_slug,data_id,role_id){var role_list=horizon.membership.current_membership[step_slug][role_id];role_list.push(data_id);horizon.membership.update_role_lists(step_slug,role_id,role_list);},update_member_role_dropdown:function(step_slug,data_id,role_ids,member_el){if(typeof(role_ids)==='undefined'){role_ids=horizon.membership.get_member_roles(step_slug,data_id);}
if(typeof(member_el)==='undefined'){member_el=horizon.membership.get_member_element(step_slug,data_id);}
var $dropdown=member_el.find("li.member").siblings('.dropdown');var $role_items=$dropdown.children('.role_dropdown').children('li');$role_items.each(function(idx,el){if($.inArray(($(el).data('role-id')),role_ids)!==-1){$(el).addClass('selected');}else{$(el).removeClass('selected');}});var $roles_display=$dropdown.children('.dropdown-toggle').children('.roles_display');var roles_to_display=[];for(var i=0;i<role_ids.length;i++){if(i===2){roles_to_display.push('...');break;}
roles_to_display.push(horizon.membership.roles[step_slug][role_ids[i]]);}
text=roles_to_display.join(', ');if(text.length===0){text=gettext('No roles');}
$roles_display.text(text);},generate_member_element:function(step_slug,display_name,data_id,role_ids,text){var roles=[],that=this,membership_roles=that.roles[step_slug],r;for(r in membership_roles){if(membership_roles.hasOwnProperty(r)){roles.push({role_id:r,role_name:membership_roles[r]});}}
var template=horizon.templates.compiled_templates["#membership_template"],params={data_id:"id_"+step_slug+"_"+data_id,step_slug:step_slug,default_role:that.roles[that.default_role_id[step_slug]],display_name:display_name,text:text,roles:roles,roles_label:gettext("Roles")},member_el=$(template.render(params));this.update_member_role_dropdown(step_slug,params.data_id,role_ids,member_el);return $(member_el);},generate_html:function(step_slug){var data_id,data=horizon.membership.data[step_slug];for(data_id in data){if(data.hasOwnProperty(data_id)){var display_name=data[data_id];var role_ids=this.get_member_roles(step_slug,data_id);if(role_ids.length>0){$("."+step_slug+"_members").append(this.generate_member_element(step_slug,display_name,data_id,role_ids,"-"));}
else{$(".available_"+step_slug).append(this.generate_member_element(step_slug,display_name,data_id,role_ids,"+"));}}}
horizon.membership.detect_no_results(step_slug);},update_membership:function(step_slug){$(".available_"+step_slug+", ."+step_slug+"_members").on('click',".btn-group a[href='#add_remove']",function(evt){evt.preventDefault();var available=$(".available_"+step_slug).has($(this)).length;var data_id=horizon.membership.get_field_id($(this).parent().siblings().attr('data-'+step_slug+'-id'));var member_el=$(this).parent().parent();if(available){var default_role=horizon.membership.default_role_id[step_slug];$(this).text("-");$("."+step_slug+"_members").append(member_el);horizon.membership.add_member_to_role(step_slug,data_id,default_role);if(horizon.membership.has_roles[step_slug]){$(this).parent().siblings(".role_options").show();horizon.membership.update_member_role_dropdown(step_slug,data_id,[default_role],member_el);}}
else{$(this).text("+");$(this).parent().siblings(".role_options").hide();$(".available_"+step_slug).append(member_el);horizon.membership.remove_member_from_role(step_slug,data_id);}
horizon.membership.list_filtering(step_slug);horizon.membership.detect_no_results(step_slug);$("input."+step_slug+"_filter").val("");});},detect_no_results:function(step_slug){$('.'+step_slug+'_filterable').each(function(){var css_class=$(this).find('ul').attr('class');var filter=$.grep(css_class.split(' '),function(val){return val.indexOf(step_slug)!==-1;})[0];if(!$('.'+filter).children('ul').length){$('#no_'+filter).show();$("input[id='"+filter+"']").attr('disabled','disabled');}
else{$('#no_'+filter).hide();$("input[id='"+filter+"']").removeAttr('disabled');}});},select_member_role:function(step_slug){$(".available_"+step_slug+", ."+step_slug+"_members").on('click','.role_dropdown li',function(evt){evt.preventDefault();evt.stopPropagation();var new_role_id=$(this).attr("data-role-id");var id_str=$(this).parent().parent().siblings(".member").attr("data-"+step_slug+"-id");var data_id=horizon.membership.get_field_id(id_str);if($(this).hasClass('selected')){$(this).removeClass('selected');horizon.membership.remove_member_from_role(step_slug,data_id,new_role_id);}else{$(this).addClass('selected');horizon.membership.add_member_to_role(step_slug,data_id,new_role_id);}
horizon.membership.update_member_role_dropdown(step_slug,data_id);});},add_new_member:function(step_slug){$("select[id='id_new_"+step_slug+"']").on('change',function(evt){var display_name=$(this).find("option").text();var data_id=$(this).find("option").attr("value");var default_role_id=horizon.membership.default_role_id[step_slug];$("."+step_slug+"_members").append(horizon.membership.generate_member_element(step_slug,display_name,data_id,[default_role_id],"-"));horizon.membership.data[step_slug][data_id]=display_name;$("select[multiple='multiple']").append("<option value='"+data_id+"'>"+horizon.membership.data[step_slug][data_id]+"</option>");horizon.membership.add_member_to_role(step_slug,data_id,default_role_id);$(this).text("");horizon.membership.list_filtering(step_slug);horizon.membership.detect_no_results(step_slug);$("input.filter").val("");$("."+step_slug+"_members .btn-group").removeClass('last_stripe');$("."+step_slug+"_members .btn-group:last").addClass('last_stripe');});},add_new_member_styling:function(step_slug){var add_member_el=$("label[for='id_new_"+step_slug+"']").parent();$(add_member_el).find("select").hide();$("#add_"+step_slug).append($(add_member_el));$(add_member_el).addClass("add_"+step_slug);$(add_member_el).find("label, .input").addClass("add_"+step_slug+"_btn");},fix_stripes:function(step_slug){$('.fake_'+step_slug+'_table').each(function(){var filter="."+$(this).attr('id');var visible=" .btn-group:visible";var even=" .btn-group:visible:even";var last=" .btn-group:visible:last";$(filter+visible).removeClass('dark_stripe');$(filter+visible).addClass('light_stripe');$(filter+even).removeClass('light_stripe');$(filter+even).addClass('dark_stripe');$(filter+visible).removeClass('last_stripe');$(filter+last).addClass('last_stripe');});},list_filtering:function(step_slug){$('input.'+step_slug+'_filter').unbind();$('.'+step_slug+'_filterable').each(function(){var css_class=$(this).children().children('ul').attr('class');var filter=$.grep(css_class.split(' '),function(val){return val.indexOf(step_slug)!==-1;})[0];var input=$("input[id='"+filter+"']");input.quicksearch('ul.'+filter+' ul li span.display_name',{'delay':200,'loader':'span.loading','show':function(){$(this).parent().parent().show();if(filter==="available_"+step_slug){$(this).parent('.dropdown-toggle').hide();}},'hide':function(){$(this).parent().parent().hide();},'noResults':'ul#no_'+filter,'onAfter':function(){horizon.membership.fix_stripes(step_slug);},'prepareQuery':function(val){return new RegExp(val,"i");},'testQuery':function(query,txt,span){if($(input).attr('id')===filter){$(input).prev().removeAttr('disabled');return query.test($(span).text());}else{return true;}}});});},workflow_init:function(modal,step_slug,step_id){$(modal).find('form').each(function(){var $form=$(this);if($form.find('div.'+step_slug+'_membership').length===0){return;}
horizon.membership.init_properties(step_slug);horizon.membership.generate_html(step_slug);horizon.membership.update_membership(step_slug);horizon.membership.select_member_role(step_slug);horizon.membership.add_new_member(step_slug);$form.find(".available_"+step_slug+" .role_options").hide();if(!horizon.membership.has_roles[step_slug]){$form.find("."+step_slug+"_members .role_options").hide();}
if(step_id.indexOf('update')===0){$form.find("#"+step_id+" input").blur();}
$form.find('.'+step_slug+'_membership').keydown(function(event){if(event.keyCode===13){event.preventDefault();return false;}});horizon.membership.add_new_member_styling(step_slug);horizon.membership.list_filtering(step_slug);horizon.membership.detect_no_results(step_slug);$form.find('.fake_'+step_slug+'_table').each(function(){var filter="."+$(this).attr('id');$(filter+' .btn-group:even').addClass('dark_stripe');$(filter+' .btn-group:last').addClass('last_stripe');});});}};horizon.network_topology={model:null,svg:'#topology_canvas',svg_container:'#topologyCanvasContainer',post_messages:'#topologyMessages',network_tmpl:{small:'#topology_template > .network_container_small',normal:'#topology_template > .network_container_normal'},router_tmpl:{small:'#topology_template > .router_small',normal:'#topology_template > .router_normal'},instance_tmpl:{small:'#topology_template > .instance_small',normal:'#topology_template > .instance_normal'},balloon_tmpl:null,balloon_device_tmpl:null,balloon_port_tmpl:null,network_index:{},balloon_id:null,reload_duration:10000,draw_mode:'normal',network_height:0,previous_message:null,element_properties:{normal:{network_width:270,network_min_height:500,top_margin:80,default_height:50,margin:20,device_x:98.5,device_width:90,port_margin:16,port_height:6,port_width:82,port_text_margin:{x:6,y:-4},texts_bg_y:32,type_y:46,balloon_margin:{x:12,y:-12}},small:{network_width:100,network_min_height:400,top_margin:50,default_height:20,margin:30,device_x:47.5,device_width:20,port_margin:5,port_height:3,port_width:32.5,port_text_margin:{x:0,y:0},texts_bg_y:0,type_y:0,balloon_margin:{x:12,y:-30}},cidr_margin:5,device_name_max_size:9,device_name_suffix:'..'},init:function(){var self=this;$(self.svg_container).spin(horizon.conf.spinner_options.modal);if($('#networktopology').length===0){return;}
self.color=d3.scale.category10();self.balloon_tmpl=Hogan.compile($('#balloon_container').html());self.balloon_device_tmpl=Hogan.compile($('#balloon_device').html());self.balloon_port_tmpl=Hogan.compile($('#balloon_port').html());$(document).on('click','a.closeTopologyBalloon',function(e){e.preventDefault();self.delete_balloon();}).on('click','.topologyBalloon',function(e){e.stopPropagation();}).on('click','a.vnc_window',function(e){e.preventDefault();var vnc_window=window.open($(this).attr('href'),vnc_window,'width=760,height=560');self.delete_balloon();}).click(function(){self.delete_balloon();});$('.toggleView > .btn').click(function(){self.draw_mode=$(this).data('value');$('g.network').remove();horizon.cookies.put('ntp_draw_mode',self.draw_mode);self.data_convert();});$(window).on('message',function(e){var message=$.parseJSON(e.originalEvent.data);if(self.previous_message!==message.message){horizon.alert(message.type,message.message);horizon.autoDismissAlerts();self.previous_message=message.message;self.delete_post_message(message.iframe_id);self.load_network_info();setTimeout(function(){self.previous_message=null;},10000);}});self.load_network_info();},load_network_info:function(){var self=this;if($('#networktopology').length===0){return;}
$.getJSON($('#networktopology').data('networktopology')+'?'+$.now(),function(data){self.model=data;self.data_convert();setTimeout(function(){self.load_network_info();},self.reload_duration);});},select_draw_mode:function(){var self=this;var draw_mode=horizon.cookies.get('ntp_draw_mode');if(draw_mode&&(draw_mode==='normal'||draw_mode==='small')){self.draw_mode=draw_mode;}else{if(self.model.networks.length*self.element_properties.normal.network_width>$('#topologyCanvas').width()){self.draw_mode='small';}else{self.draw_mode='normal';}
horizon.cookies.put('ntp_draw_mode',self.draw_mode);}
$('.toggleView > .btn').each(function(){var $this=$(this);if($this.hasClass(self.draw_mode)){$this.addClass('active');}});},data_convert:function(){var self=this;var model=self.model;$.each(model.networks,function(index,network){self.network_index[network.id]=index;});self.select_draw_mode();var element_properties=self.element_properties[self.draw_mode];self.network_height=element_properties.top_margin;$.each([{model:model.routers,type:'router'},{model:model.servers,type:'instance'}],function(index,devices){var type=devices.type;var model=devices.model;$.each(model,function(index,device){device.type=type;device.ports=self.select_port(device.id);var hasports=(device.ports.length<=0)?false:true;device.parent_network=(hasports)?self.select_main_port(device.ports).network_id:self.model.networks[0].id;var height=element_properties.port_margin*(device.ports.length-1);device.height=(self.draw_mode==='normal'&&height>element_properties.default_height)?height:element_properties.default_height;device.pos_y=self.network_height;device.port_height=(self.draw_mode==='small'&&height>device.height)?1:element_properties.port_height;device.port_margin=(self.draw_mode==='small'&&height>device.height)?device.height/device.ports.length:element_properties.port_margin;self.network_height+=device.height+element_properties.margin;});});$.each(model.networks,function(index,network){network.devices=[];$.each([model.routers,model.servers],function(index,devices){$.each(devices,function(index,device){if(network.id===device.parent_network){network.devices.push(device);}});});});self.network_height+=element_properties.top_margin;self.network_height=(self.network_height>element_properties.network_min_height)?self.network_height:element_properties.network_min_height;self.draw_topology();},draw_topology:function(){var self=this;$(self.svg_container).spin(false);$(self.svg_container).removeClass('noinfo');if(self.model.networks.length<=0){$('g.network').remove();$(self.svg_container).addClass('noinfo');return;}
var svg=d3.select(self.svg);var element_properties=self.element_properties[self.draw_mode];svg.attr('width',self.model.networks.length*element_properties.network_width).attr('height',self.network_height);var network=svg.selectAll('g.network').data(self.model.networks);var network_enter=network.enter().append('g').attr('class','network').each(function(d,i){this.appendChild(d3.select(self.network_tmpl[self.draw_mode]).node().cloneNode(true));var $this=d3.select(this).select('.network-rect');if(d.url){$this.on('mouseover',function(){$this.transition().style('fill',function(){return d3.rgb(self.get_network_color(d.id)).brighter(0.5);});}).on('mouseout',function(){$this.transition().style('fill',function(){return self.get_network_color(d.id);});}).on('click',function(){window.location.href=d.url;});}else{$this.classed('nourl',true);}});network.attr('id',function(d){return'id_'+d.id;}).attr('transform',function(d,i){return'translate('+element_properties.network_width*i+','+0+')';}).select('.network-rect').attr('height',function(d){return self.network_height;}).style('fill',function(d){return self.get_network_color(d.id);});network.select('.network-name').attr('x',function(d){return self.network_height/2;}).text(function(d){return d.name;});network.select('.network-cidr').attr('x',function(d){return self.network_height-self.element_properties.cidr_margin;}).text(function(d){var cidr=$.map(d.subnets,function(n,i){return n.cidr;});return cidr.join(', ');});network.exit().remove();var device=network.selectAll('g.device').data(function(d){return d.devices;});var device_enter=device.enter().append("g").attr('class','device').each(function(d,i){var device_template=self[d.type+'_tmpl'][self.draw_mode];this.appendChild(d3.select(device_template).node().cloneNode(true));});device_enter.on('mouseenter',function(d){var $this=$(this);self.show_balloon(d,$this);}).on('click',function(){d3.event.stopPropagation();});device.attr('id',function(d){return'id_'+d.id;}).attr('transform',function(d,i){return'translate('+element_properties.device_x+','+d.pos_y+')';}).select('.frame').attr('height',function(d){return d.height;});device.select('.texts_bg').attr('y',function(d){return element_properties.texts_bg_y+d.height-element_properties.default_height;});device.select('.type').attr('y',function(d){return element_properties.type_y+d.height-element_properties.default_height;});device.select('.name').text(function(d){return self.string_truncate(d.name);});device.each(function(d){if(d.status==='BUILD'){d3.select(this).classed('loading',true);}else if(d.task==='deleting'){d3.select(this).classed('loading',true);if('bl_'+d.id===self.balloon_id){self.delete_balloon();}}else{d3.select(this).classed('loading',false);if('bl_'+d.id===self.balloon_id){var $this=$(this);self.show_balloon(d,$this);}}});device.exit().each(function(d){if('bl_'+d.id===self.balloon_id){self.delete_balloon();}}).remove();var port=device.select('g.ports').selectAll('g.port').data(function(d){return d.ports;});var port_enter=port.enter().append('g').attr('class','port').attr('id',function(d){return'id_'+d.id;});port_enter.append('line').attr('class','port_line');port_enter.append('text').attr('class','port_text');device.select('g.ports').each(function(d,i){this._portdata={};this._portdata.ports_length=d.ports.length;this._portdata.parent_network=d.parent_network;this._portdata.device_height=d.height;this._portdata.port_height=d.port_height;this._portdata.port_margin=d.port_margin;this._portdata.left=0;this._portdata.right=0;$(this).mouseenter(function(e){e.stopPropagation();});});port.each(function(d,i){var index_diff=self.get_network_index(this.parentNode._portdata.parent_network)-
self.get_network_index(d.network_id);this._index_diff=index_diff=(index_diff>=0)?++index_diff:index_diff;this._direction=(this._index_diff<0)?'right':'left';this._index=this.parentNode._portdata[this._direction]++;});port.attr('transform',function(d,i){var x=(this._direction==='left')?0:element_properties.device_width;var ports_length=this.parentNode._portdata[this._direction];var distance=this.parentNode._portdata.port_margin;var y=(this.parentNode._portdata.device_height-
(ports_length-1)*distance)/2+this._index*distance;return'translate('+x+','+y+')';});port.select('.port_line').attr('stroke-width',function(d,i){return this.parentNode.parentNode._portdata.port_height;}).attr('stroke',function(d,i){return self.get_network_color(d.network_id);}).attr('x1',0).attr('y1',0).attr('y2',0).attr('x2',function(d,i){var parent=this.parentNode;var width=(Math.abs(parent._index_diff)-1)*element_properties.network_width+
element_properties.port_width;return(parent._direction==='left')?-1*width:width;});port.select('.port_text').attr('x',function(d){var parent=this.parentNode;if(parent._direction==='left'){d3.select(this).classed('left',true);return element_properties.port_text_margin.x*-1;}else{d3.select(this).classed('left',false);return element_properties.port_text_margin.x;}}).attr('y',function(d){return element_properties.port_text_margin.y;}).text(function(d){var ip_label=[];$.each(d.fixed_ips,function(){ip_label.push(this.ip_address);});return ip_label.join(',');});port.exit().remove();},get_network_color:function(network_id){return this.color(this.get_network_index(network_id));},get_network_index:function(network_id){return this.network_index[network_id];},select_port:function(device_id){return $.map(this.model.ports,function(port,index){if(port.device_id===device_id){return port;}});},select_main_port:function(ports){var _self=this;var main_port_index=0;var MAX_INT=4294967295;var min_port_length=MAX_INT;$.each(ports,function(index,port){var port_length=_self.sum_port_length(port.network_id,ports);if(port_length<min_port_length){min_port_length=port_length;main_port_index=index;}});return ports[main_port_index];},sum_port_length:function(network_id,ports){var self=this;var sum_port_length=0;var base_index=self.get_network_index(network_id);$.each(ports,function(index,port){sum_port_length+=base_index-self.get_network_index(port.network_id);});return sum_port_length;},string_truncate:function(string){var self=this;var str=string;var max_size=self.element_properties.device_name_max_size;var suffix=self.element_properties.device_name_suffix;var bytes=0;for(var i=0;i<str.length;i++){bytes+=str.charCodeAt(i)<=255?1:2;if(bytes>max_size){str=str.substr(0,i)+suffix;break;}}
return str;},delete_device:function(type,device_id){var self=this;var message={id:device_id};self.post_message(device_id,type,message);},delete_port:function(router_id,port_id){var self=this;var message={id:port_id};self.post_message(port_id,'router/'+router_id+'/',message);},show_balloon:function(d,element){var self=this;var element_properties=self.element_properties[self.draw_mode];if(self.balloon_id){self.delete_balloon();}
var balloon_tmpl=self.balloon_tmpl;var device_tmpl=self.balloon_device_tmpl;var port_tmpl=self.balloon_port_tmpl;var balloon_id='bl_'+d.id;var ports=[];$.each(d.ports,function(i,port){var object={};object.id=port.id;object.router_id=port.device_id;object.url=port.url;object.port_status=port.status;object.port_status_css=(port.status==="ACTIVE")?'active':'down';var ip_address='';try{ip_address=port.fixed_ips[0].ip_address;}catch(e){ip_address=gettext('None');}
var device_owner='';try{device_owner=port.device_owner.replace('network:','');}catch(e){device_owner=gettext('None');}
object.ip_address=ip_address;object.device_owner=device_owner;object.is_interface=(device_owner==='router_interface');ports.push(object);});var html_data={balloon_id:balloon_id,id:d.id,url:d.url,name:d.name,type:d.type,delete_label:gettext("Delete"),status:d.status,status_class:(d.status==="ACTIVE")?'active':'down',status_label:gettext("STATUS"),id_label:gettext("ID"),interfaces_label:gettext("Interfaces"),delete_interface_label:gettext("Delete Interface"),open_console_label:gettext("Open Console"),view_details_label:gettext("View Details")};if(d.type==='router'){html_data.delete_label=gettext("Delete Router");html_data.view_details_label=gettext("View Router Details");html_data.port=ports;html_data.add_interface_url=d.url+'addinterface';html_data.add_interface_label=gettext("Add Interface");html=balloon_tmpl.render(html_data,{table1:device_tmpl,table2:(ports.length>0)?port_tmpl:null});}else if(d.type==='instance'){html_data.delete_label=gettext("Terminate Instance");html_data.view_details_label=gettext("View Instance Details");html_data.console_id=d.id;html_data.console=d.console;html=balloon_tmpl.render(html_data,{table1:device_tmpl});}else{return;}
$(self.svg_container).append(html);var device_position=element.find('.frame');var x=device_position.position().left+
element_properties.device_width+
element_properties.balloon_margin.x;var y=device_position.position().top+
element_properties.balloon_margin.y;$('#'+balloon_id).css({'left':x+'px','top':y+'px'}).show();var $balloon=$('#'+balloon_id);if($balloon.offset().left+$balloon.outerWidth()>$(window).outerWidth()){$balloon.css({'left':0+'px'}).css({'left':(device_position.position().left-$balloon.outerWidth()-
element_properties.balloon_margin.x+'px')}).addClass('leftPosition');}
$balloon.find('.delete-device').click(function(e){var $this=$(this);$this.prop('disabled',true);d3.select('#id_'+$this.data('device-id')).classed('loading',true);self.delete_device($this.data('type'),$this.data('device-id'));});$balloon.find('.delete-port').click(function(e){var $this=$(this);self.delete_port($this.data('router-id'),$this.data('port-id'));});self.balloon_id=balloon_id;},delete_balloon:function(){var self=this;if(self.balloon_id){$('#'+self.balloon_id).remove();self.balloon_id=null;}},post_message:function(id,url,message){var self=this;var iframe_id='ifr_'+id;var iframe=$('<iframe width="500" height="300" />').attr('id',iframe_id).attr('src',url).appendTo(self.post_messages);iframe.on('load',function(){$(this).get(0).contentWindow.postMessage(JSON.stringify(message,null,2),'*');});},delete_post_message:function(id){$('#'+id).remove();}};var WIDTH=100;var HEIGHT=100;var RADIUS=45;var BKGRND="#F2F2F2";var FRGRND="#006CCF";var FULL="#D0342B";var NEARLY_FULL="#FFA500";var STROKE="#CCCCCC";function create_vis(chart){return d3.select(chart).append("svg:svg").attr("class","chart").attr("width",WIDTH).attr("height",HEIGHT).attr("viewBox","0 0 "+WIDTH+" "+HEIGHT).append("g").attr("transform","translate("+(WIDTH/2)+","+(HEIGHT/2)+")");}
function create_arc(){return d3.svg.arc().outerRadius(RADIUS).innerRadius(0);}
function create_pie(param){return d3.layout.pie().sort(null).value(function(d){return d[param];});}
horizon.d3_pie_chart_usage={init:function(){var self=this;var pie_chart_data=$(".d3_pie_chart_usage");self.chart=d3.selectAll(".d3_pie_chart_usage");for(var i=0;i<pie_chart_data.length;i++){var used=Math.min(parseInt($(pie_chart_data[i]).data("used")),100);self.data=[{"percentage":used},{"percentage":100-used}];self.pieChart(i);}},pieChart:function(i){var self=this;var vis=create_vis(self.chart[0][i]);var arc=create_arc();var pie=create_pie("percentage");vis.selectAll(".arc").data(pie([{"percentage":10}])).enter().append("path").attr("class","arc").attr("d",arc).style("fill",BKGRND).style("stroke",STROKE).style("stroke-width",1);var animate=function(data){vis.selectAll(".arc").data(pie(data)).enter().append("path").attr("class","arc").attr("d",arc).style("fill",function(){if(self.data[0].percentage>=100){return FULL;}else if(self.data[0].percentage>=80){return NEARLY_FULL;}else{return FRGRND;}}).style("stroke",STROKE).style("stroke-width",function(){if(self.data[0].percentage<=0||self.data[0].percentage>=100){return 0;}else{return 1;}}).transition().duration(500).attrTween("d",function(start){start.endAngle=start.startAngle=0;var end={startAngle:0,endAngle:2*Math.PI*(100-start.value)/100};var tween=d3.interpolate(start,end);return function(t){return arc(tween(t));};});};animate(self.data);}};horizon.d3_pie_chart_distribution={colors:d3.scale.category20(),init:function(){var self=this;var pie_chart_data=$(".d3_pie_chart_distribution");self.chart=d3.selectAll(".d3_pie_chart_distribution");for(var i=0;i<pie_chart_data.length;i++){var parts=$(pie_chart_data[i]).data("used").split("|");self.data=[];self.keys=[];for(var j=0;j<parts.length;j++){var key_value=parts[j].split("=");var d={key:key_value[0],value:key_value[1]};self.data.push(d);self.keys.push(key_value[0]);}
self.pieChart(i);}},pieChart:function(i){var self=this;var vis=create_vis(self.chart[0][i]);var arc=create_arc();var pie=create_pie("value");var total=0;for(var j=0;j<self.data.length;j++){total=total+parseInt(self.data[j].value);}
var initial_data=[];if(total===0){initial_data=[{"value":1}];}
vis.selectAll(".arc").data(pie(initial_data)).enter().append("path").attr("class","arc").attr("d",arc).style("fill",BKGRND).style("stroke",STROKE).style("stroke-width",1);var animate=function(data){vis.selectAll(".arc").data(pie(data)).enter().append("path").attr("class","arc").attr("d",arc).style("fill",function(d){return self.colors(d.data.key);}).style("stroke",STROKE).style("stroke-width",1).transition().duration(500).attrTween("d",function(start){start.endAngle=start.startAngle;var end=jQuery.extend({},start);end.endAngle=end.startAngle+2*Math.PI/total*end.value;var tween=d3.interpolate(start,end);return function(t){return arc(tween(t));};});};if(total!==0){animate(self.data);}
var legend=d3.select(self.chart[0][i]).append("svg").attr("class","legend").attr("width",WIDTH*2).attr("height",self.data.length*18+20).selectAll("g").data(self.keys).enter().append("g").attr("transform",function(d,i){return"translate(0,"+i*20+")";});legend.append("rect").attr("width",18).attr("height",18).style("fill",self.colors);legend.append("text").attr("x",24).attr("y",9).attr("dy",".35em").text(function(d){if(total===0){return d+" 0%";}
var value=0;for(var j=0;j<self.data.length;j++){if(self.data[j].key==d){value=self.data[j].value;break;}}
return d+" "+Math.round(value/total*100)+"%";});}};horizon.addInitFunction(function(){horizon.d3_pie_chart_usage.init();});horizon.addInitFunction(function(){horizon.d3_pie_chart_distribution.init();});var container="#heat_resource_topology";function update(){node=node.data(nodes,function(d){return d.name;});link=link.data(links);var nodeEnter=node.enter().append("g").attr("class","node").attr("node_name",function(d){return d.name;}).attr("node_id",function(d){return d.instance;}).call(force.drag);nodeEnter.append("image").attr("xlink:href",function(d){return d.image;}).attr("id",function(d){return"image_"+d.name;}).attr("x",function(d){return d.image_x;}).attr("y",function(d){return d.image_y;}).attr("width",function(d){return d.image_size;}).attr("height",function(d){return d.image_size;});node.exit().remove();link.enter().insert("svg:line","g.node").attr("class","link").style("stroke-width",function(d){return Math.sqrt(d.value);});link.exit().remove();node.on("mouseover",function(d){$("#info_box").html(d.info_box);current_info=d.name;});node.on("mouseout",function(d){$("#info_box").html('');});force.start();}
function tick(){link.attr("x1",function(d){return d.source.x;}).attr("y1",function(d){return d.source.y;}).attr("x2",function(d){return d.target.x;}).attr("y2",function(d){return d.target.y;});node.attr("transform",function(d){return"translate("+d.x+","+d.y+")";});}
function set_in_progress(stack,nodes){if(stack.in_progress===true){in_progress=true;}
for(var i=0;i<nodes.length;i++){var d=nodes[i];if(d.in_progress===true){in_progress=true;return false;}}}
function findNode(name){for(var i=0;i<nodes.length;i++){if(nodes[i].name===name){return nodes[i];}}}
function findNodeIndex(name){for(var i=0;i<nodes.length;i++){if(nodes[i].name===name){return i;}}}
function addNode(node){nodes.push(node);needs_update=true;}
function removeNode(name){var i=0;var n=findNode(name);while(i<links.length){if(links[i].source===n||links[i].target===n){links.splice(i,1);}else{i++;}}
nodes.splice(findNodeIndex(name),1);needs_update=true;}
function remove_nodes(old_nodes,new_nodes){for(var i=0;i<old_nodes.length;i++){var remove_node=true;for(var j=0;j<new_nodes.length;j++){if(old_nodes[i].name===new_nodes[j].name){remove_node=false;break;}}
if(remove_node===true){removeNode(old_nodes[i].name);}}}
function build_links(){for(var i=0;i<nodes.length;i++){build_node_links(nodes[i]);build_reverse_links(nodes[i]);}}
function build_node_links(node){for(var j=0;j<node.required_by.length;j++){var push_link=true;var target_idx='';var source_idx=findNodeIndex(node.name);try{target_idx=findNodeIndex(node.required_by[j]);}catch(err){push_link=false;}
for(var lidx=0;lidx<links.length;lidx++){if(links[lidx].source===source_idx&&links[lidx].target===target_idx){push_link=false;break;}}
if(push_link===true&&(source_idx&&target_idx)){links.push({'source':source_idx,'target':target_idx,'value':1});}}}
function build_reverse_links(node){for(var i=0;i<nodes.length;i++){if(nodes[i].required_by){for(var j=0;j<nodes[i].required_by.length;j++){var dependency=nodes[i].required_by[j];if(node.name===dependency){links.push({'source':findNodeIndex(nodes[i].name),'target':findNodeIndex(node.name),'value':1});}}}}}
function ajax_poll(poll_time){setTimeout(function(){$.getJSON(ajax_url,function(json){$("#d3_data").attr("data-d3_data",JSON.stringify(json));$("#stack_box").html(json.stack.info_box);set_in_progress(json.stack,json.nodes);needs_update=false;remove_nodes(nodes,json.nodes);json.nodes.forEach(function(d){current_node=findNode(d.name);if(current_node){current_node.status=d.status;if(current_node.image!==d.image){current_node.image=d.image;var this_image=d3.select("#image_"+current_node.name);this_image.transition().attr("x",function(d){return d.image_x+5;}).duration(100).transition().attr("x",function(d){return d.image_x-5;}).duration(100).transition().attr("x",function(d){return d.image_x+5;}).duration(100).transition().attr("x",function(d){return d.image_x-5;}).duration(100).transition().attr("xlink:href",d.image).transition().attr("x",function(d){return d.image_x;}).duration(100).ease("bounce");}
current_node.info_box=d.info_box;}else{addNode(d);build_links();}});if(needs_update===true){update();}});if(in_progress===false){poll_time=30000;}
else{poll_time=3000;}
ajax_poll(poll_time);},poll_time);}
if($(container).length){var width=$(container).width(),height=500,stack_id=$("#stack_id").data("stack_id"),ajax_url='/project/stacks/get_d3_data/'+stack_id+'/',graph=$("#d3_data").data("d3_data"),force=d3.layout.force().nodes(graph.nodes).links([]).gravity(0.1).charge(-2000).linkDistance(100).size([width,height]).on("tick",tick),svg=d3.select(container).append("svg").attr("width",width).attr("height",height),node=svg.selectAll(".node"),link=svg.selectAll(".link"),needs_update=false,nodes=force.nodes(),links=force.links();build_links();update();$("#stack_box").html(graph.stack.info_box);var in_progress=false;set_in_progress(graph.stack,node);var poll_time=0;if(in_progress===true){poll_time=3000;}
else{poll_time=30000;}
ajax_poll(poll_time);}
Rickshaw.namespace('Rickshaw.Graph.Renderer.StaticAxes');Rickshaw.Graph.Renderer.StaticAxes=Rickshaw.Class.create(Rickshaw.Graph.Renderer.Line,{name:'StaticAxes',defaults:function($super){return Rickshaw.extend($super(),{xMin:undefined,xMax:undefined,yMin:undefined,yMax:undefined});},domain:function($super){var ret=$super();var xMin,xMax;if(this.yMin!==undefined&&this.yMax!==undefined){ret.y=[this.yMin,this.yMax];}
if(this.xMin!==undefined&&this.xMax!==undefined){xMin=d3.time.format('%Y-%m-%dT%H:%M:%S').parse(this.xMin);xMin=xMin.getTime()/1000;xMax=d3.time.format('%Y-%m-%dT%H:%M:%S').parse(this.xMax);xMax=xMax.getTime()/1000;ret.x=[xMin,xMax];}
return ret;}});horizon.d3_line_chart={LineChart:function(chart_module,html_element,settings){var self=this;var jquery_element=$(html_element);self.chart_module=chart_module;self.html_element=html_element;self.jquery_element=jquery_element;self.init=function(){var self=this;self.legend_element=$(jquery_element.data('legend-selector')).get(0);self.slider_element=$(jquery_element.data('slider-selector')).get(0);self.url=jquery_element.data('url');self.url_parameters=jquery_element.data('url_parameters');self.final_url=self.url;if(jquery_element.data('form-selector')){$(jquery_element.data('form-selector')).each(function(){if(self.final_url.indexOf('?')>-1){self.final_url+='&'+$(this).serialize();}else{self.final_url+='?'+$(this).serialize();}});}
self.data=[];self.color=d3.scale.category10();self.stats={};self.stats.average=0;self.stats.last_value=0;self.init_settings(settings);self.get_size();};self.init_settings=function(settings){var self=this;self.settings={};self.settings.renderer='line';self.settings.auto_size=true;self.settings.axes_x=true;self.settings.axes_y=true;self.settings.axes_y_label=true;self.settings.interpolation='linear';self.settings.yMin=undefined;self.settings.yMax=undefined;self.settings.xMin=undefined;self.settings.xMax=undefined;self.settings.higlight_last_point=false;self.settings.composed_chart_selector='.overview_chart';self.settings.bar_chart_selector='div[data-chart-type="overview_bar_chart"]';self.settings.bar_chart_settings=undefined;self.hover_formatter='verbose';if(settings){self.apply_settings(settings);}
if(self.jquery_element.data('settings')){var inline_settings=self.jquery_element.data('settings');self.apply_settings(inline_settings);}};self.apply_settings=function(settings){var self=this;var allowed_settings=['renderer','auto_size','axes_x','axes_y','interpolation','yMin','yMax','xMin','xMax','bar_chart_settings','bar_chart_selector','composed_chart_selector','higlight_last_point','axes_y_label'];jQuery.each(allowed_settings,function(index,setting_name){if(settings[setting_name]!==undefined){self.settings[setting_name]=settings[setting_name];}});};self.get_size=function(){$(self.html_element).css('height','');$(self.html_element).css('width','');var svg=$(self.html_element).find('svg');svg.hide();self.width=jquery_element.width();self.height=jquery_element.height();if(self.settings.auto_size){var auto_height=$(window).height()-jquery_element.offset().top-30;if(auto_height>self.height){self.height=auto_height;}}
$(self.html_element).css('height',self.height);$(self.html_element).css('width',self.width);svg.show();svg.css('height',self.height);svg.css('width',self.width);};self.init();self.refresh=function(){var self=this;self.start_loading();horizon.ajax.queue({url:self.final_url,success:function(data,textStatus,jqXHR){self.jquery_element.empty();$(self.legend_element).empty();self.series=data.series;self.stats=data.stats;self.apply_settings(data.settings);if(self.series.length<=0){$(self.html_element).html(gettext('No data available.'));$(self.legend_element).empty();$(self.legend_element).css('height','');}else{self.render();}},error:function(jqXHR,textStatus,errorThrown){$(self.html_element).html(gettext('No data available.'));$(self.legend_element).empty();$(self.legend_element).css('height','');horizon.alert('error',gettext('An error occurred. Please try again later.'));},complete:function(jqXHR,textStatus){self.finish_loading();}});};self.render=function(){var self=this;var last_point,last_point_color;$.map(self.series,function(serie){serie.color=last_point_color=self.color(serie.name);$.map(serie.data,function(statistic){statistic.x=d3.time.format('%Y-%m-%dT%H:%M:%S').parse(statistic.x);statistic.x=statistic.x.getTime()/1000;last_point=statistic;last_point.color=serie.color;});});var renderer=self.settings.renderer;if(renderer==='StaticAxes'){renderer=Rickshaw.Graph.Renderer.StaticAxes;}
self.jquery_element.empty();var $newGraph=self.jquery_element.clone();self.jquery_element.replaceWith($newGraph);self.jquery_element=$newGraph;self.html_element=self.jquery_element[0];var graph=new Rickshaw.Graph({element:self.html_element,width:self.width,height:self.height,renderer:renderer,series:self.series,yMin:self.settings.yMin,yMax:self.settings.yMax,xMin:self.settings.xMin,xMax:self.settings.xMax,interpolation:self.settings.interpolation});graph.render();if(self.hover_formatter==='verbose'){var hoverDetail=new Rickshaw.Graph.HoverDetail({graph:graph,formatter:function(series,x,y){var date='<span class="date">'+new Date(x*1000).toUTCString()+'</span>';var swatch='<span class="detail_swatch" style="background-color: '+series.color+'"></span>';var content=swatch+series.name+': '+parseFloat(y).toFixed(2)+' '+series.unit+'<br>'+date;return content;}});}
if(self.legend_element){var legend=new Rickshaw.Graph.Legend({graph:graph,element:self.legend_element});var shelving=new Rickshaw.Graph.Behavior.Series.Toggle({graph:graph,legend:legend});var order=new Rickshaw.Graph.Behavior.Series.Order({graph:graph,legend:legend});var highlighter=new Rickshaw.Graph.Behavior.Series.Highlight({graph:graph,legend:legend});}
if(self.settings.axes_x){var axes_x=new Rickshaw.Graph.Axis.Time({graph:graph});axes_x.render();}
if(self.settings.axes_y){var axes_y_settings={graph:graph};if(!self.settings.axes_y_label){axes_y_settings.tickFormat=(function(d){return'';});}
var axes_y=new Rickshaw.Graph.Axis.Y(axes_y_settings);axes_y.render();}
$(self.legend_element).css('height','');if(self.stats!==undefined){var composed_chart=self.jquery_element.parents(self.settings.composed_chart_selector).first();var bar_chart_html=composed_chart.find(self.settings.bar_chart_selector).get(0);horizon.d3_bar_chart.refresh(bar_chart_html,self.settings.bar_chart_settings,self.stats);}
if(self.settings.higlight_last_point){if(last_point!==undefined&&last_point_color!==undefined){graph.vis.append('circle').attr('class','used_component').attr('cy',graph.y(last_point.y)).attr('cx',graph.x(last_point.x)).attr('r',2).style('fill',last_point_color).style('stroke',last_point_color).style('stroke-width',2);}}};self.start_loading=function(){var self=this;$(self.html_element).find('.modal-backdrop').remove();$(self.html_element).find('.spinner_wrapper').remove();self.backdrop=$('<div class="modal-backdrop"></div>');self.backdrop.css('width',self.width).css('height',self.height);$(self.html_element).append(self.backdrop);$(self.legend_element).empty().addClass('disabled');self.spinner=$('<div class="spinner_wrapper"></div>');$(self.html_element).append(self.spinner);self.spinner.spin(horizon.conf.spinner_options.line_chart);var radius=horizon.conf.spinner_options.line_chart.radius;var length=horizon.conf.spinner_options.line_chart.length;var spinner_size=radius+length;var top=(self.height/2)-spinner_size/2;var left=(self.width/2)-spinner_size/2;self.spinner.css('top',top).css('left',left);};self.finish_loading=function(){var self=this;$(self.legend_element).removeClass('disabled');};},init:function(selector,settings){var self=this;$(selector).each(function(){self.refresh(this,settings);});if(settings!==undefined&&settings.auto_resize){var rtime=new Date(1,1,2000,12,0,0);var timeout=false;var delta=400;$(window).resize(function(){rtime=new Date();if(timeout===false){timeout=true;setTimeout(resizeend,delta);}});var resizeend=function(){if(new Date()-rtime<delta){setTimeout(resizeend,delta);}else{timeout=false;$(selector).each(function(){self.refresh(this,settings);});}};}
self.bind_commands(selector,settings);},refresh:function(html_element,settings){var chart=new this.LineChart(this,html_element,settings);chart.refresh();},bind_commands:function(selector,settings){var select_box_selector='select[data-line-chart-command="select_box_change"]';var datepicker_selector='input[data-line-chart-command="date_picker_change"]';var self=this;connect_forms_to_charts=function(){$(selector).each(function(){var chart=$(this);$(chart.data('form-selector')).each(function(){var form=$(this);var chart_identifier='div[data-form-selector="'+chart.data('form-selector')+'"]';if(!form.data('charts_selector')){form.data('charts_selector',chart_identifier);}else{form.data('charts_selector',form.data('charts_selector')+', '+chart_identifier);}});});};delegate_event_and_refresh_charts=function(selector,event_name,settings){$('form').delegate(selector,event_name,function(){var invoker=$(this);var form=invoker.parents('form').first();$(form.data('charts_selector')).each(function(){self.refresh(this,settings);});});};bind_select_box_change=function(settings){delegate_event_and_refresh_charts(select_box_selector,'change',settings);};bind_datepicker_change=function(settings){var now=new Date();$(datepicker_selector).each(function(){var el=$(this);el.datepicker({format:'yyyy-mm-dd',setDate:new Date(),showButtonPanel:true});});delegate_event_and_refresh_charts(datepicker_selector,'changeDate',settings);};connect_forms_to_charts();bind_select_box_change(settings);bind_datepicker_change(settings);}};horizon.addInitFunction(function(){horizon.d3_line_chart.init('div[data-chart-type="line_chart"]',{});});horizon.d3_bar_chart={BarChart:function(chart_module,html_element,settings,data){var self=this;self.chart_module=chart_module;self.html_element=html_element;self.jquery_element=$(self.html_element);self.init=function(settings,data){var self=this;self.data={};self.data.max_value=self.jquery_element.data('max-value');if(!self.max_value){self.max_value=100;}
self.data.used=self.jquery_element.data('used');self.data.average=self.jquery_element.data('average');self.data.tooltip_average=self.jquery_element.data('tooltip-average');self.data.tooltip_free=self.jquery_element.data('tooltip-free');self.data.tooltip_used=self.jquery_element.data('tooltip-used');if(data!==undefined){if(data.used!==undefined){self.data.used=data.used;}
if(data.average!==undefined){self.data.average=data.average;}
if(data.tooltip_average!==undefined){self.data.tooltip_average=data.tooltip_average;}
if(data.tooltip_free!==undefined){self.data.tooltip_free=data.tooltip_free;}
if(data.tooltip_used!==undefined){self.data.tooltip_used=data.tooltip_used;}}
if($.isArray(self.data.used)){self.data.percentage_average=0;self.data.percentage_used=Array();self.data.tooltip_used_contents=Array();for(var i=0;i<self.data.used.length;++i){if(!isNaN(self.max_value)&&!isNaN(self.data.used[i].used_instances)){var used=Math.round((self.data.used[i].used_instances/self.max_value)*100);self.data.percentage_used.push(used);self.data.tooltip_used_contents.push(self.data.used[i].tooltip_used);}else{}}}
else{if(!isNaN(self.max_value)&&!isNaN(self.data.used)){self.data.percentage_used=Math.round((self.data.used/self.max_value)*100);}else{self.data.percentage_used=0;}
if(!isNaN(self.max_value)&&!isNaN(self.data.average)){self.data.percentage_average=((self.data.average/self.max_value)*100);}else{self.data.percentage_average=0;}}
self.init_settings(settings);};self.init_settings=function(settings){var self=this;self.data.settings={};self.data.settings.used_label_placement=undefined;self.data.settings.orientation='horizontal';self.data.settings.color_scale_domain=[0,100];self.data.settings.color_scale_range=['#000000','#0000FF'];self.data.settings.width=self.jquery_element.data('width');self.data.settings.height=self.jquery_element.data('height');if(settings){self.apply_settings(settings);}
if(self.jquery_element.data('settings')){var inline_settings=self.jquery_element.data('settings');self.apply_settings(inline_settings);}};self.apply_settings=function(settings){var self=this;var allowed_settings=['orientation','used_label_placement','color_scale_domain','color_scale_range','width','height'];$.each(allowed_settings,function(index,setting_name){if(settings[setting_name]!==undefined){self.data.settings[setting_name]=settings[setting_name];}});};self.init(settings,data);self.refresh=function(){var self=this;self.jquery_element.empty();self.render();};self.render=function(){var self=this;var wrapper=new self.chart_module.Wrapper(self.chart_module,self.html_element,self.data);var tooltip_average=(new self.chart_module.TooltipComponent(wrapper)).render(self.data.tooltip_average);var tooltip_free=(new self.chart_module.TooltipComponent(wrapper)).render(self.data.tooltip_free);var tooltip_used=(new self.chart_module.TooltipComponent(wrapper)).render(self.data.tooltip_used);(new self.chart_module.UnusedComponent(wrapper)).render(tooltip_free);if(wrapper.used_multi()){for(var i=0;i<wrapper.percentage_used.length;++i){wrapper.used_multi_iterator=i;tooltip_used=(new self.chart_module.TooltipComponent(wrapper)).render('');(new self.chart_module.UsedComponent(wrapper)).render(tooltip_used);wrapper.total_used_perc+=wrapper.percentage_used_value();wrapper.total_used_value_in_pixels=(wrapper.w/100)*wrapper.total_used_perc;}}else{(new self.chart_module.UsedComponent(wrapper)).render(tooltip_used);(new self.chart_module.AverageComponent(wrapper)).render(tooltip_average);}};},Wrapper:function(chart_module,html_element,data){var self=this;self.html_element=html_element;self.jquery_element=$(html_element);self.bar_html=d3.select(html_element);self.bar=self.bar_html.append('svg:svg').attr('class','chart').style('background-color','white');chart_module.get_size(self.html_element);self.data=data;self.used_label_placement=data.settings.used_label_placement;if(data.settings.width!==undefined){self.w=parseFloat(data.settings.width);}else{self.w=parseFloat(self.jquery_element.width());}
if(data.settings.height!==undefined){self.h=parseFloat(data.settings.height);}else{self.h=parseFloat(self.jquery_element.height());}
self.chart_start_x=0;if(self.data.settings.orientation==='vertical'){if(self.used_label_placement==='left'){self.chart_start_x=44;}
self.chart_wrapper_w=self.w+self.chart_start_x;}else{self.chart_wrapper_w=self.w;}
self.chart_wrapper_h=self.h;self.lvl_curve=3;self.bkgrnd='#F2F2F2';self.frgrnd='grey';self.color_scale_max=25;self.percentage_used=data.percentage_used;self.total_used_perc=0;self.total_used_value_in_pixels=0;self.used_value_in_pixels=0;self.average_value_in_pixels=0;self.percentage_average=data.percentage_average;self.tooltip_used_contents=data.tooltip_used_contents;self.usage_color=d3.scale.linear().domain(data.settings.color_scale_domain).range(data.settings.color_scale_range);self.border_width=1;self.used_multi=function(){return($.isArray(self.percentage_used));};self.used_multi_iterator=0;self.percentage_used_value=function(){if(self.used_multi()){return self.percentage_used[self.used_multi_iterator];}else{return self.percentage_used;}};self.tooltip_used_value=function(){if(self.used_multi()){return self.tooltip_used_contents[self.used_multi_iterator];}else{return'';}};self.horizontal_orientation=function(){return(self.data.settings.orientation==='horizontal');};},UsedComponent:function(wrapper){var self=this;self.wrapper=wrapper;if(self.wrapper.horizontal_orientation()){self.wrapper.used_value_in_pixels=(self.wrapper.w/100)*self.wrapper.percentage_used_value();self.y=0;self.x=self.wrapper.total_used_value_in_pixels;self.width=0;self.height=self.wrapper.h;self.trasition_attr='width';self.trasition_value=self.wrapper.used_value_in_pixels;}else{self.wrapper.used_value_in_pixels=(self.wrapper.h/100)*self.wrapper.percentage_used_value();self.y=self.wrapper.h;self.x=self.wrapper.chart_start_x;self.width=self.wrapper.w-self.wrapper.border_width;self.height=self.wrapper.used_value_in_pixels;self.trasition_attr='y';self.trasition_value=self.wrapper.h-self.wrapper.used_value_in_pixels;}
self.render=function(tooltip){self.wrapper.bar.append('rect').attr('class','used_component').attr('y',self.y).attr('x',self.x).attr('width',self.width).attr('height',self.height).style('fill',self.wrapper.usage_color(self.wrapper.percentage_used_value())).style('stroke','#bebebe').style('stroke-width',0).attr('d',self.wrapper.percentage_used_value()).attr('tooltip-used',self.wrapper.tooltip_used_value()).on('mouseover',function(d){if($(this).attr('tooltip-used')){tooltip.html($(this).attr('tooltip-used'));}
tooltip.style('visibility','visible');}).on('mousemove',function(d){var eventX=event.offsetX||event.layerX;var eventY=event.offsetY||event.layerY;tooltip.style('top',(eventY-10)+'px').style('left',(eventX+10)+'px');}).on('mouseout',function(d){tooltip.style('visibility','hidden');}).transition().duration(500).attr(self.trasition_attr,self.trasition_value);if(self.wrapper.used_label_placement==='left'){var label_placement_y=self.wrapper.h-self.wrapper.used_value_in_pixels;if(label_placement_y<=6){label_placement_y=6;}else if(label_placement_y>=(self.wrapper.h-6)){label_placement_y=self.wrapper.h-6;}
self.wrapper.bar.append('text').attr('class','used_component_label').text(self.wrapper.percentage_used_value()+'%').attr('y',label_placement_y).attr('x',0).attr('dominant-baseline','middle').attr('font-size',12).transition().duration(500).attr('x',function(){if(self.wrapper.percentage_used_value()>99){return 0;}
else if(self.wrapper.percentage_used_value()>9){return 4;}
else{return 8;}});var poly=[{'x':self.wrapper.chart_start_x-8,'y':label_placement_y},{'x':self.wrapper.chart_start_x-3,'y':label_placement_y+2},{'x':self.wrapper.chart_start_x-3,'y':label_placement_y-2}];self.wrapper.bar.selectAll('polygon').data([poly]).enter().append('polygon').attr('points',function(d){return d.map(function(d){return[d.x,d.y].join(',');}).join(' ');}).attr('stroke','black').attr('stroke-width',2);}};},AverageComponent:function(wrapper){var self=this;self.wrapper=wrapper;if(wrapper.horizontal_orientation()){self.wrapper.average_value_in_pixels=(self.wrapper.w/100)*self.wrapper.percentage_average;self.y=1;self.x=self.wrapper.average_value_in_pixels;self.width=0;self.height=self.wrapper.h;}else{self.wrapper.average_value_in_pixels=(self.wrapper.h/100)*(100-self.wrapper.percentage_average);self.y=self.wrapper.average_value_in_pixels;self.x=self.wrapper.chart_start_x;self.width=self.wrapper.w-self.wrapper.border_width;self.height=0;}
self.render=function(tooltip){if(self.wrapper.percentage_average>0){self.wrapper.bar.append('line').attr('class','average_component').attr('y1',self.y).attr('x1',self.x).attr('class','average').attr('y2',self.y+self.height).attr('x2',self.x+self.width).style('stroke','black').style('stroke-width',3).style('stroke-dasharray',('6, 2')).on('mouseover',function(){tooltip.style('visibility','visible');}).on('mousemove',function(){var eventX=event.offsetX||event.layerX;var eventY=event.offsetY||event.layerY;tooltip.style('top',(eventY-10)+'px').style('left',(eventX+10)+'px');}).on('mouseout',function(){tooltip.style('visibility','hidden');});self.wrapper.bar.append('line').attr('class','average_component').attr('y1',self.y).attr('x1',self.x).attr('class','average').attr('y2',self.y+self.height).attr('x2',self.x+self.width).style('stroke','transparent').style('stroke-width',5).on('mouseover',function(){tooltip.style('visibility','visible');}).on('mousemove',function(){var eventX=event.offsetX||event.layerX;var eventY=event.offsetY||event.layerY;tooltip.style('top',(eventY-10)+'px').style('left',(eventX+10)+'px');}).on('mouseout',function(){tooltip.style('visibility','hidden');});}};},UnusedComponent:function(wrapper){var self=this;self.wrapper=wrapper;self.render=function(tooltip_free){self.wrapper.bar.append('rect').attr('class','unused_component').attr('y',0).attr('x',self.wrapper.chart_start_x).attr('width',self.wrapper.w).attr('height',self.wrapper.h).attr('rx',self.wrapper.lvl_curve).attr('ry',self.wrapper.lvl_curve).style('fill',self.wrapper.bkgrnd).on('mouseover',function(d){tooltip_free.style('visibility','visible');}).on('mousemove',function(d){var eventX=event.offsetX||event.layerX;var eventY=event.offsetY||event.layerY;tooltip_free.style('top',(eventY-10)+'px').style('left',(eventX+10)+'px');}).on('mouseout',function(d){tooltip_free.style('visibility','hidden');});self.wrapper.bar.append('rect').attr('class','unused_component_border').attr('x',self.wrapper.chart_start_x).attr('y',0).attr('height',self.wrapper.h).attr('width',self.wrapper.w-self.wrapper.border_width).style('stroke','#bebebe').style('fill','none').style('stroke-width',1);};},TooltipComponent:function(wrapper){var self=this;self.wrapper=wrapper;self.tooltip_html=self.wrapper.bar_html.append('div');self.render=function(html_content){var display='none';if(html_content){display='block';}
return self.tooltip_html.attr('class','tooltip_detail').style('position','absolute').style('z-index','10').style('visibility','hidden').style('display',display).html(html_content);};},init:function(selector,settings,data){var self=this;self.bars=$(selector);self.bars.each(function(){self.refresh(this,settings,data);});},refresh:function(html_element,settings,data){var chart=new this.BarChart(this,html_element,settings,data);chart.refresh();},get_size:function(html_element){var jquery_element=$(html_element);jquery_element.css('height','');jquery_element.css('width','');var svg=jquery_element.find('svg');svg.hide();var width=jquery_element.width();var height=jquery_element.height();jquery_element.css('height',height);jquery_element.css('width',width);svg.show();svg.css('height',height);svg.css('width',width);}};horizon.addInitFunction(function(){horizon.d3_bar_chart.init('div[data-chart-type="bar_chart"]',{},{});});horizon.firewalls={user_decided_length:false,rules_selected:[],rules_available:[],getConsoleLog:function(via_user_submit){var form_element=$("#tail_length"),data;if(!via_user_submit){via_user_submit=false;}
if(this.user_decided_length){data=$(form_element).serialize();}else{data="length=35";}
$.ajax({url:$(form_element).attr('action'),data:data,method:'get',success:function(response_body){$('pre.logs').text(response_body);},error:function(response){if(via_user_submit){horizon.clearErrorMessages();horizon.alert('error',gettext('There was a problem communicating with the server, please try again.'));}}});},get_rule_element:function(rule_id){return $('li > label[for^="id_rule_'+rule_id+'"]');},init_rule_list:function(){horizon.firewalls.rules_selected=[];horizon.firewalls.rules_available=[];$(this.get_rule_element("")).each(function(){var $this=$(this);var $input=$this.children("input");var rule_property={name:$this.text().replace(/^\s+/,""),id:$input.attr("id"),value:$input.attr("value")};if($input.is(':checked')){horizon.firewalls.rules_selected.push(rule_property);}else{horizon.firewalls.rules_available.push(rule_property);}});},generate_rule_element:function(name,id,value){var $li=$('<li>');$li.attr('name',value).html(name+'<em class="rule_id">('+value+')</em><a href="#" class="btn btn-primary"></a>');return $li;},generate_rulelist_html:function(){var self=this;var updateForm=function(){var lists=$("#ruleListId li").attr('data-index',100);var active_rules=$("#selected_rule > li").map(function(){return $(this).attr("name");});$("#ruleListId input:checkbox").removeAttr('checked');active_rules.each(function(index,value){$("#ruleListId input:checkbox[value="+value+"]").prop('checked',true).parents("li").attr('data-index',index);});$("#ruleListId ul").html(lists.sort(function(a,b){if($(a).data("index")<$(b).data("index")){return-1;}
if($(a).data("index")>$(b).data("index")){return 1;}
return 0;}));};$("#ruleListSortContainer").show();$("#ruleListIdContainer").hide();self.init_rule_list();$("#available_rule").empty();$.each(self.rules_available,function(index,value){$("#available_rule").append(self.generate_rule_element(value.name,value.id,value.value));});$("#selected_rule").empty();$.each(self.rules_selected,function(index,value){$("#selected_rule").append(self.generate_rule_element(value.name,value.id,value.value));});$(".rulelist > li > a.btn").click(function(e){var $this=$(this);e.preventDefault();e.stopPropagation();if($this.parents("ul#available_rule").length>0){$this.parent().appendTo($("#selected_rule"));}else if($this.parents("ul#selected_rule").length>0){$this.parent().appendTo($("#available_rule"));}
updateForm();});if($("#ruleListId > div.form-group.error").length>0){var errortext=$("#ruleListId > div.form-group.error").find("span.help-block").text();$("#selected_rule_h4").before($('<div class="dynamic-error">').html(errortext));}
$(".rulelist").sortable({connectWith:"ul.rulelist",placeholder:"ui-state-highlight",distance:5,start:function(e,info){$("#selected_rule").addClass("dragging");},stop:function(e,info){$("#selected_rule").removeClass("dragging");updateForm();}}).disableSelection();},workflow_init:function(modal){horizon.firewalls.generate_rulelist_html();}};horizon.addInitFunction(function(){$(document).on('submit','#tail_length',function(evt){horizon.firewalls.user_decided_length=true;horizon.firewalls.getConsoleLog(true);evt.preventDefault();});});(function(){'use strict';horizonApp.controller('ImageFormCtrl',['$scope',function($scope){$scope.selectImageFormat=function(path){if(!path){return;}
var format=path.substr(path.lastIndexOf(".")+1).toLowerCase().replace(/[^a-z0-9]+/gi,"");if($('#id_disk_format').find('[value='+format+']').length!==0){$scope.diskFormat=format;}else{$scope.diskFormat="";}};}]);horizonApp.directive('imageFileOnChange',function(){return{require:'ngModel',restrict:'A',link:function($scope,element,attrs,ngModel){element.bind('change',function(event){var files=event.target.files,file=files[0];ngModel.$setViewValue(file);$scope.$apply();});}};});}());