# ShareMeal Project

## Project Structure

This project has been restructured for better maintainability.

- **`backend/`**: Contains the core server logical code.
  - `app.py`: The main Flask application entry point. Serves API and Static files.
  - `server.js`: (Legacy) Node.js server alternative.
- **`frontend/`**: Contains all HTML, CSS, and Client-side JavaScript.
  - `user/`, `donor/`, `ngo/`, `delivery/`, `admin/`: Role-specific pages.
- **`database/`**: Contains Database configurations and the SQLite file.
  - `sharemeal.db`: The SQLite database file.
  - `db.py`: Database connection and initialization logic.
- **`scripts/`**: Contains maintenance and utility scripts.
  - `create_admin.py`: Create admin user.
  - `update_db*.py`: Update database schema scripts.
  - `cleanup_db.py`: Database cleanup utilities.
  - `check_donors.py`, `fix_role.py`: Debugging scripts.

## How to Run

### Prerequisite
- Python 3 Installed
- (Optional) `.venv` virtual environment configured.

### Quick Start
To start both the Frontend and Backend servers, simply run:

```bash
./start.sh
```

or manually:

```bash
python3 backend/app.py
```

The application will be available at: **http://localhost:3000**

## Database Scripts

All database maintenance scripts have been moved to the `scripts/` folder.
To run any of them, execute from the project root:

```bash
python3 scripts/create_admin.py
python3 scripts/check_donors.py
# etc.
```

These scripts have been updated to automatically locate the database file correctly.
