#!/usr/bin/expect -f

# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

spawn gpg --gen-key

expect "Your selection?"
send "\r"

expect "What keysize do you want? (2048)"
send "\r"

expect "Key is valid for? (0)"
send "\r"

expect "Is this correct? (y/N)"
send "y\r"

expect "Real name:"
send "vsm@intel.com\r"

expect "Email address:"
send "vsm@intel.com\r"

expect "Comment:"
send "vsm_project\r"

expect "Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit?"
send "O\r"

expect "Passphrase"
send "%VSM_GPG_PASSWORD%\r"

