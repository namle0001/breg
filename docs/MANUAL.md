# Manual

## Setting Up BReg

To set up BReg, a project directory must be presented. At there, BReg will store its configuration, environment, data, ... etc.

### Environment

BReg requires a configuration file, and an environment file to be set up in the project directory.
The default names for these files are `breg.conf` and `.env` respectively, but they can be customized via command-line arguments.

Both files are in the standard INI format. (See [INI File Format](https://en.wikipedia.org/wiki/INI_file) for more details.)

## Architecture Overview

Breg is structured into modules by levels of abstraction and functional capability:

-   **breg.core**: Contains fundamental data structures and utilities used throughout the system.
-   **breg.processor**: Implements the main processing logic, including planning and scheduling algorithms.
-   **breg.macro**: Provides high-level functionalities that combine multiple processing steps for ease of use.
-   **breg.ui**: Manages user interactions, input/output operations, and external integrations
