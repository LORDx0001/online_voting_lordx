# Online Voting System (online_voting_lordx)

A simple and secure online voting system built with Django.

## Table of Contents

- [Online Voting System (online_voting_lordx)](#online-voting-system-online_voting_lordx)
    - [Table of Contents](#table-of-contents)
    - [Features](#features)
    - [Technologies Used](#technologies-used)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Contributing](#contributing)

## Features

- User registration and authentication
- Participate in voting processes
- View voting results
- Admin dashboard for managing users, votes, and results

## Technologies Used

- Python 3.x
- Django
- Django Rest Framework
- SQLite (default, can be changed)
- Bootstrap (for frontend, if used)

## Installation

1. Clone the repository:

     ```bash
     git clone https://github.com/yourusername/online_voting_lordx.git
     cd online_voting_lordx
     ```

2. Create and activate a virtual environment:

     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install dependencies:

     ```bash
     pip install -r requirements.txt
     ```

4. Run migrations:

     ```bash
     python manage.py migrate
     ```

5. Create a superuser:

     ```bash
     python manage.py createsuperuser
     ```

6. Start the development server:

     ```bash
     python manage.py runserver
     ```

## Usage

- Open your browser and go to [http://localhost:8000/](http://localhost:8000/)
- Access the admin panel at [http://localhost:8000/admin/](http://localhost:8000/admin/)

## Contributing

Contributions, pull requests, and issues are welcome!
