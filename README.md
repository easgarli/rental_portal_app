# Rental Portal

A comprehensive web application that connects tenants and landlords, featuring a mutual rating system and tenant scoring mechanism.

## Overview

Rental Portal is a sophisticated platform designed to bring transparency and trust to the rental market. It enables landlords and tenants to rate each other, track rental history, and make informed decisions based on comprehensive scoring systems.

### Key Features

- **User Authentication System**
  - Separate registration and login for tenants and landlords
  - Role-based access control
  - Secure session management

- **TenantScore System**
  - Composite scoring based on:
    - Payment history
    - Landlord ratings
    - Credit assessment
    - Property maintenance record
  - Score range: 0-100
  - Dynamic score updates

- **Mutual Rating System**
  - 5-star rating scale
  - Multiple rating dimensions:
    - For Tenants:
      - Payment reliability
      - Property care
      - Communication
      - Neighbor relations
      - Contract compliance
    - For Landlords:
      - Property condition accuracy
      - Contract transparency
      - Communication & support
      - Maintenance service
      - Privacy & respect

- **Property Management**
  - Property listing creation and management
  - Detailed property information
  - Availability tracking
  - Rental history recording

- **Contract Management System**
  - Digital contract generation
  - Contract signing workflow
  - Payment schedule tracking
  - Monthly rent payment recording
  - Contract status monitoring (draft, pending_signatures, active, completed, terminated)

## Technical Stack

### Backend
- **Framework**: Flask
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login
- **Form Handling**: Flask-WTF
- **API**: RESTful endpoints

### Frontend
- **Framework**: Bootstrap 5
- **JavaScript**: Vanilla JS
- **UI Components**: 
  - Progress bars
  - Rating displays
  - Interactive forms
  - Responsive design

### Security Features
- CSRF protection
- Input validation
- Secure password handling
- Rate limiting
- Session management

### Database Schema
- Users (tenants, landlords, admins)
- Properties
- Ratings
- TenantScores
- RentalApplications
- Contracts
- Payments
- UserContractInfo

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/easgarli/rental-portal.git
    cd rental-portal
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up PostgreSQL database and configure environment variables:
    ```bash
    # Create a .env file in the root directory
    touch .env
    ```
Update .env with your database credentials
    POSTGRES_USER=your_user
    POSTGRES_PASSWORD=your_password
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=rental_portal   
    ```

5. Initialize the database:
    ```bash
    flask db init
    flask db migrate
    flask db upgrade
    ```

6. Run the development server:
    ```bash
    flask run
    ``` 

7. Access the application at `http://localhost:5000`

## Usage

## Project Structure

flask-rental-portal/
├── app.py # Application entry point
├── models/ # Database models
├── routes/ # Route handlers
├── static/ # Static files (CSS, JS)
├── templates/ # HTML templates
├── utils/ # Utility functions
├── migrations/ # Database migrations
└── tests/ # Test suite

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout

### Ratings
- `POST /rate-tenant` - Submit tenant rating
- `POST /rate-landlord` - Submit landlord rating
- `GET /ratings/<user_id>` - Get user ratings

### Tenant Score
- `GET /tenant-score/<tenant_id>` - Get tenant score
- `POST /tenant-score/update` - Update tenant score

### Properties
- `GET /api/properties` - List properties
- `POST /api/properties` - Create property
- `PUT /api/properties/<id>` - Update property
- `DELETE /api/properties/<id>` - Delete property

### Contracts
- `GET /api/contracts` - List user's contracts
- `GET /api/contracts/<contract_id>` - Get contract details
- `POST /api/payments` - Record rent payment

## Development

### Running Tests

pytest

### Database Migrations
```bash
flask db migrate -m "Migration message"
flask db upgrade
```

## Deployment

### Prerequisites
- Ubuntu 24.04.1 LTS
- Python 3.8+
- PostgreSQL 12+
- Nginx
- Gunicorn

### Deployment Steps
1. Set up Ubuntu server
2. Install dependencies
3. Configure Nginx
4. Set up Gunicorn
5. Configure SSL
6. Set up environment variables
7. Run database migrations
8. Start application

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Gunicorn Configuration
```bash
gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- Elnur Asgarli - Initial work

## Acknowledgments

- Flask documentation
- SQLAlchemy documentation
- Bootstrap documentation

## Database Models

### Contract Model
- UUID-based identification
- Tenant and Property relationships
- Start and end dates
- Monthly rent amount
- Contract status tracking
- Payment history relationship

### Payment Model
- UUID-based identification
- Contract relationship
- Payment date tracking
- Amount recording
- Payment notes
- Timestamp tracking



