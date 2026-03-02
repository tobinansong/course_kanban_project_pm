import { expect, test, type Page } from "@playwright/test";

const login = async (page: Page) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

// Created in beforeAll and shared with the drag test.
let reviewCardId: string;

test.beforeAll(async ({ request }) => {
  // Reset card-1 to col-backlog so the drag test starts from a known position.
  await request.post("/api/cards/card-1/move", {
    data: { toColumnId: "col-backlog", position: 0 },
  });
  // Create a fresh card in col-review as the drag-drop target.
  // Relying on seed cards (card-6 etc.) is fragile because previous test runs
  // may have moved or the database may not contain them.
  const response = await request.post("/api/cards", {
    data: { columnId: "col-review", title: "Review target", details: "" },
  });
  const card = (await response.json()) as { id: string };
  reviewCardId = card.id;
});

test("loads the kanban board", async ({ page }) => {
  await login(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await login(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  // Use .first() to avoid strict-mode failures when previous runs left duplicate cards.
  await expect(firstColumn.getByText("Playwright card").first()).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await login(page);

  // card-1 is in col-backlog (ensured by beforeAll).
  // reviewCardId is a fresh card in col-review (created in beforeAll).
  // Dragging card-1 ONTO the review card gives closestCorners a clear target
  // inside col-review — avoiding the empty-column corner-distance problem.
  const card = page.getByTestId("card-card-1");
  const targetCard = page.getByTestId(`card-${reviewCardId}`);
  const targetColumn = page.getByTestId("column-col-review");

  const cardBox = await card.boundingBox();
  const targetCardBox = await targetCard.boundingBox();
  if (!cardBox || !targetCardBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  const startX = cardBox.x + cardBox.width / 2;
  const startY = cardBox.y + cardBox.height / 2;
  await page.mouse.move(startX, startY);
  await page.mouse.down();
  // Small nudge to exceed dnd-kit PointerSensor's 6 px activation distance.
  await page.mouse.move(startX + 10, startY, { steps: 5 });
  // Move to the review card; closestCorners will choose it as the droppable.
  await page.mouse.move(
    targetCardBox.x + targetCardBox.width / 2,
    targetCardBox.y + targetCardBox.height / 2,
    { steps: 30 }
  );
  await page.mouse.up();

  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("logs out and returns to login", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
});
