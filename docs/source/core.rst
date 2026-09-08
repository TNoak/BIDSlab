BIDS core
---------

These subpackages provide the Python implementation for the specification of the BIDS core.

.. rubric:: Common subpackage

This subpackage contains the common specifications shared across all BIDS modalities.

.. toctree::
   :maxdepth: 2

   common.specs_dataset
   common.specs_datatype
   common.specs_misc
   common.specs_phenotype
   common.specs_summary
   common.specs_task
   .. comment
   common.specs_stim

   .. comment
   .. rubric:: Modalities subpackage

   .. comment
   This subpackage contains the specifications for each BIDS modality except for BIDS extensions.

   .. comment
   .. toctree::
     :maxdepth: 2

   .. comment
     modalities.anat
     modalities.beh
     modalities.dwi
     modalities.fmap
     modalities.func
     modalities.perf
