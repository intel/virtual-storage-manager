
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

import datetime

def get_time_delta(dt):
    try:

        timedelta = datetime.datetime.now() - datetime.datetime.strptime(dt,"%Y-%m-%d %H:%M:%S")
        secs = timedelta.days * 3600 * 24 + timedelta.seconds
        ab = 1 if secs > 0 else -1
        days = abs(secs) / (3600 * 24) * ab
        hours = (abs(secs) - abs(days) * 3600 * 24) / 3600 * ab

        if (hours >= 1) or (days >= 1):
            return str(days) + "days, " + str(hours) + " hours ago"
        minutes = secs / 60
        if minutes >= 1:
            return str(minutes) + " minutes ago"
        return str(secs) + " seconds ago"
    except:
        return dt

def get_time_delta2(dt):
    try:
        timedelta = datetime.datetime.now() - datetime.datetime.strptime(dt,"%Y-%m-%d %H:%M:%S")
        secs = timedelta.days * 3600 * 24 + timedelta.seconds
        ab = 1 if secs > 0 else -1
        days = abs(secs) / (3600 * 24) * ab
        hours = (abs(secs) - abs(days) * 3600 * 24) / 3600 * ab
        if (hours >= 1) or (days >= 1):
            return str(days) + "days, " + str(hours) + " hours"
        minutes = secs / 60
        if minutes >= 1:
            return str(minutes) + " minutes"
        return str(secs) + " seconds"
    except:
        return dt

def get_time_delta3(secs):
    try:
        secs = int(float(secs))
        ab = 1 if secs > 0 else -1
        days = abs(secs) / (3600 * 24) * ab
        hours = (abs(secs) - abs(days) * 3600 * 24) / 3600 * ab
        if (hours >= 1) or (days >= 1):
            return str(days) + "days, " + str(hours) + " hours"
        minutes = secs / 60
        if minutes >= 1:
            return str(minutes) + " minutes"
        return str(secs) + " seconds"
    except:
        return secs