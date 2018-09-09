package ipam

import (
	flag "github.com/spf13/pflag"

	"github.com/projectcalico/calicoctl/calicoctl/commands/constants"
)

// ipamArgs defines the set of args for an ipam command
type ipamArgs struct {
	ip, config *string
}

// newIPAMArgs parses a flagset to generate a ipamArgs instance
func newIPAMArgs(fs *flag.FlagSet) ipamArgs {
	return ipamArgs{
		ip: fs.String("ip", "", "Specifies the IP address to use"),
		config: fs.StringP(
			"config", "c", constants.DefaultConfigPath,
			"Path to the file containing connection configuration in YAML or JSON format."),
	}
}
