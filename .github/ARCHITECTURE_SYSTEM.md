# Local Architecture Summary System

This system now stores architecture summaries locally in the repository alongside Firebase backup.

## Files Created

### `.github/architecture-summary.json`
Main architecture summary file containing:
- `repository`: Repository name
- `summary`: AI-generated architecture description
- `last_updated`: ISO timestamp
- `source`: "local"

### `.github/architecture-changes.json`
Recent architecture changes tracking:
- Array of recent PR changes (last 10)
- Each entry contains PR number, timestamp, diff size, metadata

## How It Works

### 1. Architecture Tracking (`track_architecture.py`)
- Writes changes to **both** local files AND Firebase
- Uses local logic for deciding when to regenerate summary
- Falls back gracefully if Firebase fails

### 2. Architecture Summarization (`summarize_architecture.py`)
- Reads existing summary from local files first, Firebase fallback
- Generates new summary with Claude
- Writes to **both** local files AND Firebase
- Prioritizes local storage success

### 3. AI Review (`ai_review.py`)
- Reads architecture context from local files **first**
- Falls back to Firebase if local files unavailable
- Provides better error messages showing source

### 4. Workflow Integration
- Automatically commits architecture files after updates
- Uses `[skip ci]` to avoid triggering recursive builds
- Pushes directly to PR branch for immediate availability

## Benefits

✅ **Faster**: No Firebase queries during review (local files)  
✅ **Reliable**: Works even if Firebase is down  
✅ **Transparent**: Architecture visible in repository  
✅ **Versioned**: Architecture changes tracked in git  
✅ **Fallback**: Firebase still works as backup  

## File Locations

- **Summary**: `.github/architecture-summary.json`
- **Changes**: `.github/architecture-changes.json` 
- **Manager**: `.github/workflows/scripts/local_architecture.py`

These files are automatically managed by the CI system and should not be manually edited.

