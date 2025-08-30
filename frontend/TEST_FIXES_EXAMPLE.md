# Test Fixes Examples for User Story 3

## Fix 1: React Act() Warnings

### Problem
```
Warning: An update to ChatInput inside a test was not wrapped in act(...).
```

### Solution
Wrap async user interactions in act():

```typescript
// ❌ Before (causes warnings)
await user.type(textarea, 'test message');
await user.keyboard('{Enter}');

// ✅ After (properly wrapped)
await act(async () => {
  await user.type(textarea, 'test message');
  await user.keyboard('{Enter}');
});
```

## Fix 2: Loading State Text Matching

### Problem
Test fails to find "HSA Assistant is thinking..." text.

### Solution
The text is correct in implementation. Issue is likely timing. Fix with better waitFor:

```typescript
// ❌ Before (timing issue)
expect(screen.getByText('HSA Assistant is thinking...')).toBeInTheDocument();

// ✅ After (with proper timing)
await waitFor(() => {
  expect(screen.getByText('HSA Assistant is thinking...')).toBeInTheDocument();
}, { timeout: 1000 });
```

## Fix 3: Router Future Flags

### Problem
```
React Router Future Flag Warning: React Router will begin wrapping state updates in `React.startTransition` in v7
```

### Solution
Add future flags to BrowserRouter in tests:

```typescript
// ❌ Before
<BrowserRouter>
  <ChatPage />
</BrowserRouter>

// ✅ After  
<BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
  <ChatPage />
</BrowserRouter>
```

## Fix 4: Test Timing Issues

### Problem
Tests fail due to async timing issues with API calls.

### Solution
Use more specific waitFor conditions:

```typescript
// ❌ Before (generic wait)
await waitFor(() => {
  expect(mockAskQuestion).toHaveBeenCalled();
});

// ✅ After (specific condition)
await waitFor(() => {
  expect(screen.getByText('Expected response text')).toBeInTheDocument();
}, { timeout: 2000 });
```

## Fix 5: Mock Data Consistency

### Problem
Tests expect specific response formats that don't match mocks.

### Solution
Ensure mock data structure matches actual API:

```typescript
// ✅ Consistent mock structure
const mockQAResponse: QAResponse = {
  answer: 'Test answer',
  confidence_score: 0.9,
  citations: [{
    document_name: 'Test Doc',
    page_number: 1,
    excerpt: 'Test excerpt',
    relevance_score: 0.85,
  }],
  source_documents: ['Test Doc'],
  processing_time_ms: 100,
  created_at: '2024-01-15T10:00:00Z',
};
```

## Implementation Priority

1. **High Priority**: Act() warnings - affects all interactive tests
2. **Medium Priority**: Timing issues - affects reliability  
3. **Low Priority**: Router warnings - cosmetic, doesn't affect functionality

## Quick Fix Script

Run these commands to apply common fixes:

```bash
# Update all test files with act() wrappers
npm run test:fix-act-warnings

# Run tests with increased timeout
npm test -- --testTimeout=10000

# Run specific test file with fixes
npm test ChatPage.integration.test.tsx -- --run --reporter=verbose
```