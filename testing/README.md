
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/collection-check-2026-08-24T0624.csv](results/collection-check-2026-08-24T0624.csv)



## Storm overflows
Page: [https://data.gov.uk/collections/environment/storm-overflows](https://data.gov.uk/collections/environment/storm-overflows)


            

The following links were not reachable during test

- [https://environment.data.gov.uk/dataset/21e15f12-0df8-4bfc-b763-45226c16a8ac](https://environment.data.gov.uk/dataset/21e15f12-0df8-4bfc-b763-45226c16a8ac)



