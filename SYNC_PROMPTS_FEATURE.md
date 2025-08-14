# Sync from Defaults Feature

## Overview

The Prompts tab now includes a **"Sync from Defaults"** button that allows users to pull in any new prompts that have been added to the default `llm_prompts.json` file but are not yet in their personal configuration.

## Problem Solved

When new prompts are added to the default configuration file (like the recent %description% wildcard enhancements), existing users won't see these new prompts because:

1. The application loads prompts from the user's personal config (`~/.llamalot/prompts.json`) 
2. This personal config was created from the defaults when first run
3. New prompts added to defaults later don't automatically appear

## Solution

The **"Sync from Defaults"** button:

1. **Compares** the user's current prompt configuration with the default `llm_prompts.json`
2. **Identifies** any prompts that exist in defaults but not in the user's config
3. **Adds** missing prompts without overwriting existing ones
4. **Updates** the categories list automatically
5. **Saves** the updated configuration
6. **Refreshes** the UI to show new prompts immediately

## How to Use

1. **Open** the Prompts tab
2. **Click** the "Sync from Defaults" button (located next to "Base Prompts:" label)
3. **Wait** for the progress dialog to complete
4. **Review** the results showing how many prompts were added
5. **Browse** the updated prompt lists to find new options

## What Gets Synced

### Base Prompts
- New template prompts for different use cases
- Additional categories and input types

### Extra Prompts  
- New modifier prompts like the %description% wildcard enhancements:
  - **verify_description_tags**: "Please verify that your response addresses all aspects mentioned in these tags: %description%"
  - **expand_description_tags**: "Please expand on each of these image board tags in your response: %description%"

### Categories
- Automatically updated to include categories from new prompts

## Safety Features

- **Non-destructive**: Never overwrites existing prompts
- **Backup**: Original configuration is preserved
- **Validation**: JSON structure is validated before saving
- **Error handling**: Graceful failure with user notification
- **Progress feedback**: Shows sync progress and results

## Technical Implementation

### Backend Changes
- **PromptsManager.sync_from_defaults()**: Core sync logic
- **Categories auto-update**: Rebuilds category list from all prompts
- **JSON validation**: Ensures configuration integrity

### UI Changes
- **Sync button**: Added to prompts tab header
- **Progress dialog**: Shows sync status and results
- **Result notification**: Detailed feedback on what was synced

## Use Cases

### For Users
- **Get latest prompts**: Access new features without manual configuration
- **Stay updated**: Automatically benefit from prompt improvements
- **Easy maintenance**: One-click synchronization

### For Developers
- **Distribute updates**: New prompts reach existing users
- **Feature rollout**: Gradual deployment of new prompt templates
- **Version compatibility**: Maintains backward compatibility

## Example Results

```
Sync Complete

Successfully synced 2 new prompts:
• 0 base prompts  
• 2 extra prompts

The following prompts were added:
- verify_description_tags (content_focus)
- expand_description_tags (content_focus)
```

## Future Enhancements

- **Version checking**: Compare prompt versions for updates
- **Selective sync**: Choose which prompts to import
- **Auto-sync**: Optional automatic synchronization on startup
- **Conflict resolution**: Handle modified default prompts

This feature ensures that users can easily access new prompt templates and enhancements without losing their existing customizations.
