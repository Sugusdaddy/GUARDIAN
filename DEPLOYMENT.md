# 🚀 GUARDIAN Deployment Guide

## GitHub Pages Website

The GUARDIAN website is automatically deployed to GitHub Pages at:

**🌐 https://sugusdaddy.github.io/GUARDIAN/**

### Automatic Deployment

Every push to `main` or `copilot/improve-overall-professionalism` branches triggers automatic deployment via GitHub Actions.

### Manual Deployment

To manually trigger deployment:

1. Go to GitHub Actions
2. Select "Deploy to GitHub Pages" workflow
3. Click "Run workflow"

### What Gets Deployed

The following files are deployed to GitHub Pages:
- `index.html` - Main landing page
- `docs/` - Documentation files
- All markdown documentation (README, FEATURES, etc.)
- Static assets and resources

### Configuration

GitHub Pages is configured via:
- `.github/workflows/deploy-pages.yml` - Deployment workflow
- `_config.yml` - Jekyll configuration
- `README.md` - Project information

### Troubleshooting

#### Website not updating?
1. Check GitHub Actions for deployment status
2. Wait 2-3 minutes for CDN cache to clear
3. Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)

#### 404 errors?
1. Verify `index.html` exists in root directory
2. Check GitHub Pages settings in repository settings
3. Ensure deployment workflow completed successfully

#### Links not working?
1. Use absolute URLs for external resources
2. Use relative URLs for internal pages
3. Test locally before pushing

### Local Testing

Before deploying, test the website locally:

```bash
# Option 1: Simple Python server
python -m http.server 8000

# Option 2: Using the API server
python app/api/main.py

# Then open http://localhost:8000
```

### Features on GitHub Pages

✅ **Working:**
- Landing page with all information
- Interactive UI elements
- Smooth animations and transitions
- Mobile responsive design
- All static content

⚠️ **Limited:**
- Real-time API calls (static hosting)
- Backend agent communication
- Database persistence

💡 **Tip:** For full functionality including API and agents, run the local server.

### Performance

GitHub Pages provides:
- Fast global CDN
- Free HTTPS
- Automatic optimization
- 99.9% uptime

### Support

- 📖 [GitHub Pages Documentation](https://docs.github.com/en/pages)
- 🐛 [Report Issues](https://github.com/Sugusdaddy/GUARDIAN/issues)
- 💬 [Discussions](https://github.com/Sugusdaddy/GUARDIAN/discussions)

---

**Last Updated:** 2024-02-04
