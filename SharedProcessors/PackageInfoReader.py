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
        "pkg_version": {
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

        pkginfo = tree.getroot()

        if pkginfo is not None:
            self.env["pkg_version"] = pkginfo.get("version", None)
            self.env["pkg_id"] = pkginfo.get("identifier", None)

            if self.env["pkg_version"] is not None:
                self.output(f"Found package version: {self.env['pkg_version']}.")

            if self.env["pkg_id"] is not None:
                self.output(f"Found package identifier: {self.env['pkg_id']}.")

if __name__ == "__main__":
    p = PackageInfoReader()
    p.execute_shell()
