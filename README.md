# django_query_demo

A sample django project I created demonstrating Django queries for an interview

This Django project is deployed and running live at: http://transvec.com/django_query_sample

More notes and details can be found on the live demo page.

Features:
- A management command script that loads the  database tables from the .csv files provided for the exercise using bulk insert. It
  also handles duplicate/existing record checks and managing dependencies on record creation

- The queries live in the views.py file of the 'assignment' app and use Django's ORM to fetch results for most of the report items.

- The views are exposed as an api using Django Rest Framework. JavaScript is used to fetch the data from these REST endpoints via AJAX
  requests when the page loads and update the DOM with the results.

The source files of particular interest are:

    assignment/views.py (contains the Python/Django ORM queries as Django Rest Framework API views)
    assignment/models.py (contains the Django models that define the database schema)
    assignment/management/commands/import_csv_data.py (a custom management command that populates the app tables from the provided CSV files)
    assignment/static/assignment/assets/js/report.py (the JavaScript that fetches the report data and renders it to the DOM)

