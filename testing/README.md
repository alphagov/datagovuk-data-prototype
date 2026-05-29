
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/collection-check-2026-05-29T0737.csv](results/collection-check-2026-05-29T0737.csv)



## Deprivation
Page: [https://data.gov.uk/collections/people/deprivation](https://data.gov.uk/collections/people/deprivation)


            

The following links were not reachable during test

- [https://www.gov.wales/welsh-index-multiple-deprivation-2025-series](https://www.gov.wales/welsh-index-multiple-deprivation-2025-series)



