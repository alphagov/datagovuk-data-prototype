# Notes

This is a collection of notes about visualisation data for dataset pages.

***

## Get company information

No obvious candidate data specifically from the links we're thinking of putting on the page, namely user facing web service and API.

It's possible to create a graph of quarterly formation/dissolution graph from other companies house data we could link to if required. 

**However if we don't list the source on page it could be confusing for the user?**

### Possible visualisation

Sample data here: [data/quaterly-company-formation.json](data/quaterly-company-formation.json)

With caveat noted above a quarterly statitical resport such as [Incorporated companies in the UK July to September 2025](https://assets.publishing.service.gov.uk/media/6900d17ba6048928d3fc2b20/Incorporated_companies_in_the_UK_July_to_September_2025.csv) could be used to create data for a chart

### How data for a graph was collected

A script was used to parse the file [Incorporated companies in the UK July to September 2025](https://assets.publishing.service.gov.uk/media/6900d17ba6048928d3fc2b20/Incorporated_companies_in_the_UK_July_to_September_2025.csv).

This CSV file was filtered for rows where the following are true:

    "Region" == "UK"
    "Corporate body type" == "All companies"
    "Attribute"  == "Incorporations" || "Dissolutions"

From resulting rows were sorted by date and the last four rows were taken. The script can be found here: [scripts/company_formation.py](scripts/company_formation.py)

***

## Births

Birth data for England and Wales is easily avaiable and most visualisations on ONS site have download links making charts easy to reproduce.

The ONS birth data is available on a couple of urls, but in this case I used this page:
[https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/bulletins/birthsummarytablesenglandandwales/2024refreshedpopulations](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/bulletins/birthsummarytablesenglandandwales/2024refreshedpopulations)

### Possible visualisation

Sample data: [data/total-live-birth-counts-england-and-wales-1939-to-2024.json](data/total-live-birth-counts-england-and-wales-1939-to-2024.json)

### How data for a graph was collected

A download of a table of live births in England and Wales was taken from the site above. This is a local copy: [data/reference/total-live-birth-counts-england-and wales-1939-to-2024.xlsx](data/reference/total-live-birth-counts-england-and wales-1939-to-2024.xlsx)

Note that the aggregated data is available on another ONS url as an Excel workbook here: [https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/birthsinenglandandwalesbirthregistrations](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/livebirths/datasets/birthsinenglandandwalesbirthregistrations) which may be a more stable url to use.

The csv was then just converted to json.

***

## Deaths

As with births, there are a number of options of data avaible as downloads from ONS. In this case the following url was used: [https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/bulletins/deathsregistrationsummarytables/2024](https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/bulletins/deathsregistrationsummarytables/2024)


### Possible visualisation

Sample data: [data/deaths-registered-in-england-and-wales-by-sex-1992-to-2024.json](data/deaths-registered-in-england-and-wales-by-sex-1992-to-2024.json)


### How data for a graph was collected

The csv data for the table "Deaths registered in England and Wales by sex, 1992 to 2024" on the page above was downloaded and converted to a json file.

***

## Food hygiene ratings

Good data is available for download here: [https://ratings.food.gov.uk/open-data](https://ratings.food.gov.uk/open-data)

### Possible visualisation

Sample data: [data/fhrs-ratings-by-region.json](data/fhrs-ratings-by-region.json)

There was a suggestion to create a graph or table of ratings by region which could be done by reworking FSAs downloadable data with a manually created mapping of local authorities
to regions. See below.

### How data for a graph was collected

The FHRS all region rating csv here: [https://safhrsprodstorage.blob.core.windows.net/opendatafileblobstorage/FHRS_All_en-GB.csv](https://safhrsprodstorage.blob.core.windows.net/opendatafileblobstorage/FHRS_All_en-GB.csv) was used as a starting point. This file lists rated establishments by local authority.

In order to create a list of ratings by region, given the above file does not record region, we had to create a mapping of local authorties to regions matching FSA names [data/reference/fhrs-local-authority-by-region.csv](data/reference/fhrs-local-authority-by-region.csv).

Clearly a govt mandated list of organisations (with identifiers) would be a good thing.

A sample script to collate the data is here: [scripts/aggregate_fhrs_ratings_by_region.py](scripts/aggregate_fhrs_ratings_by_region.py). It's nothing complicated but worth noting some work
needed.

***

## Health dashboard

The [UKHSA dashboard](https://ukhsa-dashboard.data.gov.uk/) has numerous visualsations all of which are easy to recreate as downloads for each chart available.

### Possible visualisation

Pick something of general interest from site above? We might want to check which (if any) are stable and evergreen, e.g. does the flu cases chart get taken down when flu season over?

***

## Planning data

There are a number of datasets available here: [https://www.planning.data.gov.uk/](https://www.planning.data.gov.uk/)

### Possible visualisation

Sample data: [data/conservation-area.geojson](data/conservation-area.geojson)

A random conservation area geojson file was downloaded. There's no reason it needs to be a conservation area and no reason it has to be that one. It's just an example of a map that could be used for a visualisation.

### How data was collected

Stable urls available for any given dataset on the platform, as csv, json or geojson where relevant.

***

## Price paid data

It's relatively straightforward to collect data on house prices for graphs/charts from the Land Registry.

**Note the data referred to here is the price paid data, not the house price index which is another dataset**

### Possible visualisation

Sample data: [data/summary-average-house-prices-2025-11.json](data/summary-average-house-prices-2025-11.json) 

Visualisations such as these [https://www.gov.uk/government/statistics/uk-house-price-index-for-november-2025/uk-house-price-index-summary-november-2025](https://www.gov.uk/government/statistics/uk-house-price-index-for-november-2025/uk-house-price-index-summary-november-2025) are possible.

What appear to be reliable index pages make access to the data straightforward.

### How data for a graph was collected

 1. Collected [https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Average-prices-2025-11.csv](https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/Average-prices-2025-11.csv)
 2. Extracted last records by region to produce [data/summary-average-house-prices-2025-11.json](data/summary-average-house-prices-2025-11.json) 
 
 This is just an example and a script to do it is here: [scripts/uk_house_prices.py](scripts/uk_house_prices.py). Many other options available.


***

## Upcoming election data

***

## Population data
