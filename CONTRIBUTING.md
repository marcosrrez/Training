# Contributing to Hybrid Athlete Platform

Thank you for your interest in contributing to the Hybrid Athlete Platform!

## Development Setup

See the [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for detailed setup instructions.

## Code Style

### Python (Backend)
- Follow PEP 8 style guide
- Use Black for code formatting: `black .`
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Docstrings for all public functions and classes

Example:
```python
def analyze_goal_feasibility(
    goal: Goal,
    assessment: Assessment,
    constraints: Constraints
) -> FeasibilityAssessment:
    """
    Analyze whether a goal is realistic given current state.

    Args:
        goal: The user's training goal
        assessment: Current fitness assessment
        constraints: Time and resource constraints

    Returns:
        FeasibilityAssessment with probability and recommendations
    """
    pass
```

### TypeScript/React (Frontend)
- Use Prettier for formatting
- Use ESLint for linting
- Functional components with hooks
- TypeScript strict mode enabled
- Descriptive component and prop names

### Testing
- Write tests for all new features
- Maintain >80% code coverage
- Unit tests for algorithms
- Integration tests for API endpoints
- E2E tests for critical user flows

## Git Workflow

### Branch Naming
- Feature: `feature/description-of-feature`
- Bug fix: `fix/description-of-bug`
- Documentation: `docs/what-was-documented`
- Refactor: `refactor/what-was-refactored`

### Commit Messages
Follow Conventional Commits format:

```
type(scope): brief description

Longer description if needed

Refs: #issue-number
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(algorithm): implement methodology selector

Added logic to choose optimal training methodology based on
user goals, fitness level, and time constraints.

Refs: #12
```

```
fix(api): correct goal feasibility calculation

Fixed bug where detraining period was not being factored
into timeline estimates.

Refs: #45
```

## Pull Request Process

1. **Create a branch** from `main`
2. **Make your changes** with clear, atomic commits
3. **Write/update tests** for your changes
4. **Update documentation** if needed
5. **Run tests locally**: `pytest` (backend) and `npm test` (frontend)
6. **Run linters**: `black .` and `flake8` (backend)
7. **Create pull request** with clear description
8. **Link related issues** in PR description
9. **Wait for review** and address feedback
10. **Merge** after approval

### PR Description Template
```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues
Fixes #issue-number

## Testing
Describe how you tested these changes.

## Screenshots (if applicable)
Add screenshots for UI changes.

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] All tests passing
- [ ] No new warnings
```

## Research Contributions

When adding research to the database:

1. **Use the template**: `research_database/templates/research_article_template.yaml`
2. **Verify accuracy**: Double-check citations and findings
3. **Quality sources only**: Peer-reviewed journals, meta-analyses preferred
4. **Complete metadata**: Fill all fields in the template
5. **Practical application**: Always include "how to apply this"
6. **Cite conflicts**: Note contradictory research when relevant

## Algorithm Development

When building algorithms:

1. **Research first**: Base all decisions on scientific evidence
2. **Document sources**: Cite research in code comments
3. **Test edge cases**: Think about unusual user scenarios
4. **Conservative defaults**: When in doubt, err on the side of caution
5. **Explain decisions**: Add comments explaining "why" not just "what"

## Questions?

- Open an issue for feature requests or bugs
- Tag issues with appropriate labels
- Be respectful and constructive
- Ask for help when stuck

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Assume good intentions
- Help others learn and grow
- Prioritize user safety and outcomes

Thank you for contributing! 🙏
