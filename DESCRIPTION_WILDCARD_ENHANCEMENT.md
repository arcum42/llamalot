# %description% Wildcard Enhancement for Image Board Tag Integration

## Overview

Added specialized extra prompts to enhance the existing `%description%` wildcard functionality in batch processing. These prompts are designed specifically for working with image board tags and tag-based workflows.

## What Was Added

### New Extra Prompts in llm_prompts.json

Added 4 new prompts in the `content_focus` category to support different approaches to working with image board tags:

1. **append_description** - "Please append the following tags to your response: %description%"
   - Simple tag appending at the end of responses
   - Useful for ensuring specific tags are included in output

2. **integrate_description_tags** - "Please integrate these image tags naturally into your analysis: %description%"
   - Natural integration of tags into analysis content
   - Better for cohesive content where tags should flow naturally

3. **verify_description_tags** - "Please verify that your response addresses all aspects mentioned in these tags: %description%"
   - Quality control approach to ensure tag coverage
   - Useful for comprehensive analysis requirements

4. **expand_description_tags** - "Please expand on each of these image board tags in your response: %description%"
   - Detailed exploration of each individual tag
   - Best for educational or detailed analysis scenarios

## How It Works

### Integration with Existing %description% Wildcard

The `%description%` wildcard in batch processing reads `.txt` files paired with images and substitutes their content into prompts. These new extra prompts provide different ways to incorporate that tag data:

```
Image: cute_cat.jpg
Tags file: cute_cat.txt (contains: "cat, cute, fluffy, orange, sitting")
```

### Usage Examples

1. **Using append_description**:
   - Base prompt: "Describe this image"
   - Result: "Describe this image. Please append the following tags to your response: cat, cute, fluffy, orange, sitting"

2. **Using integrate_description_tags**:
   - Base prompt: "Analyze this artwork"
   - Result: "Analyze this artwork. Please integrate these image tags naturally into your analysis: cat, cute, fluffy, orange, sitting"

### Accessing in the UI

1. Open the **Prompts** tab
2. Filter by **content_focus** category
3. Select one of the 4 new description-related prompts
4. Use "Use in Batch" button to apply to batch processing
5. The prompt will work with any batch operation that has `%description%` wildcard support

## Benefits

- **Flexibility**: Different approaches for different use cases
- **Natural Integration**: Tags can be incorporated smoothly into analysis
- **Quality Control**: Verification prompts ensure comprehensive coverage
- **Educational**: Expansion prompts provide detailed tag exploration
- **Batch Efficiency**: Works with existing batch processing infrastructure

## Technical Implementation

- Added to existing `llm_prompts.json` configuration
- Loaded automatically by `PromptsManager`
- Available immediately in the Prompts tab UI
- Fully compatible with existing batch processing %description% wildcard
- No changes required to batch processing logic

## Testing Status

✅ JSON validation passed
✅ PromptsManager loads all 4 new prompts correctly
✅ Application starts successfully with enhanced prompts
✅ Prompts tab displays new options in content_focus category

## Usage Workflow

1. Prepare images with paired `.txt` files containing tags
2. Select appropriate description integration prompt from Prompts tab
3. Apply to batch processing using "Use in Batch" button
4. Run batch processing - %description% wildcard will incorporate tags per selected prompt style
5. Review results with enhanced tag integration

This enhancement makes the existing %description% wildcard functionality much more versatile for image board tag workflows while maintaining full backward compatibility.
