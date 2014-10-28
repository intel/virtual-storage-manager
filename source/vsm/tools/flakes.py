
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

"""
 wrapper for pyflakes to ignore gettext based warning:
     "undefined name '_'"

 Synced in from openstack-common
"""

__all__ = ['main']

import __builtin__ as builtins
import sys

import pyflakes.api
from pyflakes import checker

def main():
    checker.Checker.builtIns = (set(dir(builtins)) |
                                set(['_']) |
                                set(checker._MAGIC_GLOBALS))
    sys.exit(pyflakes.api.main())

if __name__ == "__main__":
    main()
