# Journal Writing Timer Feature

## Overview
This feature tracks how much time users spend writing journal entries, from the moment they click "Create New Journal" until they successfully save their entry.

## How It Works

### 1. Timer Start
- When a user clicks the "Create New Journal" button on the home page, a timer starts
- The start time is stored in the browser's sessionStorage
- This ensures the timer persists even if the user navigates away and comes back

### 2. Timer Display
- On the answer prompt page, a real-time timer is displayed in the header
- Shows elapsed time in MM:SS format (e.g., "02:45")
- Updates every second while the user is writing

### 3. Timer End
- When the user successfully submits the journal entry (with valid title and answer), the timer stops
- The total writing time is calculated and saved to the database
- The timer data is cleared from sessionStorage

### 4. Time Display
- Writing time is displayed in the "My Journals" page for each entry
- Shows time in a human-readable format:
  - Less than 60 seconds: "45s"
  - 1-59 minutes: "5m"
  - 1+ hours: "1.5h"
- Also displayed in the journal entry modal

## Technical Implementation

### Database Changes
- Added `writing_time` field to the `JournalEntry` model
- Field stores time in seconds as an integer
- Default value is 0 for existing entries

### Frontend Changes
- **Home page**: JavaScript to start timer on "Create New Journal" click
- **Answer prompt page**: Real-time timer display and form submission handling
- **My Journals page**: Display writing time for each entry
- **CSS styling**: Styled timer display and writing time badges

### Backend Changes
- Updated `answer_prompt_view` to capture and save writing time
- Added custom template filter for time formatting
- Migration created for the new database field

## Files Modified

### Models
- `authentication/models.py` - Added `writing_time` field

### Views
- `authentication/views.py` - Updated to handle writing time

### Templates
- `templates/home.html` - Added timer start functionality
- `templates/answer_prompt.html` - Added timer display and form handling
- `templates/my_journals.html` - Added writing time display

### Static Files
- `static/css/style.css` - Added timer and writing time styles

### Custom Template Filters
- `authentication/templatetags/time_filters.py` - Time formatting filter

## Usage Flow

1. **User logs in** to the application
2. **Clicks "Create New Journal"** - Timer starts automatically
3. **Selects a theme** - Timer continues running
4. **Writes journal entry** - Real-time timer display shows elapsed time
5. **Saves entry** - Timer stops and writing time is recorded
6. **Views in My Journals** - Can see writing time for each entry

## Features

### ✅ Implemented
- Automatic timer start on journal creation
- Real-time timer display during writing
- Timer persistence across page navigation
- Writing time storage in database
- Human-readable time display
- Timer display in journal cards and modal
- Responsive design for mobile devices

### 🔄 Timer Persistence
- Uses sessionStorage to maintain timer state
- Timer continues if user navigates away and returns
- Timer resets only when journal is successfully saved

### 📱 Mobile Support
- Timer display is responsive
- Touch-friendly interface
- Works on all device sizes

## Testing

Run the timer functionality test:
```bash
python test_timer_functionality.py
```

This tests the basic timer logic and time formatting functions.

## Future Enhancements

Potential improvements for the timer feature:

1. **Writing Analytics**: Track average writing time per theme
2. **Progress Indicators**: Show writing progress based on time
3. **Writing Goals**: Set time-based writing goals
4. **Export Data**: Export writing time statistics
5. **Timer Pause**: Allow users to pause/resume timer
6. **Writing Streaks**: Track daily writing consistency

## Browser Compatibility

The timer feature uses:
- `sessionStorage` for data persistence
- `Date.now()` for timestamp generation
- `setInterval` for timer updates

These are supported in all modern browsers (Chrome, Firefox, Safari, Edge). 