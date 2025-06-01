from jupyter_client import KernelManager, run_kernel
from jupyter_client.kernelspec import KernelSpecManager
import threading
import re
import os
import base64
import logging
import traceback
from queue import Empty
from typing import List


logger = logging.getLogger(__name__)


class JupyterKernels:
    """A class to manage Jupyter kernels and their specifications.

    This class provides functionality to retrieve and store information about available
    Jupyter kernels, including their display names and supported languages.
    """

    def __init__(self):
        """Initialize the JupyterKernels instance.

        Creates a KernelSpecManager and populates the kernel specifications dictionary
        with information about all available kernels.
        """
        self.ksm = KernelSpecManager()
        self.ks = {}
        all_specs = self.ksm.get_all_specs()
        for ks in all_specs:
            self.ks[ks] = {
                "display_name": all_specs[ks]["spec"]["display_name"],
                "language": all_specs[ks]["spec"]["language"]
            }


class JupyterNotebook:
    """A class to manage Jupyter notebook operations.

    This class provides functionality to execute code cells, manage kernels,
    handle outputs, and manage files generated during execution.
    """

    def __init__(self, kernel_name: str = "python3"):
        """Initialize a JupyterNotebook instance.

        Args:
            kernel_name (str, optional): Name of the kernel to use. Defaults to "python3".
        """
        self.kc = run_kernel(kernel_name=kernel_name).gen
        self.km = next(self.kc)

    def clean_output(self, outputs: List[str | list | dict]):
        """Clean and format the output from code execution.

        Args:
            outputs (list): Raw outputs from code execution, can contain dicts, strings, or lists.

        Returns:
            str: A cleaned string representation of the outputs.
        """
        outputs_only_str = list()
        for i in outputs:
            if type(i) == dict:
                if "text/plain" in list(i.keys()):
                    outputs_only_str.append(i["text/plain"])
            elif type(i) == str:
                outputs_only_str.append(i)
            elif type(i) == list:
                error_msg = "\n".join(i)
                error_msg = re.sub(r"\x1b\[.*?m", "", error_msg)
                outputs_only_str.append(error_msg)

        return "\n".join(outputs_only_str).strip()

    def get_files(self):
        """Get and encode files generated during code execution.

        Reads all files in the current working directory, encodes them in base64,
        and removes them after reading.

        Returns:
            list: List of dictionaries containing file names and their base64-encoded content.
        """
        files = os.listdir(os.getcwd())
        logger.debug(f"Files: {files}")
        content = []
        for file in files:
            file_path = os.path.join(os.getcwd(), file)
            if os.path.isfile(file_path):
                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())
                    content.append({"file": file, "content": encoded_string.decode()})
                os.remove(file_path)
        logger.debug(f"Content: {content}")
        return content

    def install_python_packages(self, packages: List[str], timeout: int = 10):
        """Install Python packages using pip.

        Args:
            packages (list): List of package names to install.
            timeout (int, optional): Timeout in seconds for each package installation. Defaults to 10.

        Returns:
            tuple: (Success status, Timeout flag, Error message) or None if successful.
        """
        for package in packages:
            try:
                resp = self.run_cell(f"!pip install {package}", timeout=timeout)
                if resp[1]:
                    return True, False, resp[1]
            except Empty:
                return True, True, "Package Install Timeout"
        return None

    def install_npm_packages(self, packages: List[str], timeout: int = 30):
        """Install JavaScript packages using npm.

        Args:
            packages (list): List of package names to install.
            timeout (int, optional): Timeout in seconds for each package installation. Defaults to 30.

        Returns:
            tuple: (Success status, Timeout flag, Error message) or None if successful.
        """
        for package in packages:
            try:
                resp = self.run_cell(f"!npm install {package}", timeout=timeout)
                if resp[1]:
                    return True, False, resp[1]
            except Empty:
                return True, True, f"Timeout installing package {package}"
        return None

    def run_cell(self, code_string: str, timeout: int = 10):
        """Execute a code cell in the Jupyter kernel.

        Args:
            code_string (str): The code to execute.
            timeout (int, optional): Timeout in seconds for cell execution. Defaults to 10.

        Returns:
            tuple: (Cleaned output, Error flag, Generated files, Timeout flag)
        """
        # Execute the code and get the execution count
        outputs = []
        error_flag = False
        timeout_flag = False
        # client = next(self.kc)
        client = self.km
        msg_id = client.execute(code_string)

        while True:
            try:
                msg = client.get_iopub_msg(timeout=timeout)

                msg_type = msg["header"]["msg_type"]
                content = msg["content"]

                if msg_type == "execute_result":
                    outputs.append(content["data"])
                elif msg_type == "stream":
                    outputs.append(content["text"])
                elif msg_type == "error":
                    error_flag = True
                    outputs.append(content["traceback"])

                # If the execution state of the kernel is idle, it means the cell finished executing
                if msg_type == "status" and content["execution_state"] == "idle":
                    break
            except Empty:
                outputs.append("Timeout waiting for cell execution")
                error_flag = True
                timeout_flag = True
                break
            except Exception as e:
                logging.error(traceback.format_exc())
                break

        return self.clean_output(outputs), error_flag, self.get_files(), timeout_flag