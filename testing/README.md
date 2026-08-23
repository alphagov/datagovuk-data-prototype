
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/collection-check-2026-08-23T0616.csv](results/collection-check-2026-08-23T0616.csv)



## Childhood vaccinations
Page: [https://data.gov.uk/collections/early-years/childhood-vaccinations](https://data.gov.uk/collections/early-years/childhood-vaccinations)


            

The following links were not reachable during test

- [https://phw.nhs.wales/knowledge-article/cover-national-childhood-immunisation-uptake-data/](https://phw.nhs.wales/knowledge-article/cover-national-childhood-immunisation-uptake-data/)



## Main rivers
Page: [https://data.gov.uk/collections/environment/main-rivers](https://data.gov.uk/collections/environment/main-rivers)


            

The following links were not reachable during test

- [https://environment.data.gov.uk/dataset/25dde009-ba7d-40de-8380-c5c3bb32ccdc](https://environment.data.gov.uk/dataset/25dde009-ba7d-40de-8380-c5c3bb32ccdc)



