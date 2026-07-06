
# data.gov.uk collection page checks
                    
This test uses Playwright to check the [collection content files](https://github.com/alphagov/datagovuk_find/tree/main/app/content/collections) from the datagovuk_find repository.

It fetches those files, extracts the list of urls (webistes, api, dataset) referred to the markdown frontmatter.

The tests visit the rendered html version of each collection page on data.gov.uk and ensures that:

- the links listed in the frontmatter are rendered on the page
- that those links are reachable
                    
                    
## Report

Using test results file: [results/collection-check-2026-07-06T0753.csv](results/collection-check-2026-07-06T0753.csv)


No issues reported
