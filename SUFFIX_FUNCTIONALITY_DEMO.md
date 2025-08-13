# File Suffix Functionality for Batch Processing

## Overview

The batch processing panel now supports **file name suffixes** for both reading existing files and writing new files. This allows for more flexible file management and prevents overwriting existing content.

## New Features

### 1. Read Suffix
- **Purpose**: Specify a suffix for files to read when using the `%description%` wildcard
- **UI Control**: "Read suffix" text field with hint "e.g., _tags"
- **Example**: If you set read suffix to `_tags`, then `%description%` will read from `image1_tags.txt` instead of `image1.txt`

### 2. Write Suffix  
- **Purpose**: Specify a suffix for output files to prevent overwriting existing files
- **UI Control**: "Write suffix" text field with hint "e.g., _desc"
- **Example**: If you set write suffix to `_desc`, output will be saved to `image1_desc.txt` instead of `image1.txt`

## Usage Examples

### Example 1: Basic Usage (Current Behavior)
- **Read suffix**: (empty)
- **Write suffix**: (empty)
- **Behavior**: 
  - `%description%` reads from `image1.txt`
  - Output saves to `image1.txt`
  - **Same as before** - maintains backward compatibility

### Example 2: Read Existing Tags, Write New Descriptions
- **Read suffix**: `_tags`
- **Write suffix**: `_desc`
- **Prompt**: "Based on these tags: %description%, write a detailed description"
- **Behavior**:
  - `%description%` reads from `image1_tags.txt`
  - Output saves to `image1_desc.txt`
  - **Preserves existing files** - no overwriting

### Example 3: Read Descriptions, Write Enhanced Versions
- **Read suffix**: (empty)
- **Write suffix**: `_enhanced`
- **Prompt**: "Enhance this description: %description%"
- **Behavior**:
  - `%description%` reads from `image1.txt`
  - Output saves to `image1_enhanced.txt`
  - **Creates new enhanced versions** without losing originals

### Example 4: Multiple Processing Passes
- **First pass**:
  - Read suffix: (empty)
  - Write suffix: `_basic`
  - Prompt: "Describe this image briefly"
  - Result: `image1_basic.txt`

- **Second pass**:
  - Read suffix: `_basic`
  - Write suffix: `_detailed`  
  - Prompt: "Based on this basic description: %description%, add detailed analysis"
  - Result: `image1_detailed.txt`

## File Name Rules

### Suffix Formatting
- **Automatic underscore**: If suffix doesn't start with `_`, it's added automatically
- **Examples**:
  - Input: `tags` → Becomes: `_tags`
  - Input: `_desc` → Stays: `_desc`

### File Path Resolution
- **With source path**: `image1.png` → `image1_suffix.txt` (same directory)
- **Without source path**: Uses current directory

## UI Layout

```
File name suffixes (optional):
[Read suffix: _______] (for %description% wildcard)
[Write suffix: _______] (for output files)
```

## Benefits

1. **Prevent Overwriting**: Keep existing files safe while creating new ones
2. **Multiple Processing Passes**: Build upon previous results iteratively  
3. **Organized Output**: Separate different types of processing results
4. **Backward Compatible**: Empty suffixes work exactly as before
5. **Flexible Workflows**: Support complex multi-step processing pipelines

## Technical Implementation

### Methods Added
- **`_get_read_filename(image)`**: Gets filename for reading with read suffix
- **`_get_output_filename(image)`**: Enhanced to support write suffix  

### UI Controls Added
- **`self.read_suffix_text`**: TextCtrl for read suffix input
- **`self.write_suffix_text`**: TextCtrl for write suffix input

### Wildcard Processing Updated
- **`%description%`** now uses `_get_read_filename()` instead of `_get_output_filename()`

## Example File Structure After Processing

```
images/
├── image1.png
├── image1_tags.txt      # Original tags (preserved)
├── image1_desc.txt      # New descriptions (created)
├── image2.png
├── image2_tags.txt      # Original tags (preserved)  
└── image2_desc.txt      # New descriptions (created)
```

This enhancement makes the batch processing much more flexible and powerful for complex workflows!
