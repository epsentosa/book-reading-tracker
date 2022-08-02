# Web Application
This is my web development project focusing of use [Python Flask](http://flask.pocoo.org) as backend, [Bootstrap 5](https://getbootstrap.com) as simple frontend and [MySQL](https://www.mysql.com) for database.
Using [docker](https://www.docker.com) for easy deployment and auto switch between development server and production 'like' server using [gunicorn](https://gunicorn.org).

### Description
Main purpose of this web is to save user note of book into spesific page's book.
More than 10.000 book title already include into database so user can search it or add it if there is not found.


### Working Tree
```bash
book-reading-tracker
├── docker-compose.yml
├── Dockerfile
├── mysql-data
├── README.md
├── requirements.txt
└── src
    ├── app.py
    ├── books
    │   ├── forms.py
    │   ├── __init__.py
    │   ├── routes.py
    │   ├── static
    │   └── templates
    └── config.yml
```

### Steps to get working
Git clone this repo and and clone also mysql-data from github.com/ekoputrasentosa/mysql-data inside book-reading-tracker folder
* **Production 'like' server**
Only need docker-compose in host, and to run just simply do
  ```bash
  docker-compose up --build -d
  ```
