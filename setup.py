#!/usr/bin/env python

import os
import shlex
import shutil
import subprocess
import sysconfig
import tarfile

import requests
from Cython.Build import cythonize
from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.extension import Extension


def urlretrieve(source_url, destination_path):
    response = requests.get(source_url, stream=True)
    if response.status_code != 200:
        raise Exception("status code was: {}".format(response.status_code))

    with open(destination_path, "wb") as fileobj:
        for chunk in response.iter_content(chunk_size=128):
            fileobj.write(chunk)

def path_in_dir(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))

def dependency_path(relative_path):
    return os.path.join(path_in_dir("_deps"), relative_path)

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


jq_lib_tarball_path = dependency_path("jq-lib-1.6.tar.gz")
jq_lib_dir = dependency_path("jq-1.6")

oniguruma_version = "6.9.4"
oniguruma_lib_tarball_path = dependency_path("onig-{}.tar.gz".format(oniguruma_version))
oniguruma_lib_build_dir = dependency_path("onig-{}".format(oniguruma_version))
oniguruma_lib_install_dir = dependency_path("onig-install-{}".format(oniguruma_version))

class jq_build_ext(build_ext):
    def run(self):
        if not os.path.exists(dependency_path(".")):
            os.makedirs(dependency_path("."))
        self._build_oniguruma()
        self._build_libjq()
        build_ext.run(self)

    def _build_oniguruma(self):
        self._build_lib(
            source_url="https://github.com/kkos/oniguruma/releases/download/v{0}/onig-{0}.tar.gz".format(oniguruma_version),
            tarball_path=oniguruma_lib_tarball_path,
            lib_dir=oniguruma_lib_build_dir,
            commands=[
                ["./configure", "CFLAGS=-fPIC", "--prefix=" + oniguruma_lib_install_dir],
                ["make"],
                ["make", "install"],
            ])


    def _build_libjq(self):
        self._build_lib(
            source_url="https://github.com/stedolan/jq/releases/download/jq-1.6/jq-1.6.tar.gz",
            tarball_path=jq_lib_tarball_path,
            lib_dir=jq_lib_dir,
            commands=[
                ["autoreconf", "-i"],
                ["./configure", "CFLAGS=-fPIC", "--disable-maintainer-mode", "--with-oniguruma=" + oniguruma_lib_install_dir],
                ["make"],
            ])

    def _build_lib(self, source_url, tarball_path, lib_dir, commands):
        self._download_tarball(
            source_url=source_url,
            tarball_path=tarball_path,
            lib_dir=lib_dir,
        )

        macosx_deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        if macosx_deployment_target:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = macosx_deployment_target

        def run_command(args):
            args = " ".join(shlex.quote(x) for x in args)
            print("Executing: %s" % args)

            subprocess.check_call(["bash", "-exc", args], cwd=lib_dir)

        for command in commands:
            run_command(command)

    def _download_tarball(self, source_url, tarball_path, lib_dir):
        if os.path.exists(tarball_path):
            os.unlink(tarball_path)
        print("Downloading {}".format(source_url))
        urlretrieve(source_url, tarball_path)
        print("Downloaded {}".format(source_url))

        if os.path.exists(lib_dir):
            shutil.rmtree(lib_dir)
        tarfile.open(tarball_path, "r:gz").extractall(dependency_path("."))


jq_extension = Extension(
    "jq",
    sources=["jq.pyx"],
    include_dirs=[os.path.join(jq_lib_dir, "src")],
    extra_link_args=["-lm"],
    extra_objects=[
        os.path.join(jq_lib_dir, ".libs/libjq.a"),
        os.path.join(oniguruma_lib_install_dir, "lib/libonig.a"),
    ],
)

setup(
    name='jq',
    version='1.1.1',
    description='jq is a lightweight and flexible JSON processor.',
    long_description=read("README.rst"),
    author='Michael Williamson',
    url='http://github.com/mwilliamson/jq.py',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    license='BSD 2-Clause',
    ext_modules = cythonize([jq_extension]),
    cmdclass={"build_ext": jq_build_ext},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)

