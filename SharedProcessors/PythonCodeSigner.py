#!/usr/bin/env python
# coding: utf-8

import asyncio
import glob
import os
import shlex
import sys

from autopkglib import Processor, ProcessorError
from asyncio.subprocess import PIPE


class ShellCommander(object):
    """
    """
    async def start(self, cmd, cmd_args=[], input_bytes=None):
        """
        """
        args = __class__.escape_args(*cmd_args)

        command = f"{cmd} {args}"

        proc = await asyncio.create_subprocess_shell(command, stdin=PIPE,
                                                     stdout=PIPE, stderr=PIPE)

        stdout_data, stderr_data = await proc.communicate(input_bytes)

        if stdout_data:
            print(stdout_data.decode("utf-8"))

        if stderr_data:
            print(stderr_data.decode("utf-8"), file=sys.stderr)

        return True if proc.returncode is 0 else False

    @classmethod
    def escape_args(cls, *args):
        """
        """
        escaped_args = [shlex.quote(str(arg)) for arg in args]

        return " ".join(escaped_args)


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

    def main(self):
        """
        """
        print(self.env)
        self.cert = self.env["signing_cert"]
        self.python_path = self.env["python_framework_path"]

        asyncio.run(self.scheduler())

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
            l = [f for f in os.listdir(e) \
                 if os.path.isfile(f) and os.access(f, os.X_OK)]
            files = [*files, *l]

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
        while not queue.empty():
            filename = await queue.get()

            args = ["--force", "--deep", "--verbose", "-s", self.cert, filename]

            p = ShellCommander()
            r = await p.start("/usr/bin/codesign", args)

            queue.task_done()


if __name__ == "__main__":
    processor = PythonCodeSigner()
    processor.execute_shell()
