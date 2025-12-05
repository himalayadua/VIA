import { test, expect, Page } from '@playwright/test';

/**
 * E2E Tests for Canvas Card Types
 * 
 * Tests all 5 card types: RichText, Todo, Video, Link, Reminder
 */

test.describe('Canvas Card Types', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    await page.goto('/');
    
    // Wait for app to load
    await page.waitForSelector('[data-testid="canvas-manager"]', { timeout: 10000 });
    
    // Create a new canvas for testing
    await page.click('text=New Canvas');
    await page.fill('input[placeholder*="Canvas name"]', 'Test Canvas - Card Types');
    await page.click('button:has-text("Create")');
    
    // Wait for canvas to load
    await page.waitForSelector('.react-flow', { timeout: 10000 });
  });

  test.afterEach(async () => {
    // Clean up: delete the test canvas
    // This would require implementing a delete function or API call
  });

  test('should create a Rich Text card via context menu', async () => {
    // Right-click on canvas to open context menu
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    
    // Wait for context menu
    await page.waitForSelector('[data-testid="context-menu"]', { timeout: 5000 });
    
    // Click "Add Rich Text Card"
    await page.click('text=Add Rich Text Card');
    
    // Wait for card to appear
    await page.waitForSelector('[data-card-type="rich_text"]', { timeout: 5000 });
    
    // Verify card exists
    const card = page.locator('[data-card-type="rich_text"]').first();
    await expect(card).toBeVisible();
    
    // Verify card has correct theme (emerald/green)
    await expect(card).toHaveClass(/bg-emerald-500/);
  });

  test('should edit Rich Text card content', async () => {
    // Create a Rich Text card
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    await page.click('text=Add Rich Text Card');
    await page.waitForSelector('[data-card-type="rich_text"]');
    
    const card = page.locator('[data-card-type="rich_text"]').first();
    
    // Click on title to edit
    const titleInput = card.locator('input[placeholder*="Title"]');
    await titleInput.click();
    await titleInput.fill('Test Rich Text Card');
    
    // Click on content to edit
    const contentArea = card.locator('textarea, [contenteditable="true"]').first();
    await contentArea.click();
    await contentArea.fill('This is **markdown** content with _formatting_.');
    
    // Click outside to save
    await canvas.click({ position: { x: 100, y: 100 } });
    
    // Verify content is saved
    await expect(card.locator('text=Test Rich Text Card')).toBeVisible();
  });

  test('should create a Todo card with checklist', async () => {
    // Right-click on canvas
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    
    // Click "Add Todo Card"
    await page.click('text=Add Todo Card');
    
    // Wait for card to appear
    await page.waitForSelector('[data-card-type="todo"]', { timeout: 5000 });
    
    const card = page.locator('[data-card-type="todo"]').first();
    await expect(card).toBeVisible();
    
    // Verify card has correct theme (blue)
    await expect(card).toHaveClass(/bg-blue-500/);
    
    // Add todo items
    const addItemInput = card.locator('input[placeholder*="Add"]');
    await addItemInput.fill('First todo item');
    await addItemInput.press('Enter');
    
    await addItemInput.fill('Second todo item');
    await addItemInput.press('Enter');
    
    // Verify items appear
    await expect(card.locator('text=First todo item')).toBeVisible();
    await expect(card.locator('text=Second todo item')).toBeVisible();
    
    // Check first item
    const firstCheckbox = card.locator('input[type="checkbox"]').first();
    await firstCheckbox.check();
    
    // Verify progress bar updates
    const progressBar = card.locator('[data-testid="progress-bar"]');
    await expect(progressBar).toBeVisible();
  });

  test('should create a Video card with YouTube URL', async () => {
    // Right-click on canvas
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    
    // Click "Add Video Card"
    await page.click('text=Add Video Card');
    
    // Wait for card to appear
    await page.waitForSelector('[data-card-type="video"]', { timeout: 5000 });
    
    const card = page.locator('[data-card-type="video"]').first();
    await expect(card).toBeVisible();
    
    // Verify card has correct theme (purple)
    await expect(card).toHaveClass(/bg-purple-500/);
    
    // Enter YouTube URL
    const urlInput = card.locator('input[placeholder*="URL"]');
    await urlInput.fill('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    await urlInput.press('Enter');
    
    // Verify YouTube iframe appears
    await page.waitForSelector('iframe[src*="youtube.com/embed"]', { timeout: 5000 });
    const iframe = card.locator('iframe');
    await expect(iframe).toBeVisible();
  });

  test('should create a Link card with URL and description', async () => {
    // Right-click on canvas
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    
    // Click "Add Link Card"
    await page.click('text=Add Link Card');
    
    // Wait for card to appear
    await page.waitForSelector('[data-card-type="link"]', { timeout: 5000 });
    
    const card = page.locator('[data-card-type="link"]').first();
    await expect(card).toBeVisible();
    
    // Verify card has correct theme (orange)
    await expect(card).toHaveClass(/bg-orange-500/);
    
    // Enter URL
    const urlInput = card.locator('input[placeholder*="URL"]');
    await urlInput.fill('https://example.com');
    
    // Enter description
    const descInput = card.locator('textarea[placeholder*="description"]');
    await descInput.fill('Example website link');
    
    // Click outside to save
    await canvas.click({ position: { x: 100, y: 100 } });
    
    // Verify link is clickable
    const link = card.locator('a[href="https://example.com"]');
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('target', '_blank');
  });

  test('should create a Reminder card with date and time', async () => {
    // Right-click on canvas
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    
    // Click "Add Reminder Card"
    await page.click('text=Add Reminder Card');
    
    // Wait for card to appear
    await page.waitForSelector('[data-card-type="reminder"]', { timeout: 5000 });
    
    const card = page.locator('[data-card-type="reminder"]').first();
    await expect(card).toBeVisible();
    
    // Verify card has correct theme (amber/yellow)
    await expect(card).toHaveClass(/bg-amber-500/);
    
    // Enter date
    const dateInput = card.locator('input[type="date"]');
    await dateInput.fill('2025-12-31');
    
    // Enter time
    const timeInput = card.locator('input[type="time"]');
    await timeInput.fill('14:30');
    
    // Enter description
    const descInput = card.locator('textarea[placeholder*="description"]');
    await descInput.fill('Important deadline');
    
    // Click outside to save
    await canvas.click({ position: { x: 100, y: 100 } });
    
    // Verify reminder displays date and time
    await expect(card.locator('text=2025-12-31')).toBeVisible();
    await expect(card.locator('text=14:30')).toBeVisible();
  });

  test('should add tags to any card type', async () => {
    // Create a Rich Text card
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    await page.click('text=Add Rich Text Card');
    await page.waitForSelector('[data-card-type="rich_text"]');
    
    const card = page.locator('[data-card-type="rich_text"]').first();
    
    // Add tags
    const tagInput = card.locator('input[placeholder*="tag"]');
    await tagInput.fill('important');
    await tagInput.press('Enter');
    
    await tagInput.fill('testing');
    await tagInput.press('Enter');
    
    // Verify tags appear
    await expect(card.locator('text=important')).toBeVisible();
    await expect(card.locator('text=testing')).toBeVisible();
    
    // Remove a tag
    const removeButton = card.locator('[data-tag="important"] button').first();
    await removeButton.click();
    
    // Verify tag is removed
    await expect(card.locator('text=important')).not.toBeVisible();
    await expect(card.locator('text=testing')).toBeVisible();
  });

  test('should delete a card', async () => {
    // Create a card
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    await page.click('text=Add Rich Text Card');
    await page.waitForSelector('[data-card-type="rich_text"]');
    
    const card = page.locator('[data-card-type="rich_text"]').first();
    
    // Right-click on card
    await card.click({ button: 'right' });
    
    // Click delete
    await page.click('text=Delete');
    
    // Verify card is removed
    await expect(card).not.toBeVisible();
  });

  test('should duplicate a card', async () => {
    // Create a card with content
    const canvas = page.locator('.react-flow__pane');
    await canvas.click({ button: 'right', position: { x: 400, y: 300 } });
    await page.click('text=Add Rich Text Card');
    await page.waitForSelector('[data-card-type="rich_text"]');
    
    const card = page.locator('[data-card-type="rich_text"]').first();
    
    // Add content
    const titleInput = card.locator('input[placeholder*="Title"]');
    await titleInput.fill('Original Card');
    
    // Right-click on card
    await card.click({ button: 'right' });
    
    // Click duplicate
    await page.click('text=Duplicate');
    
    // Verify duplicate exists
    const cards = page.locator('[data-card-type="rich_text"]');
    await expect(cards).toHaveCount(2);
    
    // Verify duplicate has same content
    const duplicateCard = cards.nth(1);
    await expect(duplicateCard.locator('text=Original Card')).toBeVisible();
  });
});
