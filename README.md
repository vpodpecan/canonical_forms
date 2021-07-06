## Canonizer web service


### About

This repository contains the code for finding canonical forms in Slovene language. It was developed as a part of the [RSDO project](https://www.cjvt.si/rsdo/en/project/).

The code can be used as a REST web service which accepts POST requests at `/rest_api/canonize` with JSON payload such as:

```json
{
  "forms": [
    "histološko zgradbo",
    "histoloških tkivnih rezin",
    "žlezne celice"
  ]
}
```

which returns a response like this:
```json
{
  "canonical_forms": [
    "histološka zgradba",
    "histološka tkivna rezina",
    "žlezna celica"
  ]
}
```

It is also possible to use the code as a standalone program which processes CSV files. The program can determine the delimiter automatically but the index of the relevant column must be specified. For example, the following command will process the third column of the CSV file `test.csv` (columns are zero-indexed):

```bash
python services/web/canonizer.py test.csv 2
```

### Requirements

-  docker
-  docker-compose

If you want to use the code as a standalone program outside of Docker the following python packages are required:

- flask-restx==0.4.0
- gunicorn==20.1.0
- classla==1.0.1
- lemmagen3==3.3.1
- flask-socketio==5.1.0
- simple-websocket==0.2.0


### How to use

#### Development

The following command

```sh
$ docker-compose up --build
```

will build the images and run the container. If you go to [http://localhost:5000](http://localhost:5000) you will see a web interface where you can check and test the REST API.

#### Production

The following command

```sh
$ docker-compose -f docker-compose.prod.yml up -d --build
```

will build the images and run the service and proxy containers. The web interface is now available at [http://localhost](http://localhost) (port 80). This setup can be used in production.


## Authors

The code for finding canonical forms was written by Andraž Repar. [Vid Podpečan](vid.podpecan@ijs.si) adapted the code, wrote the web service interface and Docker config files.
