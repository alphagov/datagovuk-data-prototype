# Notes about datasets

This is a collection of notes, observations about the curated datasets.


=
## Get company information

Main public data API provides programatic access to much the same information (as data) as the web based end user search pages.

Other datasets available are the quarterly statitical resports such as [Incorporated companies in the UK July to September 2025](https://assets.publishing.service.gov.uk/media/6900d17ba6048928d3fc2b20/Incorporated_companies_in_the_UK_July_to_September_2025.csv) which was used to create
the initial data in [data/quaterly-company-formation.json](data/quaterly-company-formation.json) for a graph.

**Other sources**
 - [Companies house data products](https://www.gov.uk/guidance/companies-house-data-products) 


**How data for a graph was collected**

A script was used to parse the file [Incorporated companies in the UK July to September 2025](https://assets.publishing.service.gov.uk/media/6900d17ba6048928d3fc2b20/Incorporated_companies_in_the_UK_July_to_September_2025.csv). 

This CSV file was filtered for rows where the following are true:

    "Region" == "UK"
    "Corporate body type" == "All companies"
    "Attribute"  == "Incorporations"

From resulting rows were sorted by date and the last four rows were taken. The script can be found here: [scripts/company_formation.py](scripts/company_formation.py)

