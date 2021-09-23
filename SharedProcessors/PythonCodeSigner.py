#!/usr/bin/env python
# coding: utf-8

import asyncio
import glob
import os
import shlex
import sys

from autopkglib import Processor, ProcessorError
from asyncio.subprocess import PIPE


class PythonCodeSigner(Processor):
    """
    Use `codesign` to sign the Python framework."
    """
    description = __doc__

    input_variables = {
        "signing_cert": {
            "required": True,
            "description": "Name of the certificate used to sign the files. MUST be an EXACT match."
        },
        "python_framework_path": {
            "required": True,
            "description": "Path to Python framework."
        },
    }

    output_variables = {}

    cmd = "/usr/bin/codesign"
    cmd_args = ["--force", "--deep", "--verbose", "-s"]

    def main(self):
        """
        """
        self.cert = self.env["signing_cert"]
        self.python_path = self.env["python_framework_path"]

        if self.cert:
            asyncio.run(self.scheduler())
        # else we do nothing.

    async def scheduler(self):
        """
        """
        files = []

        execs = (
            f"{self.python_path}/bin",
            f"{self.python_path}/lib"
        )

        patterns = (
            f"{self.python_path}/lib/**/*dylib",
            f"{self.python_path}/lib/**/*so"
        )

        # We need to codesign the executables files in `bin` and `lib`:
        for e in execs:
            for f in os.listdir(e):
                fp = os.path.join(e, f)

                if os.path.isfile(fp) and os.access(fp, os.X_OK):
                    files.append(fp)

        # We also need to codesign a few librairies:
        for p in patterns:
            l = glob.glob(p, recursive=True)
            files = [*files, *l]

        q = asyncio.Queue()

        for f in files:
            q.put_nowait(f)

        tasks = []

        for i in range(3):
            task = asyncio.create_task(self.worker(q))
            tasks.append(task)

        await q.join()

        # Cancel worker tasks
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

    async def worker(self, queue):
        """
        """
        cargs = self.cmd_args.copy()
        cargs.append(self.cert)

        while not queue.empty():
            filename = await queue.get()

            cargs.append(filename)
            args = __class__.escape_args(*cargs)
            command = f"{self.cmd} {args}"

            proc = await asyncio.create_subprocess_shell(command,
                                                         stdin=PIPE,
                                                         stdout=PIPE,
                                                         stderr=PIPE)

            stdout_data, stderr_data = await proc.communicate(None)

            if stdout_data:
                self.output(stdout_data.decode("utf-8"), verbose_level=2)

            if stderr_data:
                self.output(stderr_data.decode("utf-8"), verbose_level=1)

            queue.task_done()

    @classmethod
    def escape_args(cls, *args):
        """
        """
        escaped_args = [shlex.quote(str(arg)) for arg in args]

        return " ".join(escaped_args)


if __name__ == "__main__":
    processor = PythonCodeSigner()
    processor.execute_shell()
