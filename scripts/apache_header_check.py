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

license_to_check_18 = ['Copyright 2018 Comcast Cable Communications Management, LLC',
                       'Licensed under the Apache License, Version 2.0 (the "License");',
                       'you may not use this file except in compliance with the License.',
                       'You may obtain a copy of the License at', '    http://www.apache.org/licenses/LICENSE-2.0',
                       'Unless required by applicable law or agreed to in writing, software',
                       'distributed under the License is distributed on an "AS IS" BASIS,',
                       'WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.',
                       'See the License for the specific language governing permissions and',
                       'limitations under the License.']
license_to_check_26 = ['Copyright 2026 Comcast Cable Communications Management, LLC',
                       'Licensed under the Apache License, Version 2.0 (the "License");',
                       'you may not use this file except in compliance with the License.',
                       'You may obtain a copy of the License at', '    http://www.apache.org/licenses/LICENSE-2.0',
                       'Unless required by applicable law or agreed to in writing, software',
                       'distributed under the License is distributed on an "AS IS" BASIS,',
                       'WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.',
                       'See the License for the specific language governing permissions and',
                       'limitations under the License.']

missing_license = False


#checks if the license_to_check is in a comment in the files
def license_crosscheck(file_path, license_to_check_18, license_to_check_26):
    with tokenize.open(file_path) as file:
        # this list will have all the comments tokens in the file
        license_tokens = []

        # Loop through every token in the Python file
        for token in tokenize.generate_tokens(file.readline):

            # Check if the current token is a comment
            if token.type == tokenize.COMMENT:
                if token.string.startswith("# "):
                    #add the comment to the license_tokens list, removing the leading "# " from the comment
                    license_tokens.append(token.string[2:])

        #if the boiler text exists, the first 10 comment tokens will always be the license tokens

        if license_tokens[:10] == license_to_check_18 or license_tokens[:10] == license_to_check_26:
            return True
        else:
            return False


#Iterate through the .py files passed by the .pre-commit-config.yaml file
for filepath in sys.argv[1:]:
    with open(filepath, "r", encoding="utf-8") as f:

        #check if the first 10 comment tokens in the file match the licenses list for either 2018 or 2026 copyright boiler text
        if not license_crosscheck(filepath, license_to_check_18, license_to_check_26):
            print(f"Error: Missing Apache License header in {filepath}")
            missing_license = True

if missing_license:
    sys.exit(1)
