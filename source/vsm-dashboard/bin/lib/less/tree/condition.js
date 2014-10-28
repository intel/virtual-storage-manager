
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

tree.Condition = function (op, l, r, i, negate) {
    this.op = op.trim();
    this.lvalue = l;
    this.rvalue = r;
    this.index = i;
    this.negate = negate;
};
tree.Condition.prototype.eval = function (env) {
    var a = this.lvalue.eval(env),
        b = this.rvalue.eval(env);

    var i = this.index, result;

    var result = (function (op) {
        switch (op) {
            case 'and':
                return a && b;
            case 'or':
                return a || b;
            default:
                if (a.compare) {
                    result = a.compare(b);
                } else if (b.compare) {
                    result = b.compare(a);
                } else {
                    throw { type: "Type",
                            message: "Unable to perform comparison",
                            index: i };
                }
                switch (result) {
                    case -1: return op === '<' || op === '=<';
                    case  0: return op === '=' || op === '>=' || op === '=<';
                    case  1: return op === '>' || op === '>=';
                }
        }
    })(this.op);
    return this.negate ? !result : result;
};

})(require('../tree'));
