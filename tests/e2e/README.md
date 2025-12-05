# Via Canvas E2E Tests

End-to-end tests for Via Canvas using Playwright.

## Setup

1. Install Playwright:
```bash
npm install -D @playwright/test
npx playwright install
```

2. Make sure all services are running:
```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend
npm run server

# Terminal 3: Python AI Service
cd chat_service
python app.py
```

## Running Tests

### Run all tests
```bash
npx playwright test
```

### Run specific test file
```bash
npx playwright test tests/e2e/canvas/card-types.spec.ts
```

### Run tests in headed mode (see browser)
```bash
npx playwright test --headed
```

### Run tests in debug mode
```bash
npx playwright test --debug
```

### Run tests in specific browser
```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## View Test Results

### HTML Report
```bash
npx playwright show-report
```

### View traces for failed tests
```bash
npx playwright show-trace trace.zip
```

## Test Structure

```
tests/e2e/
├── canvas/
│   ├── card-types.spec.ts      - Test all 5 card types
│   ├── layouts.spec.ts          - Test layout algorithms
│   ├── hierarchy.spec.ts        - Test parent-child relationships
│   ├── search.spec.ts           - Test search functionality
│   └── context-menu.spec.ts     - Test context menus
├── chat/
│   ├── messaging.spec.ts        - Test chat messaging
│   ├── file-upload.spec.ts      - Test file uploads
│   ├── tool-execution.spec.ts   - Test tool execution display
│   └── sessions.spec.ts         - Test session management
└── ai/
    ├── url-extraction.spec.ts   - Test URL extraction
    ├── grow-card.spec.ts        - Test grow feature
    └── learning-features.spec.ts - Test learning features
```

## Writing Tests

### Test Template
```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Setup code
  });

  test('should do something', async ({ page }) => {
    // Test code
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

### Best Practices

1. **Use data-testid attributes** for reliable selectors
2. **Wait for elements** before interacting
3. **Clean up** after tests (delete test data)
4. **Use descriptive test names** that explain what is being tested
5. **Keep tests independent** - each test should work in isolation
6. **Use page object pattern** for complex pages

### Debugging Tips

1. Use `await page.pause()` to pause execution
2. Use `--headed` flag to see browser
3. Use `--debug` flag for step-by-step debugging
4. Check screenshots in `test-results/` folder
5. View traces for failed tests

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch

See `.github/workflows/test.yml` for configuration.

## Troubleshooting

### Tests timing out
- Increase timeout in `playwright.config.ts`
- Check if services are running
- Check network connectivity

### Elements not found
- Add `data-testid` attributes to components
- Use `waitForSelector` with longer timeout
- Check if element is in viewport

### Flaky tests
- Add explicit waits
- Use `waitForLoadState('networkidle')`
- Increase retries in config

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright API Reference](https://playwright.dev/docs/api/class-playwright)
