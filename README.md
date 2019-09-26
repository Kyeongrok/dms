# Volvo Cars and Zenuity (VCCZ) ADAC project

This repository contains the main software components for the project.

Below is a short description of what you will find in each root directories.

- `bootstrap` contains scripts and instructions used by Virtustream to provision and initialize some project components.
- `dmsclient` contains the Python library that provides interfaces to the Data Management System (DMS) and is used for ingestion and for further processing in the compute nodes.
- `docs` contains Sphinx documentation about administration, configuration, and installation of the DMS components.
- `ingest` contains the ingestion software including the Python package, the Bash wrapper, the udev trigger, and the CLI utility.
- `legacy` contains the former ingest scripts, created by Volvo Cars and Zenuity.
- `samples` contains various Bash and Python scripts to generate and obtain DMS data for testing purposes.


For general project documentation or other concerns, please contact Agron Sylaj (agron.sylaj@dell.com) and Don Gray (don.gray@dell.com).
