#!/usr/bin/env python
# coding: utf-8

from xml.etree import ElementTree as ET
from autopkglib import Processor, ProcessorError


class PackageInfoReader(Processor):
    """
    Try to retrieve the version and the package identifier from a PackageInfo.
    You'd probably want to use FlatPkgUnpacker processor before this one.
    """

    description = __doc__

    input_variables = {
        "pkginfo_path": {
            "required": True,
            "description": (
                "Path to PackageInfo file, probably extracted from a bundle/distribution package.",
            ),
        }
    }
    output_variables = {
        "pkg_id": {
            "description": "Package identifier of the package."
        },
        "version": {
            "description": "Version of the package."
        }
    }

    def main(self):
        """
        """
        try:
            tree = ET.parse(self.env["pkginfo_path"])
        except IOError as err:
            raise ProcessorError(err)

        pkginfo = tree.find("pkg-info")

        if pkginfo is not None:
            try:
                self.env["version"] = pkginfo.attrib["version"]
                self.output(f"Found package version: {self.env['version']}.")
            except KeyError as e:
                pass

            try:
                self.env["pkg_id"] = pkginfo.attrib["identifier"]
                self.output(f"Found package identifier: {self.env['pkg_id']}.")
            except KeyError as e:
                pass


if __name__ == "__main__":
    p = PackageInfoVersioner()
    p.execute_shell()
