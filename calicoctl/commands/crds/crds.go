// Copyright (c) 2020 Tigera, Inc. All rights reserved.

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

package crds

import (
	"k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1beta1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// TODO: Generate these from the CRDs generated in libcalico-go
var (
	BGPConfigurationCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "bgpconfigurations.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "BGPConfiguration",
				Plural:   "bgpconfigurations",
				Singular: "bgpconfiguration",
			},
		},
	}
	BGPPeerCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "bgppeers.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "BGPPeer",
				Plural:   "bgppeers",
				Singular: "bgppeer",
			},
		},
	}
	BlockAffinityCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "blockaffinities.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "BlockAffinity",
				Plural:   "blockaffinities",
				Singular: "blockaffinity",
			},
		},
	}
	ClusterInformationCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "clusterinformations.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "ClusterInformation",
				Plural:   "clusterinformations",
				Singular: "clusterinformation",
			},
		},
	}
	FelixConfigurationCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "felixconfigurations.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "FelixConfiguration",
				Plural:   "felixconfigurations",
				Singular: "felixconfiguration",
			},
		},
	}
	GlobalNetworkPolicyCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "globalnetworkpolicies.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:       "GlobalNetworkPolicy",
				Plural:     "globalnetworkpolicies",
				Singular:   "globalnetworkpolicy",
				ShortNames: []string{"gnp"},
			},
		},
	}
	GlobalNetworkSetCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "globalnetworksets.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "GlobalNetworkSet",
				Plural:   "globalnetworksets",
				Singular: "globalnetworkset",
			},
		},
	}
	HostEndpointCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "hostendpoints.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "HostEndpoint",
				Plural:   "hostendpoints",
				Singular: "hostendpoint",
			},
		},
	}
	IPAMBlockCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "ipamblocks.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "IPAMBlock",
				Plural:   "ipamblocks",
				Singular: "ipamblock",
			},
		},
	}
	IPAMConfigCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "ipamconfigs.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "IPAMConfig",
				Plural:   "ipamconfigs",
				Singular: "ipamconfig",
			},
		},
	}
	IPAMHandleCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "ipamhandles.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "IPAMHandle",
				Plural:   "ipamhandles",
				Singular: "ipamhandle",
			},
		},
	}
	IPPoolCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "ippools.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "IPPool",
				Plural:   "ippools",
				Singular: "ippool",
			},
		},
	}
	KubeControllersConfigurationCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "kubecontrollersconfigurations.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.ClusterScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "KubeControllersConfiguration",
				Plural:   "kubecontrollersconfigurations",
				Singular: "kubecontrollersconfiguration",
			},
		},
	}
	NetworkPolicyCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "networkpolicies.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.NamespaceScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "NetworkPolicy",
				Plural:   "networkpolicies",
				Singular: "networkpolicy",
			},
		},
	}
	NetworkSetCRD v1beta1.CustomResourceDefinition = v1beta1.CustomResourceDefinition{
		TypeMeta: metav1.TypeMeta{Kind: "CustomResourceDefinition", APIVersion: "apiextensions.k8s.io/v1beta1"},
		ObjectMeta: metav1.ObjectMeta{
			Name: "networksets.crd.projectcalico.org",
		},
		Spec: v1beta1.CustomResourceDefinitionSpec{
			Group:   "crd.projectcalico.org",
			Scope:   v1beta1.NamespaceScoped,
			Version: "v1",
			Names: v1beta1.CustomResourceDefinitionNames{
				Kind:     "NetworkSet",
				Plural:   "networksets",
				Singular: "networkset",
			},
		},
	}

	CalicoCRDs []*v1beta1.CustomResourceDefinition = []*v1beta1.CustomResourceDefinition{
		&BGPConfigurationCRD,
		&BGPPeerCRD,
		&BlockAffinityCRD,
		&ClusterInformationCRD,
		&FelixConfigurationCRD,
		&GlobalNetworkPolicyCRD,
		&GlobalNetworkSetCRD,
		&HostEndpointCRD,
		&IPAMBlockCRD,
		&IPAMConfigCRD,
		&IPAMHandleCRD,
		&IPPoolCRD,
		&KubeControllersConfigurationCRD,
		&NetworkPolicyCRD,
		&NetworkSetCRD,
	}
)
