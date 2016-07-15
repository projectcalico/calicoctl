// Copyright (c) 2016 Tigera, Inc. All rights reserved.

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package common

const (
	DefaultTierName = ".default"
	blank           = ""
)

// Return the tier name, or the default if blank.
func TierOrDefault(tier string) string {
	if tier == blank {
		return DefaultTierName
	} else {
		return tier
	}
}

// Return the tier name, or blank if the default.
func TierOrBlank(tier string) string {
	if tier == DefaultTierName {
		return blank
	} else {
		return tier
	}
}
