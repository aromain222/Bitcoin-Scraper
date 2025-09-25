# FinModAI Cloud Deployment Guide

This guide provides instructions for deploying FinModAI to various cloud platforms.

## 🚀 Quick Deploy Options

### Option 1: Railway (Recommended)
Railway offers the easiest deployment with automatic builds and free tier.

1. **Sign up at [Railway.app](https://railway.app)**
2. **Connect your GitHub repository**
3. **Deploy with one click:**
   ```bash
   # Push your code to GitHub first
   git add .
   git commit -m "Initial deployment setup"
   git push origin main
   ```
4. **Railway will automatically:**
   - Detect the Dockerfile
   - Build and deploy your app
   - Provide a public URL

### Option 2: Render
Free tier with automatic SSL and custom domains.

1. **Sign up at [Render.com](https://render.com)**
2. **Connect your GitHub repository**
3. **The `render.yaml` file will automatically configure the deployment**
4. **Your app will be live at `https://your-app-name.onrender.com`**

### Option 3: Heroku
Traditional platform with extensive add-ons.

1. **Install Heroku CLI**
2. **Deploy:**
   ```bash
   heroku create finmodai-your-name
   git push heroku main
   heroku open
   ```

## 📋 Pre-Deployment Checklist

### ✅ Files Created
- [x] `requirements.txt` - Python dependencies
- [x] `Dockerfile` - Container configuration
- [x] `Procfile` - Heroku process file
- [x] `railway.json` - Railway configuration
- [x] `render.yaml` - Render configuration
- [x] `.gitignore` - Git ignore rules

### ⚙️ Environment Variables (Optional)
Set these in your cloud platform's dashboard:

- `FLASK_ENV=production` - Enables production mode
- `OPENAI_API_KEY` - Your OpenAI API key (if using AI features)
- `PORT` - Port number (usually auto-set by platform)

## 🌐 Platform-Specific Instructions

### Railway Deployment
1. Go to [Railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your FinModAI repository
5. Railway will automatically build and deploy

### Render Deployment
1. Go to [Render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will use the `render.yaml` configuration
5. Your app will be live in ~5 minutes

### Heroku Deployment
```bash
# Install Heroku CLI first
npm install -g heroku

# Login and create app
heroku login
heroku create finmodai-banking-platform

# Deploy
git push heroku main

# Open your app
heroku open
```

## 🔧 Production Features

### Automatic Configuration
The app automatically detects cloud environments and:
- Disables ngrok tunneling
- Uses production-optimized settings
- Serves on the correct port
- Disables debug mode

### Performance Optimizations
- Gunicorn WSGI server for production
- 2 worker processes for handling requests
- 120-second timeout for long-running operations
- Proper static file serving

## 🎯 Post-Deployment

### Testing Your Deployment
1. **Visit your app URL**
2. **Test the main features:**
   - Dashboard loads correctly
   - Model generation works
   - Excel downloads function
   - Professional styling displays properly

### Custom Domain (Optional)
Most platforms offer custom domain support:
- **Railway**: Add custom domain in project settings
- **Render**: Configure custom domain in service settings
- **Heroku**: Use `heroku domains:add yourdomain.com`

## 🛠️ Troubleshooting

### Common Issues
1. **Build failures**: Check that all dependencies are in `requirements.txt`
2. **Port issues**: Ensure the app uses `$PORT` environment variable
3. **File permissions**: Make sure `generated_models/` and `uploads/` directories exist

### Logs
Check application logs:
- **Railway**: View logs in the Railway dashboard
- **Render**: Check logs in the Render dashboard
- **Heroku**: Use `heroku logs --tail`

## 💰 Cost Estimates
- **Railway**: Free tier with 500 hours/month
- **Render**: Free tier with limitations, $7/month for production
- **Heroku**: Free tier discontinued, starts at $7/month

## 🎉 Success!
Your FinModAI Investment Banking Platform is now live in the cloud!

Share your professional financial modeling platform with:
- Investment bankers
- Private equity professionals
- Corporate development teams
- Financial analysts

---

**Need help?** Check the platform-specific documentation or open an issue in the repository.

