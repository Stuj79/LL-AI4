# Technical FAQs

### Installation & Setup

**Q: What are the system requirements for the Legal AI Marketing Assistant?**
A: The application requires Python 3.8 or higher, with at least 4GB of RAM recommended. It runs on Windows, macOS, and Linux environments with proper Python installation.

**Q: How do I install the required dependencies?**
A: You can install all required dependencies using pip: `pip install -r requirements.txt` from the root directory of the application.

**Q: Can I run the application in a virtual environment?**
A: Yes, and it's recommended. Create a virtual environment using `python -m venv venv`, activate it, then install the dependencies.

### Data & Files

**Q: What file formats are supported for importing data?**
A: The application supports CSV and Excel (.xlsx) files for content inventory uploads. JSON files can also be imported for certain operations.

**Q: Where does the application store my data?**
A: Data is stored in the `outputs/` directory. This includes CSV, JSON, and Markdown reports generated during your analysis.

**Q: Is there a way to back up my data?**
A: Yes, you can manually back up the `outputs/` directory to preserve your data. We recommend doing this regularly, especially after completing significant analysis work.

### API & Integration

**Q: Does the application use any external APIs?**
A: Yes, the application uses the OpenAI API for content analysis and classification. You'll need to provide your API key in the `.env` file.

**Q: How do I set up my API keys?**
A: Copy the `.env.example` file to `.env` and fill in your API key information. The application will read this file to authenticate with external services.

**Q: How can I monitor API usage?**
A: The application logs API calls and token usage. Check the console output or logs for details on API usage. You can also monitor usage through your OpenAI dashboard.

### Performance & Troubleshooting

**Q: Why is content analysis taking a long time?**
A: Content analysis depends on external API response times. Large content sets may take longer to process. Consider breaking your analysis into smaller batches.

**Q: How do I resolve "Memory Error" messages?**
A: This usually indicates your system is running out of RAM. Try closing other applications, processing smaller batches of content, or upgrading your system's memory.

**Q: What should I do if I encounter API rate limits?**
A: The application implements retry logic, but persistent rate limiting might require you to wait before continuing. Consider upgrading your API tier if you need higher throughput.
