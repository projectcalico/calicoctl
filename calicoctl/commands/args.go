package commands

import (
	flag "github.com/spf13/pflag"

	"github.com/projectcalico/calicoctl/calicoctl/commands/constants"
)

// mapable defines the interface to maintain backward compatability with the docopt implementation
type mapable interface {
	mapArgs() map[string]interface{}
}

// baseResourceArgs defines the base set of args for a resource-based command
// (apply, create, delete, get, replace)
type baseResourceArgs struct {
	filename, config, namespace *string
}

// newBaseResourceArgs parses a flagset to generate a baseResourceArgs instance
func newBaseResourceArgs(fs *flag.FlagSet) baseResourceArgs {
	return baseResourceArgs{
		filename: fs.StringP(
			"filename", "f", "",
			"Filename to use to apply the resource"),
		config: fs.StringP(
			"config", "c", constants.DefaultConfigPath,
			"Path to the file containing connection configuration in YAML or JSON format."),
		namespace: fs.StringP(
			"namespace", "n", "",
			"Filename to use to apply the resource"),
	}
}

// mapArgs converts the baseResourceArgs to map[string]interface{}
func (args baseResourceArgs) mapArgs() map[string]interface{} {
	return map[string]interface{}{
		"--filename":  *args.filename,
		"--config":    *args.config,
		"--namespace": *args.namespace,
	}
}

// getResourceArgs defines the extended set of args for a "get" command
type getResourceArgs struct {
	baseResourceArgs
	allNamespaces, export *bool
	output                *string
}

// newGetResourceArgs parses a flagset to generate a getResourceArgs instance
func newGetResourceArgs(fs *flag.FlagSet) getResourceArgs {
	return getResourceArgs{
		baseResourceArgs: newBaseResourceArgs(fs),
		allNamespaces: fs.BoolP(
			"all-namespaces", "a", false,
			"If present, list the requested object(s) access all nammespaces"),
		export: fs.BoolP(
			"export", "e", false,
			`If present, returns the requested object(s) stripped of cluster-specific information. 
This flag will be ignored if <NAME> is not specified`),
		output: fs.StringP(
			"output", "o", "ps",
			`Output format. One of: yaml, json, ps, wide, 
custom-columns=..., go-template=..., go-template-file=... [Default: ps]`),
	}
}

// mapArgs converts the getResourceArgs to map[string]interface{}
func (args getResourceArgs) mapArgs() map[string]interface{} {
	m := args.baseResourceArgs.mapArgs()
	m["--all-namespaces"] = *args.allNamespaces
	m["--export"] = *args.export
	m["--output"] = *args.output
	return m
}

// createResourceArgs defines the extended set of args for a "create" command
type createResourceArgs struct {
	baseResourceArgs
	skipExists *bool
}

// newCreateResourceArgs parses a flagset to generate a createResourceArgs instance
func newCreateResourceArgs(fs *flag.FlagSet) createResourceArgs {
	return createResourceArgs{
		baseResourceArgs: newBaseResourceArgs(fs),
		skipExists: fs.Bool(
			"skip-exists", false,
			"Skip over and treat as successful any attempts to create an entry that already exists"),
	}
}

// mapArgs converts the createResourceArgs to map[string]interface{}
func (args createResourceArgs) mapArgs() map[string]interface{} {
	m := args.baseResourceArgs.mapArgs()
	m["--skip-exists"] = *args.skipExists
	return m
}

// deleteResourceArgs defines the extended set of args for a "delete" command
type deleteResourceArgs struct {
	baseResourceArgs
	skipNotExists *bool
}

// newDeleteResourceArgs parses a flagset to generate a deleteResourceArgs instance
func newDeleteResourceArgs(fs *flag.FlagSet) deleteResourceArgs {
	return deleteResourceArgs{
		baseResourceArgs: newBaseResourceArgs(fs),
		skipNotExists: fs.Bool(
			"skip-not-exists", false,
			"Skip over and treat as successful, resources that don't exist."),
	}
}

// mapArgs converts the deleteResourceArgs to map[string]interface{}
func (args deleteResourceArgs) mapArgs() map[string]interface{} {
	m := args.baseResourceArgs.mapArgs()
	m["--skip-not-exists"] = *args.skipNotExists
	return m
}

// convertArgs defines the set of args for a "convert" command
type convertArgs struct {
	filename, output *string
	ignoreValidation *bool
}

// newConvertArgs parses a flagset to generate a deleteResourceArgs instance
func newConvertArgs(fs *flag.FlagSet) convertArgs {
	return convertArgs{
		filename: fs.StringP(
			"filename", "f", "",
			`Filename to use to create the resource. If set to "-" loads from stdin.`),
		output: fs.StringP(
			"output", "o", "yaml",
			"Output format. One of: yaml or json."),
		ignoreValidation: fs.Bool(
			"ignore-validation", false, "Skip validation on the converted manifest."),
	}
}

// mapArgs converts the convertArgs to map[string]interface{}
func (args convertArgs) mapArgs() map[string]interface{} {
	return map[string]interface{}{
		"--filename":          *args.filename,
		"--output":            *args.output,
		"--ignore-validation": *args.ignoreValidation,
	}
}
