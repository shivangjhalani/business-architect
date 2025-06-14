# Business Capability Map Management System

An AI-powered application to manage, analyze, and evolve an organization's business capability map.

## Project Structure

```
business-cap/
├── backend/           # Django backend
│   └── venv/         # Python virtual environment
├── frontend/         # React frontend
└── pgdata/          # PostgreSQL data directory
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory and activate the virtual environment:
   ```bash
   cd backend
   python -n venv venv
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run Django migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

### Database Setup


1. Setup pg:
   ```bash
   mkdir pgdata pg_socket
   initdb -D pgdata --auth-local=trust --auth-host=scram-sha-256
   ```

2. Set local pg_socket:
   ```bash
   # Update postgresql.conf to use local socket directory
   sed -i "s|#unix_socket_directories = '/run/postgresql'|unix_socket_directories = '$PWD/pg_socket'|" pgdata/postgresql.conf
   ```

3. Start PostgreSQL server:
   ```bash
   pg_ctl -D pgdata -l pgdata/postgres.log start
   ```

4. Create the postgres role and database:
   ```bash
   export PGHOST=$PWD/pg_socket

   # Create the postgres superuser role with password
   createuser -s postgres
   
   # Set a password for the postgres user (connect to the default postgres database)
   psql -d postgres -c "ALTER USER postgres PASSWORD '<password>';"
   
   # Create your database
   createdb -U postgres business_cap
   ```

5. Update .env using .env.example:


6. Stop PostgreSQL server when done:
   ```bash
   pg_ctl -D pgdata stop
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

## Development

- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:5173
- API documentation available at http://localhost:8000/swagger
