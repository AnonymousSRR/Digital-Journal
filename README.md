# Digital Journal App

A modern, AI-powered digital journaling application built with Django that helps users reflect on their thoughts and experiences through guided prompts.

## Features

- 🔐 **User Authentication** - Secure signup and login system
- 🎨 **Theme Selection** - Choose from various journaling themes
- 🤖 **AI-Powered Prompts** - Dynamic prompts generated using Cohere AI
- 📝 **Journal Entries** - Create and save personalized journal entries
- 🔍 **Search Functionality** - Search through your journal entries
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile
- 🎯 **Expandable Cards** - Click to expand and read full journal entries

## Tech Stack

- **Backend**: Django 5.2.4
- **Database**: MySQL
- **AI Integration**: Cohere API
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Django's built-in auth system

## Installation

### Prerequisites

- Python 3.8 or higher
- MySQL database
- Cohere API key

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd joural-app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DATABASE_URL=mysql://username:password@localhost/database_name
   COHERE_API_KEY=your-cohere-api-key-here
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   Open your browser and go to `http://127.0.0.1:8000`

## Project Structure

```
joural-app/
├── authentication/          # User authentication app
│   ├── models.py           # User, Theme, and JournalEntry models
│   ├── views.py            # Authentication and journal views
│   ├── urls.py             # Authentication URL patterns
│   └── forms.py            # Custom user forms
├── config/                 # Main project configuration
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL configuration
│   └── wsgi.py             # WSGI configuration
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── home.html           # Home dashboard
│   ├── theme_selector.html # Theme selection page
│   ├── answer_prompt.html  # Journal entry creation
│   └── my_journals.html    # Journal entries listing
├── static/                 # Static files
│   └── css/
│       └── style.css       # Main stylesheet
├── requirements.txt        # Python dependencies
└── manage.py              # Django management script
```

## URL Structure

- `/` - Redirects to home or login
- `/home/` - Main dashboard
- `/home/theme-selector/` - Select journal theme
- `/home/answer-prompt/` - Create journal entry
- `/home/my-journals/` - View all journal entries
- `/login/` - Authentication page
- `/admin/` - Django admin interface

## API Integration

The app integrates with Cohere AI to generate dynamic journal prompts based on selected themes. Make sure to:

1. Sign up for a Cohere account at https://cohere.ai
2. Get your API key from the dashboard
3. Add the API key to your environment variables

## Database Models

### User Model
- Custom user model with email authentication
- First name, last name, and email fields

### Theme Model
- Name and description fields
- Used to categorize journal entries

### JournalEntry Model
- User relationship
- Theme relationship
- Title, prompt, and answer fields
- Timestamps for creation and updates

## Features in Detail

### 1. User Authentication
- Email-based registration and login
- Secure password handling
- Session management

### 2. Theme Selection
- Browse available journaling themes
- Visual theme cards with descriptions
- One-click theme selection

### 3. AI-Powered Prompts
- Dynamic prompt generation using Cohere AI
- Context-aware prompts based on selected theme
- Fallback prompts if API is unavailable

### 4. Journal Entry Creation
- Title and answer input fields
- Real-time form validation
- Automatic saving to database

### 5. Journal Management
- Grid layout of journal entries
- Search functionality with auto-submit
- Expandable cards for full content viewing
- Chronological ordering (newest first)

### 6. Responsive Design
- Mobile-first approach
- Clean, modern UI
- Smooth animations and transitions

## Development

### Running Tests
```bash
python manage.py test
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

### Creating Migrations
```bash
python manage.py makemigrations
```

### Database Migrations
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Create migration with custom name
python manage.py makemigrations --name descriptive_name
```

**Important Notes about Migrations:**
- ✅ **Migration files are tracked in version control by default**
- ✅ **This ensures all team members have the same database schema**
- ✅ **For production deployment, migrations are essential**
- ⚠️ **If you need to ignore migrations (not recommended), uncomment `# migrations/` in `.gitignore`**

### Migration Best Practices
1. **Always commit migrations** - They represent your database schema changes
2. **Test migrations** - Run `python manage.py migrate` after pulling changes
3. **Don't edit existing migrations** - Create new ones instead
4. **Use meaningful names** - `python manage.py makemigrations --name descriptive_name`
5. **Review migrations** - Check generated SQL with `python manage.py sqlmigrate app_name migration_number`

## Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use `python-decouple` for secure configuration
2. **Production Server**: Use `gunicorn` instead of Django's development server
3. **Database**: Consider PostgreSQL for better performance
4. **Static Files**: Use a CDN or cloud storage (AWS S3)
5. **Caching**: Implement Redis for better performance
6. **Security**: Enable HTTPS and configure CORS properly

Uncomment the relevant packages in `requirements.txt` for production use.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on the GitHub repository.
