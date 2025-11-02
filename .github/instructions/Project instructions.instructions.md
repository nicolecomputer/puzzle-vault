---
applyTo: '**'
---

- Be sparse with comments, do not add a comment if a human would not have
- Never update readme files unless explicitly asked
- Always make sure the code passes type checking with `make typecheck`
- Always make sure the code is formatted with `make format`
- Always use the cache buster query parameter when linking to CSS files in HTML templates
- All commands should be run through make
- DO NOT automatically reset the database or delete data unless explicitly asked
- This project uses UV and python must be used through it


## Testing
- Only write tests if explicitly asked to. Offer to write tests but do not write them unless requested
- Tests should test edge cases and the general idea but shoudl not be exhaustive
- Tests are only required for complex logic and are usually not needed
- After iterating on code, run `make test` to ensure tests pass
- Only write tests for functions that are data in data out
- Tests live next to files so thing.py and thing_test.py
- Use bdd style tests

## Code Organization Principles

- Prefer small functions with clear "data in, data out" patterns
- Router files should only contain route handlers and route-specific helpers
- Route handlers should be thin wrappers that compose helper functions
- Use FastAPI dependency injection for cross-cutting concerns like authentication
- Extract business logic into utility modules (e.g., `feed_utils.py`)
- Put authentication/authorization logic in `auth.py`
- Add query methods as class methods on the model they query
- Define TypedDict types for structured data instead of passing raw dictionaries
- Organize helpers into modules based on domain, not technical layer

## Puzzle Data Storage Architecture

### Directory Structure
Puzzle data is stored in `data/puzzles/{folder_name}/` where `{folder_name}` is either the source's `short_code` (if set) or the source's UUID.

Each source folder contains three subdirectories:
- `import/` - Staging area for puzzles to be imported
- `puzzles/` - Successfully imported puzzles
- `errors/` - Failed imports with error information

Additionally, each source folder can contain:
- `icon.png` - Optional source icon image (512x512px recommended) that appears in the JSON Feed

### Import Process Flow
1. **Staging**: Puzzles are placed in the `import/` folder with two required files:
   - `{filename}.puz` - The crossword puzzle file in .puz format
   - `{filename}.meta.json` - Metadata file (see format below)

2. **Processing**: The `FileProcessor` scans all source `import/` folders and processes puzzle pairs that have both files present

3. **Success**: If import succeeds:
   - Puzzle is added to the database with a generated UUID
   - Both files are moved to `puzzles/` and renamed to date-based filenames:
     - `{puzzle_date}.puz` and `{puzzle_date}.meta.json` (e.g., `2020-12-21.puz`)
     - If a puzzle with the same date already exists, a counter is appended (e.g., `2020-12-21-2.puz`, `2020-12-21-3.puz`)
   - The filename (without path) is stored in the puzzle's `filename` field
   - Preview images use the same naming scheme (e.g., `2020-12-21.preview.png`)

4. **Failure**: If import fails:
   - Both files are moved to `errors/` and renamed with timestamp: `{filename}_{timestamp}.puz` and `{filename}_{timestamp}.meta.json`
   - An error file is created: `{filename}_{timestamp}.error.txt` containing the error message

### Metadata File Format (.meta.json)
The metadata file is a JSON file with the following structure:
```json
{
  "puzzle_date": "YYYY-MM-DD",  // Required: ISO date format
  "title": "Puzzle Title",       // Optional: Falls back to .puz file title
  "author": "Author Name"        // Optional: Falls back to .puz file author
}
```

**Required Fields**:
- `puzzle_date` (string): Must be in ISO format (YYYY-MM-DD), used for the puzzle's date field

**Optional Fields**:
- `title` (string): If not provided or empty, falls back to the title in the .puz file, then to "Untitled"
- `author` (string): If not provided or empty, falls back to the author in the .puz file

### Key Implementation Details
- Sources automatically create their folder structure when inserted into the database
- Sources automatically delete their folder structure when removed from the database
- The processor only processes puzzle pairs where both .puz and .meta.json files exist
- File operations are atomic - files are moved (not copied) to prevent duplicates
