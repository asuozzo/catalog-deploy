This Flask app is a way to keep track of the books in your home library.

It's running on Amazon Lightsail at http://18.221.156.230/. Access is on port 2200.

To add new books, create an account by logging in through Facebook. Users can edit and delete their own items, but not ones created by other users.

### Technical details

This is an edited version of this catalog app running sqlite: https://github.com/asuozzo/catalog

This version runs on a Ubuntu server and uses a Postgres database running locally. The main differences between this and the first version of the catalog app are the postgres engine structure and some file path differences required for the Facebook login credentials.

This version uses the following packages:

* flask
* psycopg2
* httplib2
* sqlalchemy