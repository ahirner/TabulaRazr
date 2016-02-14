# TabulaRazr
Web App to extract and browse through tabular data using Flask.
(c) Alexander Hirner 2016, no redistribution without permission.

## Description

Municipalities suffer from ill financed public infrastructure (e.g. Flint water scandal). A large part of this problem is caused by lack of transparency in the municipal bond market. To solve that, we extract financial data buried in pdf documents, aggregate them in comparable and tabular form, and thus enable officials to bargain better terms. This type of analysis has merit in many other verticals too. The data (>1000 docs) and NLP talent is there, now we need UI/UX and Open Data enthusiasts!

## Technologies

We use cortical.io / retina SDK API to generate embedding.
We use IBM BlueMix to perform PDF to text conversion.

## Setup and run

    npm install -g bower
    pip install -r requirements.txt
    bower install
    python server.py

Navigate to [http://localhost:8000](http://localhost:8000) and upload an example document (see below).

## Folder structure
- [./templates](./templates) ... Jinja2 template
- [,/static](./static) ... all stylesheets and media goes there
- [./static/ug/<project_name>](./static/ug/) ... user uploaded data and analysis files (graphs, json)

## Examples

see [EXAMPLES.md](EXAMPLES.md)

