const { test, expect } = require("@playwright/test");
const {
  openControlRoom,
  pendingCard,
  reminderCard,
  sendAssistantMessage,
  uniqueSuffix,
  waitForCompanionAccessCard,
  waitForMobileReady,
} = require("./helpers");

test.describe("Zivra smoke suite", () => {
  test("loads the control room and handles a safe system request", async ({ page }) => {
    const sessionId = uniqueSuffix("system-session");
    const token = uniqueSuffix("system");
    const prompt = `Show me my system status for ${token}`;

    await openControlRoom(page, sessionId);
    await sendAssistantMessage(page, prompt);

    const bubbles = page.locator("#chat-thread .chat-bubble");
    await expect(bubbles).toHaveCount(2);
    await expect(bubbles.nth(0)).toContainText(prompt);
    await expect(bubbles.nth(1)).toContainText("Collected a local system snapshot.");
  });

  test("opens the command palette with Ctrl+K and runs a safe command", async ({ page }) => {
    const sessionId = uniqueSuffix("palette-session");

    await openControlRoom(page, sessionId);
    await page.keyboard.press("Control+K");

    const dialog = page.getByRole("dialog", { name: "What would you like to do?" });
    await expect(dialog).toBeVisible();

    const searchbox = page.getByRole("searchbox", { name: "Search commands and screens" });
    await searchbox.fill("system status");
    await dialog.getByRole("button", { name: /Run system status check/i }).click();

    await expect(dialog).toBeHidden();
    const bubbles = page.locator("#chat-thread .chat-bubble");
    await expect(bubbles.nth(1)).toContainText("Collected a local system snapshot.");
  });

  test("stages and rejects a low-risk approval without side effects", async ({ page }) => {
    const sessionId = uniqueSuffix("reject-session");
    const token = uniqueSuffix("reject");
    const prompt = `Open https://example.com/${token}`;

    await openControlRoom(page, sessionId);
    await sendAssistantMessage(page, prompt);

    const card = pendingCard(page, token);
    await expect(card).toBeVisible();
    await card.getByRole("button", { name: "Reject" }).click();

    await expect(card).toHaveCount(0);
    await expect(page.locator("#chat-thread")).toContainText("Action rejected from the dashboard.");
  });

  test("creates and completes a reminder through the approval flow", async ({ page }) => {
    const sessionId = uniqueSuffix("reminder-session");
    const token = uniqueSuffix("reminder");
    const prompt = `Remind me tomorrow at 9am to review ${token}`;

    await openControlRoom(page, sessionId);
    await sendAssistantMessage(page, prompt);

    const approvalCard = pendingCard(page, token);
    await expect(approvalCard).toBeVisible();
    await approvalCard.getByRole("button", { name: "Approve" }).click();

    const card = reminderCard(page, token);
    await expect(card).toBeVisible();
    await card.getByRole("button", { name: "Mark done" }).click();
    await expect(card).toContainText("Completed");
  });

  test("loads preferred companion handoff data into email and WhatsApp drafts", async ({ page }) => {
    const sessionId = uniqueSuffix("handoff-draft-session");

    await openControlRoom(page, sessionId);
    const handoffCard = await waitForCompanionAccessCard(page);

    await handoffCard.getByRole("button", { name: "Use in email" }).click();
    await expect(page.locator("#email-subject")).toHaveValue(/Zivra handoff:/);
    await expect(page.locator("#email-body")).toHaveValue(new RegExp(sessionId));

    await handoffCard.getByRole("button", { name: "Use in WhatsApp" }).click();
    await expect(page.locator("#whatsapp-body")).toHaveValue(new RegExp(sessionId));
    await expect(page.locator("#whatsapp-body")).toHaveValue(/Zivra mobile handoff/);
  });

  test("opens the mobile handoff link on the same session and shows recent history", async ({ page, context }) => {
    const sessionId = uniqueSuffix("mobile-session");
    const token = uniqueSuffix("handoff");
    const prompt = `Show me my system status for ${token}`;

    await openControlRoom(page, sessionId);
    await sendAssistantMessage(page, prompt);

    const handoffCard = await waitForCompanionAccessCard(page);
    const mobileHref = await handoffCard.getByRole("link", { name: "Open mobile" }).getAttribute("href");
    expect(mobileHref).toBeTruthy();
    expect(mobileHref).toContain(`session_id=${encodeURIComponent(sessionId)}`);

    const mobilePage = await context.newPage();
    await mobilePage.goto(mobileHref);
    await waitForMobileReady(mobilePage);
    await expect(mobilePage.locator("#session-history")).toContainText(prompt);
  });
});
