# Copyright 2018 Comcast Cable Communications Management, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import tokenize

license_to_check =  "http://www.apache.org/licenses/LICENSE-2.0"

missing_license = False

#checks if the license_to_check is in a comment in the files
def is_string_in_comment(file_path, target_string):
    with tokenize.open(file_path) as file:
        # Loop through every token in the Python file
        for token in tokenize.generate_tokens(file.readline):
            # Check if the current token is a comment
            if token.type == tokenize.COMMENT:
                # Check if apache link string is inside that comment
                if target_string in token.string:
                    return True
    return False

#Iterate through the .py files passed by the .pre-commit-config.yaml file
for filepath in sys.argv[1:]:
    with open(filepath, "r", encoding="utf-8") as f:

        #if license is not in header print it out in the pre commit error
        if not is_string_in_comment(filepath, license_to_check):
            print(f"Error: Missing Apache License header in {filepath}")
            missing_license = True

if missing_license:
    sys.exit(1)