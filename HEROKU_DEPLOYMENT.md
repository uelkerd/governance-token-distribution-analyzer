# Deploying to Heroku

This document provides instructions for deploying the Governance Token Distribution Analyzer to Heroku.

## Prerequisites

1. A [Heroku account](https://signup.heroku.com/)
2. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed
3. Git installed
4. Etherscan API key
5. Infura Project ID

## Deployment Steps

### 1. Login to Heroku CLI

```bash
heroku login
```

### 2. Create a Heroku App

```bash
# Create a new Heroku app
heroku create your-app-name

# Or connect to an existing app
heroku git:remote -a your-app-name
```

### 3. Configure Environment Variables

Set the required environment variables for the application:

```bash
heroku config:set ETHERSCAN_API_KEY=your_etherscan_api_key
heroku config:set INFURA_PROJECT_ID=your_infura_project_id
```

### 4. Deploy the Application

Push the code to Heroku:

```bash
git push heroku main
```

### 5. Ensure at least one instance is running

```bash
heroku ps:scale web=1
```

### 6. Open the Application

```bash
heroku open
```

## Monitoring and Maintenance

### View Application Logs

```bash
heroku logs --tail
```

### Restart the Application

```bash
heroku restart
```

### Update Configuration

```bash
heroku config:set NEW_VARIABLE=new_value
```

## Troubleshooting

### Application Crashes or Fails to Start

1. Check the logs: `heroku logs --tail`
2. Ensure all required environment variables are set
3. Verify that the Procfile is correctly set up with: `web: streamlit run src/dashboard/app.py`
4. Make sure the Python version in runtime.txt is supported by Heroku

### API Rate Limiting

If you encounter rate limiting issues with the Etherscan or Infura APIs:
1. Consider upgrading to paid API plans
2. Implement caching for API responses
3. Add retry logic with exponential backoff

## Scaling the Application

To handle more traffic, you can scale the web dynos:

```bash
heroku ps:scale web=2
```

For more information about Heroku deployment, refer to the [official Heroku documentation](https://devcenter.heroku.com/articles/getting-started-with-python). 