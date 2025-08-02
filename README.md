# LinkedIn AI Agent Professionals Scraper

A comprehensive LinkedIn scraper designed to find AI automation professionals with 1k-10k followers for content partnership outreach.

## Features

- **Targeted Search**: Finds AI agent professionals, automation specialists, and workflow experts
- **Follower Filtering**: Targets profiles with 1k-10k followers (optimal engagement range)
- **Quality Scoring**: Calculates confidence and completeness scores for each profile
- **Deduplication**: Removes duplicate profiles automatically
- **CSV Export**: Saves results to structured CSV file
- **Anti-Detection**: Built-in rate limiting and browser automation measures
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd linkedin-ai-scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` file with your LinkedIn credentials:
   ```
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   ```

## Usage

### Basic Usage

Run the scraper:
```bash
python main.py
```

### Configuration

Edit `config.py` to customize:

- **Search Keywords**: Modify `SEARCH_KEYWORDS` list
- **Target Companies**: Update `TARGET_COMPANIES` list
- **Follower Range**: Adjust `MIN_FOLLOWERS` and `MAX_FOLLOWERS`
- **Rate Limiting**: Modify delays and limits
- **Quality Thresholds**: Adjust confidence and completeness scores

### Output Files

- `ai_agent_profiles.csv`: Main output with all found profiles
- `scraping_summary.txt`: Detailed statistics and summary report
- `linkedin_scraper.log`: Comprehensive logging information

## CSV Output Structure

| Column | Description |
|--------|-------------|
| name | Full name of the person |
| headline | Professional title/headline |
| location | Geographic location |
| profile_url | LinkedIn profile URL |
| company | Current company |
| follower_count | Number of followers |
| keyword_matched | Search keyword that found this profile |
| confidence_score | Quality confidence score (0-1) |
| profile_completeness | Profile completeness score (0-1) |
| scraped_date | Timestamp when profile was scraped |

## Search Strategy

The scraper uses multiple search approaches:

1. **Keyword-based searches**: AI agent, automation specialist, workflow automation, etc.
2. **Company-based searches**: Zapier, Make.com, n8n, Microsoft, Google, etc.
3. **Quality filtering**: Removes low-quality or incomplete profiles
4. **Deduplication**: Eliminates duplicate profiles based on URL

## Safety Features

- **Rate Limiting**: Respects LinkedIn's terms with delays between requests
- **Anti-Detection**: Random delays, user agent rotation, browser automation hiding
- **Error Handling**: Robust error handling and retry logic
- **Logging**: Comprehensive logging for debugging and compliance

## Troubleshooting

### Common Issues

1. **Login Failed**
   - Check your LinkedIn credentials in `.env` file
   - Ensure 2FA is disabled or use app-specific password
   - Try running in non-headless mode first

2. **No Profiles Found**
   - Check internet connection
   - Verify LinkedIn search is working manually
   - Adjust search keywords in `config.py`

3. **Rate Limiting**
   - Increase delays in `config.py`
   - Run scraper during off-peak hours
   - Use VPN if needed

### Debug Mode

Set `HEADLESS = False` in `config.py` to see the browser in action.

## Legal and Ethical Considerations

- **Respect LinkedIn's Terms**: This tool is for educational purposes
- **Rate Limiting**: Built-in delays to avoid overwhelming LinkedIn
- **Data Usage**: Only use collected data for legitimate business purposes
- **Privacy**: Respect the privacy of individuals whose data is collected

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes. Please use responsibly and in compliance with LinkedIn's terms of service.

## Support

For issues and questions:
1. Check the logs in `linkedin_scraper.log`
2. Review the troubleshooting section
3. Open an issue on GitHub

---

**Note**: This tool is designed for finding potential content partners in the AI automation space. Use the collected data responsibly and in accordance with applicable privacy laws and LinkedIn's terms of service. 