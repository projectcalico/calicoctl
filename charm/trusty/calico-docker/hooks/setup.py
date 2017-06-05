import subprocess


def pre_install():
    install_charmhelpers()
    install_python_modules()


def install_charmhelpers():
    try:
        """
        Install the charmhelpers library, if not present.
        """
        import charmhelpers  # noqa
    except ImportError:
        subprocess.check_call(['apt-get', 'install', '-y', 'python-pip'])
        subprocess.check_call(['pip', 'install', 'charmhelpers'])


def install_python_modules():
    subprocess.check_call(['pip', 'install', 'ansible'])
    subprocess.check_call(['pip', 'install', 'path.py'])
    subprocess.check_call(['pip', 'install', 'docker-py'])
