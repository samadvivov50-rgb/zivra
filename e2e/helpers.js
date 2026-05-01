const { expect } = require("@playwright/test");

function uniqueSuffix(label) {
  return `${label}-${Date.now()}-${Math.floor(Math.random() * 10_000)}`;
}

async function openControlRoom(page, sessionId) {
  await page.goto(`/ui/?session_id=${encodeURIComponent(sessionId)}`);
  await expect(page.locator("#assistant-name-heading")).toBeVisible();
  await expect(page.locator("#connection-status")).toHaveText("Backend connected");
  await expect(page.locator("#assistant-form")).toBeVisible();
}

async function waitForMobileReady(page) {
  await expect(page.locator("#assistant-name")).toBeVisible();
  await expect(page.locator("#connection-status")).toHaveText("Backend connected");
  await expect(page.locator("#session-history")).toBeVisible();
}

async function sendAssistantMessage(page, message) {
  const responsePromise = page.waitForResponse((response) => {
    return response.url().includes("/assistant/message") && response.request().method() === "POST";
  });

  await page.locator("#assistant-input").fill(message);
  await page.locator("#assistant-form button[type='submit']").click();
  await responsePromise;
  await expect(page.locator("#assistant-form button[type='submit']")).toHaveText("Send");
}

async function waitForCompanionAccessCard(page) {
  const card = page.locator("#companion-access-panel article").filter({ hasText: "Best link for phone" }).first();
  await expect(card).toBeVisible();
  return card;
}

function pendingCard(page, text) {
  return page.locator("#pending-list article").filter({ hasText: text }).first();
}

function reminderCard(page, text) {
  return page.locator("#reminders-list article").filter({ hasText: text }).first();
}

module.exports = {
  openControlRoom,
  pendingCard,
  reminderCard,
  sendAssistantMessage,
  uniqueSuffix,
  waitForCompanionAccessCard,
  waitForMobileReady,
};
