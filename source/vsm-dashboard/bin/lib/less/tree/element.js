
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

(function (tree) {

tree.Element = function (combinator, value, index) {
    this.combinator = combinator instanceof tree.Combinator ?
                      combinator : new(tree.Combinator)(combinator);

    if (typeof(value) === 'string') {
        this.value = value.trim();
    } else if (value) {
        this.value = value;
    } else {
        this.value = "";
    }
    this.index = index;
};
tree.Element.prototype.eval = function (env) {
    return new(tree.Element)(this.combinator,
                             this.value.eval ? this.value.eval(env) : this.value,
                             this.index);
};
tree.Element.prototype.toCSS = function (env) {
	var value = (this.value.toCSS ? this.value.toCSS(env) : this.value);
	if (value == '' && this.combinator.value.charAt(0) == '&') {
		return '';
	} else {
		return this.combinator.toCSS(env || {}) + value;
	}
};

tree.Combinator = function (value) {
    if (value === ' ') {
        this.value = ' ';
    } else if (value === '& ') {
        this.value = '& ';
    } else {
        this.value = value ? value.trim() : "";
    }
};
tree.Combinator.prototype.toCSS = function (env) {
    return {
        ''  : '',
        ' ' : ' ',
        '&' : '',
        '& ' : ' ',
        ':' : ' :',
        '+' : env.compress ? '+' : ' + ',
        '~' : env.compress ? '~' : ' ~ ',
        '>' : env.compress ? '>' : ' > '
    }[this.value];
};

})(require('../tree'));
