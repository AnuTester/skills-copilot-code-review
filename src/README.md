# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View announcements for the school community

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                                          | Description                                                         |
| ------ | --------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu&teacher_username=USER` | Sign up for an activity (teacher required)                          |
| POST   | `/activities/{activity_name}/unregister?email=student@mergington.edu&teacher_username=USER` | Unregister from an activity (teacher required)                      |
| POST   | `/auth/login?username=USER&password=PASS`                                          | Teacher login                                                       |
| GET    | `/auth/check-session?username=USER`                                                | Validate teacher session                                            |
| GET    | `/announcements`                                                                   | Get active announcements                                            |
| GET    | `/announcements/manage?teacher_username=USER`                                      | List all announcements (teacher required)                           |
| POST   | `/announcements?teacher_username=USER`                                             | Create announcement (teacher required)                              |
| PUT    | `/announcements/{announcement_id}?teacher_username=USER`                           | Update announcement (teacher required)                              |
| DELETE | `/announcements/{announcement_id}?teacher_username=USER`                           | Delete announcement (teacher required)                              |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in MongoDB. Sample content is created in `database.py` when the database is empty.
