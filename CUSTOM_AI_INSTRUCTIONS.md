# Custom AI Review Instructions

You can now add custom instructions to the AI review prompt by adding a special field in your Pull Request description.

## How to Use

In your PR description, add a line with the following format:

```
** Custom AI Review Instructions: ** `Your custom instructions here`
```

### Example

```markdown
This PR adds a new feature for user authentication.

** Custom AI Review Instructions: ** `Please pay special attention to security vulnerabilities in authentication logic and ensure proper input validation.`

- [x] Do you have important changes?
- [ ] Do you want to explicitly use Claude Sonnet 4?
```

## What This Does

The custom instructions you provide will be added to the AI review prompt as an "ADDITIONAL CUSTOM INSTRUCTIONS" section. This allows you to:

- Ask the AI to focus on specific aspects of your code
- Provide context about what to look for
- Request specific types of feedback
- Guide the AI's attention to particular areas of concern

## Examples of Good Custom Instructions

- `Focus on performance optimizations and memory usage in the data processing functions`
- `Pay attention to error handling and edge cases in the API endpoints`
- `Review the database queries for potential SQL injection vulnerabilities`
- `Check for proper React hooks usage and component lifecycle management`
- `Ensure the new caching logic doesn't introduce race conditions`

## Notes

- Keep instructions concise and specific
- The AI will still follow all the standard review rules (JSON output format, line-by-line comments, etc.)
- Custom instructions are additional guidance, not replacement for the standard review criteria
- Instructions are logged in the workflow output for debugging purposes
