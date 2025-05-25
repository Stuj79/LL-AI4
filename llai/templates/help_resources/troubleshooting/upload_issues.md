# Troubleshooting Upload Issues

### Common Content Inventory Upload Problems

**Issue: File format not recognized**
- **Solution**: Ensure your file is in CSV (.csv) or Excel (.xlsx) format
- **Details**: Check that the file extension matches the actual format. Sometimes files are named incorrectly.
- **Fix**: Save your file again from your spreadsheet application with the correct format.

**Issue: Column headers not recognized**
- **Solution**: Check that your file contains the expected column headers
- **Details**: The system expects headers such as "Title", "URL", "Content Type", "Practice Area", etc.
- **Fix**: Review the template in the application and adjust your headers to match.

**Issue: Upload hangs or times out**
- **Solution**: Try reducing file size or splitting into smaller files
- **Details**: Files over 10MB or containing thousands of rows may cause performance issues.
- **Fix**: Break your inventory into logical segments (by practice area, content type, etc.).

**Issue: Special characters causing parsing errors**
- **Solution**: Check for and remove special characters in your file
- **Details**: Non-standard characters, especially in CSV files, can disrupt parsing.
- **Fix**: Open the file in a text editor and look for unusual characters, or re-save from Excel with proper encoding.

**Issue: Data not appearing after successful upload**
- **Solution**: Refresh the application or check the filtering options
- **Details**: Sometimes the data loads but is filtered in a way that hides it from view.
- **Fix**: Click "Reset Filters" or reload the application while preserving your session state.

### Saving Issues

**Issue: Changes not saved**
- **Solution**: Ensure you clicked the "Save" button and waited for confirmation
- **Details**: The save process may take a few moments for large inventories.
- **Fix**: Look for the green success message before navigating away.

**Issue: Cannot locate saved files**
- **Solution**: Check the outputs/ directory in your application folder
- **Details**: Files are saved with timestamps in the filename format.
- **Fix**: Sort by date modified to find your most recent files.

**Issue: Permission error when saving**
- **Solution**: Check file system permissions
- **Details**: The application needs write permissions to the outputs/ directory.
- **Fix**: Ensure you have appropriate access rights to the directory.

### If Problems Persist

If you continue to experience issues with uploading or saving:
1. Try a different browser
2. Restart the application
3. Contact technical support with details of the issue and any error messages
