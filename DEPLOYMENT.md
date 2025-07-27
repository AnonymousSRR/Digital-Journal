# Deployment Guide for Journal App

This guide provides instructions for deploying the Journal App to Render.

## Prerequisites

- A Render account
- A PostgreSQL database (can be created through Render)

## Environment Variables

Set the following environment variables in your Render service:

### Required Variables

1. **DATABASE_URL**: PostgreSQL connection string (automatically provided by Render if you create a PostgreSQL service)
2. **SECRET_KEY**: Django secret key for production
3. **DEBUG**: Set to 'False' for production
4. **ALLOWED_HOSTS**: Your Render domain (e.g., 'your-app-name.onrender.com')

### Example Environment Variables

```
DATABASE_URL=postgres://username:password@host:port/database
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
```

## Render Configuration

### Build Command
```bash
./build.sh
```

### Start Command
```bash
./start.sh
```

### Python Version
The app uses Python 3.11.9 (specified in `runtime.txt`)

## Database Setup

1. Create a PostgreSQL database in Render
2. The `DATABASE_URL` environment variable will be automatically set
3. Database migrations will run automatically during the build process

## Static Files

Static files are automatically collected and served using WhiteNoise during the build process.

## Troubleshooting

### Common Issues

1. **psycopg2 Error**: Make sure `psycopg2-binary` is in requirements.txt
2. **Database Connection**: Verify `DATABASE_URL` is set correctly
3. **Static Files**: Ensure WhiteNoise is configured in settings.py
4. **Migrations**: Check that all migrations are applied

### Debugging

- Check Render logs for detailed error messages
- Verify environment variables are set correctly
- Ensure all dependencies are listed in requirements.txt

## Local Development

For local development, the app will use SQLite by default. To use PostgreSQL locally:

1. Install PostgreSQL
2. Set `DATABASE_URL` environment variable
3. Run migrations: `python manage.py migrate`

## Security Notes

- Never commit sensitive information like SECRET_KEY to version control
- Use environment variables for all sensitive configuration
- Enable HTTPS in production (handled automatically by Render) 