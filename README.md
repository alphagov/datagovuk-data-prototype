# Datagovuk data prototype

This repository will be used to collect a list of curated datasets and explore some lightweight ways to manage inital content and metatdata. Metadata in this context could be web page and API urls, tags or other things.

We'll use markdown and a common pattern of front matter for page metadata and markdown body as content.

In addition this repository is intended as an initial store of just enough data (csv or json) to create useful visualisations for dataset pages. 

Depending on what we find out as we go, we may add some scripts to explore ways of managing visualisation data or other aspects of the exploratory work. 

**Note**: Nothing here should be considered production like, but outputs/learnings will inform work intended for production.

## Repository structure

The [content](content) directory contains markdown files used to generate static pages for datasets.

There will be a markdown file per subject area such as company information or air quality.

The [data](data) directory is used for data used in visualisations.


## Using this repository

If you want to add a page for a dataset/topic e.g. Weather forecasts then:

1. Add a markdown file called weather-forecast.md to the [content](content) directory
1. Add some front matter
1. Add some content

For frontmatter use existing files for examples of what were doing at the moment. You don't need to fill in all key value pairs, but title and collection name is enough to get started with. 

We can fill out the rest as we go. It's more useful to have a placeholder than nothing at all.

To add a visualisation data just add a csv or json file to the [data](data) directory. Nothing large in terms of file size. Visualisations will most likely be small. If in doubt, just ask.

The choice of csv or json for now is whatever is easier to find or produce, as the first slice will probably be
hand made. Although we'll look to automate what we can.


### Scripts in this repository

Some scripts have been created to help experiment with some of the data that may be using in visualisations. To use the scripts there are some prerequisites.

First install [UV](https://docs.astral.sh/uv/) - install instructions [here](https://docs.astral.sh/uv/getting-started/installation/)

Then run: 
```
uv sync
 ```

This will create a virtualenv.

Activate the virtualenv

```
source .venv/bin/activate
```

Then run the following for help text

 ```
 python -m scripts.cli
 ```