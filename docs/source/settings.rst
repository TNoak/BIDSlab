Settings Module
===============

The Settings module provides configuration and customization options for the aBIDSkit package.
It allows users and developers to configure package behavior, control default options, and
manage application-level settings.

Overview
--------

The Settings module handles:

- **Package configuration** - Control default behavior and options
- **Settings management** - Get, set, and save configuration values
- **Environment-specific settings** - Support for different configurations across environments
- **Persistence** - Load and save settings to configuration files

Core Components
---------------

**Settings Class**
  Main configuration class that manages all package-level settings. Provides methods to
  get, set, and persist configuration values.

**PackageFetching Enum**
  Enumeration of options for how the package fetches remote resources
  (e.g., specifications from BIDS repositories).

**PackageLoading Enum**
  Enumeration of options for the format in which loaded data is returned
  (e.g., dataframes vs. arrays).

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from abidskit.settings import Settings, get_settings_value, set_settings_values

   # Get current settings
   settings = Settings()
   print(settings)

   # Get a specific setting
   value = get_settings_value("setting_name")

   # Set a configuration value
   set_settings_values({"setting_name": "new_value"})

   # Override settings temporarily
   from abidskit.settings import override_settings_values
   with override_settings_values({"setting_name": "temp_value"}):
       # Code here uses temporary settings
       pass

Module API
----------

.. automodule:: bidslab.settings
   :show-inheritance: True

Best Practices
~~~~~~~~~~~~~~

When working with settings:

1. Use configuration files for persistent settings
2. Use override contexts for temporary changes
3. Validate settings values before applying them
4. Document custom settings for team members
5. Use sensible defaults for all configuration options
