#!/usr/bin/python3

import subprocess
import os
import time
import shutil

from tempfile import mkdtemp
from contextlib import contextmanager
from productmd.treeinfo import TreeInfo, Variant
from rpmfluff import SimpleRpmBuild, SourceFile


FEDORA_REPO_NAME = "Fedora"
ARCH = "x86_64"

TREE_INFO_FILE_NAME = "treeinfo"
CUSTOM_REPO_NAME = "Custom"


# Sources:
#
# /usr/bin/genisoimage -untranslated-filenames -volid RHEL-8-0-0-BaseOS-x86_64 -J -joliet-long -rational-rock -translation-table -input-charset utf-8 -x ./lost+found -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -eltorito-alt-boot -e images/efiboot.img -no-emul-boot -o RHEL-8.0.0-20190404.2-x86_64-dvd1.iso -graft-points -path-list /mnt/redhat/rhel-8/devel/candidate-trees/RHEL-8/RHEL-8.0.0-20190404.2/work/x86_64/iso/RHEL-8.0.0-20190404.2-x86_64-dvd1.iso-graft-points
#
# /usr/bin/isohybrid --uefi RHEL-8.0.0-20190404.2-x86_64-dvd1.iso
# /usr/bin/implantisomd5 --supported-iso RHEL-8.0.0-20190404.2-x86_64-dvd1.iso

def _make_subprocess_call(command):
    print("------------------------")
    print("Running:\n'{}'".format(" ".join(command)))
    ret = subprocess.run(command)
    print("------------------------")

    ret.check_returncode()


def create_treeinfo(path):
    ti = TreeInfo()

    ti.release.name = "Fedora"
    ti.release.short = "Fedora"
    ti.release.version = "31"

    ti.tree.arch = ARCH
    ti.tree.build_timestamp = time.time()
    ti.tree.platforms.add(ARCH)

    images = {"efiboot.img": "images/efiboot.img",
              "initrd": "images/pxeboot/initrd.img",
              "kernel": "images/pxeboot/vmlinuz"
              }
    ti.images.images[ARCH] = images

    variant = Variant(ti)
    variant.id = "Server"
    variant.uid = "Server"
    variant.name = "Server"
    variant.type = "variant"

    variant.paths.repository = FEDORA_REPO_NAME
    variant.paths.packages = "{}/Packages".format(FEDORA_REPO_NAME)

    ti.variants.add(variant)

    _create_custom_variant(ti)

    ti.dump(path)


def _create_custom_variant(tree_info):
    variant = Variant(tree_info)

    variant.id = CUSTOM_REPO_NAME
    variant.uid = CUSTOM_REPO_NAME
    variant.name = CUSTOM_REPO_NAME
    variant.type = "variant"

    tree_info.variants.add(variant)


def create_custom_repo(temp_dir):
    rpm_file = _create_fake_rpm(temp_dir)
    repo_dir = os.path.join(temp_dir, CUSTOM_REPO_NAME)

    os.mkdir(repo_dir)
    shutil.copy2(rpm_file, repo_dir)

    _create_repo(temp_dir)


def _create_fake_rpm(temp_dir):
    rpm = SimpleRpmBuild(name="test-rpm", version="200", release="9000")
    rpm.add_installed_file(installPath="/usr/bin/TEST",
                           sourceFile=SourceFile(sourceName="TEST",
                                                 content="SO AWESOME APP!")
                           )
    with switch_workdir(temp_dir):
        rpm.make()

    rpm_rel_path = rpm.get_built_rpm(ARCH)
    return os.path.join(temp_dir, rpm_rel_path)


def _create_repo(repo_dir):
    _make_subprocess_call(["createrepo_c", repo_dir])


@contextmanager
def switch_workdir(dir):
    """This is a context manager to temporary switch the current directory.

    This function should be used with `with` keyword.
    """
    old_cwd = os.getcwd()
    os.chdir(dir)
    yield
    os.chdir(old_cwd)


def create_temp_dir():
    return mkdtemp(prefix="dvd_iso-")


def remove_temp_dir(temp_dir):
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    temp_dir = create_temp_dir()

    # tree_info_path = os.path.join(temp_dir, TREE_INFO_FILE_NAME)
    # create_treeinfo(tree_info_path)
    create_custom_repo(temp_dir)

    print("Everything created in", temp_dir)
