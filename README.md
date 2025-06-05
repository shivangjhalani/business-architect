# Business Capability Map Management System

An AI-powered application to manage, analyze, and evolve an organization's business capability map.

## Project Structure

```
business-cap/
├── backend/           # Django backend
│   └── venv/         # Python virtual environment
├── frontend/         # React frontend
├── pgdata/          # PostgreSQL data directory
└── PLAN.md          # Project plan and documentation
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory and activate the virtual environment:
   ```bash
   cd backend
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup

1. Initialize PostgreSQL:
   ```bash
   mkdir pgdata
   initdb -D pgdata -U pgdata/postgres --pwprompt
   ```

2. Start PostgreSQL server:
   ```bash
   pg_ctl -D pgdata -l pgdata/postgres.log start
   ```

3. Create database:
   ```bash
   createdb -U postgres <dbname>
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

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

[Add your license here] 