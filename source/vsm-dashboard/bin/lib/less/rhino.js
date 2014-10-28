
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

var name;

function loadStyleSheet(sheet, callback, reload, remaining) {
    var sheetName = name.slice(0, name.lastIndexOf('/') + 1) + sheet.href;
    var input = readFile(sheetName);
    var parser = new less.Parser({
        paths: [sheet.href.replace(/[\w\.-]+$/, '')]
    });
    parser.parse(input, function (e, root) {
        if (e) {
            print("Error: " + e);
            quit(1);
        }
        callback(root, sheet, { local: false, lastModified: 0, remaining: remaining });
    });

    // callback({}, sheet, { local: true, remaining: remaining });
}

function writeFile(filename, content) {
    var fstream = new java.io.FileWriter(filename);
    var out = new java.io.BufferedWriter(fstream);
    out.write(content);
    out.close();
}

// Command line integration via Rhino
(function (args) {
    name = args[0];
    var output = args[1];

    if (!name) {
        print('No files present in the fileset; Check your pattern match in build.xml');
        quit(1);
    }
    path = name.split("/");path.pop();path=path.join("/")

    var input = readFile(name);

    if (!input) {
        print('lesscss: couldn\'t open file ' + name);
        quit(1);
    }

    var result;
    var parser = new less.Parser();
    parser.parse(input, function (e, root) {
        if (e) {
            quit(1);
        } else {
            result = root.toCSS();
            if (output) {
                writeFile(output, result);
                print("Written to " + output);
            } else {
                print(result);
            }
            quit(0);
        }
    });
    print("done");
}(arguments));
