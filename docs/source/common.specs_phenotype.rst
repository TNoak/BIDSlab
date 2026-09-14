Phenotype Module
================

The Phenotype module provides support for phenotypic and behavioral data such as questionnaire
results in BIDS datasets.
Phenotypic data includes demographic information, clinical assessments, and behavioral scores
that characterize research subjects.

Overview
--------

The Phenotype module handles:

- **Demographic data** - Age, sex, group membership, and other subject characteristics
- **Behavioral scores** - Psychometric assessments and clinical rating scales
- **Clinical measures** - Diagnostic information and clinical outcomes
- **Subject characteristics** - Any descriptive information about participants

Use Cases
~~~~~~~~~

Phenotypic data is used for:

- Subject cohort characterization and stratification
- Correlating behavioral measures with neuroimaging data
- Clinical patient assessment and diagnosis tracking
- Group comparison studies
- Statistical analysis of behavioral outcomes
- Multi-modal dataset integration

Module API
----------

.. automodule:: abidskit.common.specs_phenotype
   :show-inheritance: True

Related Documentation
---------------------

- :doc:`common.specs_dataset` - Dataset class containing phenotypic data
- :doc:`common.specs_misc` - Data column and type definitions
- :doc:`../io` - Loading and saving datasets with phenotypic information
