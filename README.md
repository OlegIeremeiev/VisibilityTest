# VisibilityTest

Image visibility test

## System requirements

1. Python 3.11+
2. Internet access to download images from the cloud

## Installation

1. Clone the repository or just download the `VisibilityTest.pyw` file
2. Install dependencies from the file `requirements.txt` in the repository
    ```shell
    pip install -r requirements.txt
    ```
    or install directly
    ```shell
    pip install requests Pillow PyYAML
    ```
3. For Linux systems additional step: to install some basic packages from OS repository for supporting the default Python and Tkinter package (Tkinter, Tk and ImageTk). In Windows they are preinstalled with Python.
   Command example for Ubuntu:
   ```
   sudo apt install python3-tk python3-pil.imagetk
   ```
   For other Linux distributions names of these packages may be slightly differ 

## Usage

1. Launch \
   **Windows**: directly run the `VisibilityTest.pyw` file \
   **Linux**: launch from the terminal `python VisibilityTest.pyw`
2. Read the instruction in the app
3. Complete the survey required for the experiment to determine the conditions
4. Download images and start the experiment

## Current issues

Some images may be broken during download, and the download process may be infinitive due to deleting corrupted files and re-downloading them. 
In this case, download the entire archive directly from the given link.