# Contributing to Employee Attendance System

Thank you for considering contributing to this project! 🎉

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- Your environment (OS, Python version, etc.)

### Suggesting Features

Feature requests are welcome! Please:
- Check if the feature already exists
- Provide clear use case
- Explain why it would be useful
- Consider implementation complexity

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   - Ensure all features work
   - Test on different scenarios
   - Check for any warnings or errors

5. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of changes"
   ```
   Use prefixes:
   - `Add:` for new features
   - `Fix:` for bug fixes
   - `Update:` for improvements
   - `Remove:` for deletions
   - `Docs:` for documentation

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create Pull Request**
   - Provide clear description
   - Reference related issues
   - Add screenshots if UI changes

## Code Style Guidelines

### Python
- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings for functions
- Keep functions focused and small
- Use type hints where appropriate

### Example:
```python
def calculate_productivity_score(attendance_data: dict) -> float:
    """
    Calculate employee productivity score.
    
    Args:
        attendance_data: Dictionary containing attendance records
        
    Returns:
        float: Productivity score between 0 and 100
    """
    # Implementation
    pass
```

### Comments
- Explain WHY, not WHAT
- Keep comments up-to-date
- Use clear, concise language

### Database
- Use parameterized queries (prevent SQL injection)
- Close connections properly
- Handle errors gracefully

## Development Setup

1. Clone your fork
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Make changes
5. Test thoroughly

## Testing

Before submitting PR:
- [ ] Test face recognition with multiple faces
- [ ] Test all CRUD operations
- [ ] Verify ML models train correctly
- [ ] Check all navigation buttons work
- [ ] Test on different screen sizes
- [ ] Ensure no console errors/warnings

## Questions?

Feel free to:
- Open an issue for discussion
- Ask in pull request comments
- Contact maintainers

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn

Thank you for contributing! 🚀
