The aim of this project is to find arbitrage opportunities by searching for item listings and executing a multimodal query to the gemini vision pro LLM to extract historical sales data that the model was trained on.

# Goodwill Auction Analysis Tool

This application helps find undervalued items on Goodwill's auction site by:
1. Scraping Goodwill's auction site for product data
2. Using Gemini AI to analyze prices and estimate resale values
3. Calculating potential profit margins
4. Sending notifications for high-margin items
5. Providing a user-friendly interface to browse and save promising items

## Features

- **Grid View**: iPad-friendly grid layout for browsing items
- **List View**: Traditional list view for detailed analysis
- **Favorites & Promising**: Save items of interest for later review
- **Margin Analysis**: Automatically calculate profit margins
- **Buy-It-Now Identification**: Clearly identify Buy-It-Now vs Auction items
- **Direct Links**: Easily access original Goodwill listings
- **Notifications**: Email or SMS alerts for high-margin items
- **Customizable Settings**: Set location preferences, margin thresholds, and update frequency

## Quick Setup

The easiest way to set up the application is to use the provided setup script:

```
cd Goodwill-app
python setup.py
```

This script will:
1. Check your Python version
2. Install required Python dependencies
3. Create template .env files
4. Set up the SQLite database with the necessary tables
5. Configure the database path in all relevant files

After running the setup script, follow the on-screen instructions to complete the setup.

## Running the Application

After setting up the application, you can run it using the provided run script:

```
python run.py
```

This will start both the backend and frontend servers. You can also run specific components:

```
# Run only the backend server
python run.py --backend-only

# Run only the frontend server
python run.py --frontend-only

# Run with the scheduler for automatic updates
python run.py --scheduler
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## Manual Setup Instructions

If you prefer to set up the application manually, follow these steps:

### Backend Setup

1. Install Python dependencies:
   ```
   cd Goodwill-app
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the `backend` directory with the following variables:
   ```
   API_KEY=your_gemini_api_key
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASSWORD=your_email_password
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```

3. Update the database path in the following files to match your system:
   - `backend/app.py`
   - `backend/notifications.py`
   - `backend/scheduler.py`
   - `backend/gemini.py`
   - `backend/get_products.py`
   - `backend/remove_old.py`

4. Start the backend server:
   ```
   cd backend
   python app.py
   ```

### Frontend Setup

1. Install Node.js dependencies:
   ```
   cd frontend
   npm install
   ```

2. Create a `.env` file in the `frontend` directory:
   ```
   REACT_APP_SERVER_IP=localhost
   ```

3. Start the frontend development server:
   ```
   npm start
   ```

### Running the Scheduler

To enable automatic updates and notifications:

```
cd backend
python scheduler.py
```

The scheduler will run based on the frequency set in the Settings page (default: daily at 8:00 AM).

## Usage

1. Access the application at `http://localhost:3000`
2. Log in to the application
3. Use the Grid View to browse items
4. Save interesting items as Favorites or Promising
5. Configure your preferences in the Settings page

## Default Settings

- Default location: Spokane, WA (Seller ID: 198)
- Default margin threshold: 50%
- Default update frequency: Daily

## Technologies Used

- **Backend**: Flask, SQLite, Gemini AI
- **Frontend**: React, CSS Grid
- **Notifications**: Email (SMTP), SMS (Twilio)
- **Scheduling**: Python Schedule
