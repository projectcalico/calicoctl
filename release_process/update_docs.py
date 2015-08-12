import os
import re
import sys

# The heading indicator
HEADING = "##"

# Determine required paths
our_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.dirname(our_dir)
calico_containers_dir = os.path.join(root_dir, "calico_containers")
calicoctl_py = os.path.join(calico_containers_dir, "calicoctl.py")

# Add the containers path before importing calicoctl
sys.path.append(calico_containers_dir)
import calicoctl


def get_pre_post_section(filename, heading):
    """
    Extract the text before and after the section specified by the supplied
    heading.

    :param filename:  The filename of the MD file.
    :param heading:  The heading text to search for.
    :return: (pre text, post text)
    """
    current = ""
    pre = None
    post = None
    if os.path.exists(filename):
        # Read in the file if it exists.
        with open(filename, "r") as infi:
            current = infi.read()

        # Match everything up to the heading, and after the heading.
        match = re.match("(.*)%s %s\n(.*)" % (HEADING, heading),
                         current,
                         flags=re.DOTALL)
        if match:
            # In the text after the heading, find the next heading and extract
            # the text from that heading onwards.  There may be no heading,
            # in which case there is no post-text.
            pre = match.group(1)

            match = re.match(".*?\n(#.*)", match.group(2), flags=re.DOTALL)
            if match:
                post = match.group(1)
            else:
                print "  Could not find any follow-on sections in document"
        else:
            print "  Could not find existing section in document"

    return (pre if pre is not None else current, post or "")


def update_help(filename, subcommand, doc):
    """
    Update the help text section in the specified file.
    :param filename:   The filename of the MD file to update.
    :param subcommand: The calicoctl sub-command.  If None then this is the
    top level calicoctl command.
    :param doc:  The new doc string for the command.
    """
    print "Updating help: %s" % filename

    if subcommand:
        subcommand_desc = "calicoctl %s" % subcommand
        heading = "Displaying the help text for 'calicoctl %s' commands" % subcommand
    else:
        subcommand_desc = "top level calicoctl"
        heading = "Top level help"

    # Read the current file to find the sections before and after the existing
    # help section.
    pre, post = get_pre_post_section(filename, heading)

    # Write out the file with an updated help section.
    with open(filename, "w") as outfi:
        if not pre and subcommand:
            outfi.write("""
# User guide for 'calicoctl %s' commands

This sections describes the `calicoctl %s` commands.

Read the [calicoctl command line interface user guide](../calicoctl.md) for a full list of calicoctl commands.

""" % (subcommand, subcommand))

        outfi.write(pre)
        outfi.write("""%s %s

Run

    calicoctl %s--help

to display the following help menu for the %s commands.

```
%s
```

""" % (HEADING, heading, subcommand + " " if subcommand else "", subcommand_desc, doc))
        outfi.write(post)

        # If there are no post sections and this is a sub-command MD file, then
        # add placeholders for each of the commands.
        if not post and subcommand:
            print "  Writing placeholder sections for sub commands"
            outfi.write("## calicoctl %s commands\n\n" % subcommand)
            for summary, full in get_sub_commands(doc):
                print "    %s" % summary
                options = set(re.findall("(<.*?>)", full))
                outfi.write("""
### %s
This command


Command syntax:

```
%s

    %s
```

Examples:

```
%s
```
"""
 % (summary, full, "\n    ".join(options), summary))

def update_toc(filename, commands):
    """
    Update the table of contents in the top level calicoctl document.
    :param filename: The calicoctl document.
    :param commands: The list of commands.
    """
    print "Updating TOC: %s" % filename

    # Read the current file to find the sections before and after the existing
    # table of contents section.
    heading = "Top level command line options"
    pre, post = get_pre_post_section(filename, heading)

    # Write out the file with an updated TOC.
    with open(filename, "w") as outfi:
        outfi.write(pre)
        outfi.write("""
%s %s

Details on the `calicoctl` commands are described in the documents linked below
organized by top level command.

""" % (HEADING, heading))
        for command in commands:
            outfi.write("-  [calicoctl %s](%s)\n" % (command,
                                         get_commmand_md_relative(command)))
        outfi.write("\n")
        outfi.write(post)


def get_top_level_commands():
    """
    Return a list of the top level commands parsed from the main calicoctl
    doc string.
    """
    doc = calicoctl.__doc__
    commands = None
    for line in doc.split("\n"):
        if line.startswith("Usage:"):
            commands = []
            continue
        if commands is None:
            continue
        if not line.strip():
            continue
        match = re.match("    (\w*) ", line)
        if not match:
            break
        commands.append(match.group(1))

    return commands


def get_sub_commands(doc):
    """
    Return a list of the sub commands parsed from the doc string.

    This is a list of tuples containing the summary command (i.e. to use in
    headings etc.) and the full command (the full syntax).

    :param doc: The doc string to parse.
    :return: [(summary, full), ... ]
    """
    commands_summary = None
    commands_full = None
    for line in doc.split("\n"):
        if line.startswith("Usage:"):
            commands_summary = []
            commands_full = []
            continue
        if commands_summary is None:
            assert commands_full is None
            continue

        # Blank line marks the end of the usage string.
        if not line.strip():
            break

        # Commands are indented with 2 spaces.
        if not line.startswith("  "):
            continue
        line = line[2:]

        # Continuations are indented with > 2 spaces.
        if line.startswith(" "):
            commands_full[-1] = commands_full[-1] + "\n" + line
            continue

        # Get the summary command first.  All non-optional segments.
        match = re.match("([-<>\w ]*)", line.rstrip())
        if not match:
            assert "Cannot parse line: %s" % line
        commands_summary.append(match.group(1))

        # The full command is the full line.
        commands_full.append(line.strip())

    return zip(commands_summary, commands_full)


def get_command_md(command):
    """
    Return the path to the MD document for the specific command.

    :param command: The command.
    :return: Path to document.
    """
    return os.path.join(root_dir, "docs", "calicoctl", "%s.md" % command)


def get_commmand_md_relative(command):
    """
    Return the path to the MD document for the specific command relative
    to the directory containing the main calicoctl document.

    :param command: The command.
    :return: Path to document.
    """
    return os.path.join("calicoctl", "%s.md" % command)


if __name__ == '__main__':
    """
    Parse the calicoctl doc strings and update the calicoctl documentation
    with the latest help text.

    This should be done after making any updates to the calicoctl commands,
    and as part of the release process.

    If this applies any changes to the documentation files it is necessary to
    check the updated text byu hand and apply any manual updates as necessary.
    """
    # Determine the set of top level sub commands.
    commands = get_top_level_commands()

    # Start with the calicoctl doc string, update the help text in the main
    # calicoctl help file.
    calicoctl_md = os.path.join(root_dir, "docs", "calicoctl.md")
    update_help(calicoctl_md, None, calicoctl.__doc__)

    # Loop through and update all of the sub commands help texts.
    for command in commands:
        command_module = getattr(calicoctl.calico_ctl, command)
        update_help(get_command_md(command), command, command_module.__doc__)

    # Update the table of contents.
    update_toc(calicoctl_md, commands)
