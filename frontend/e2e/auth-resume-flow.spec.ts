import { test, expect } from "@playwright/test";
import path from "path";
import fs from "fs";

test.describe("NaziranGPT E2E Pipeline", () => {
  const testEmail = `candidate_${Date.now()}@example.com`;
  const testPassword = "SecretPassword123!";
  const testName = "Jane E2E Candidate";

  test("Should execute Register -> Dashboard -> Upload Resume -> ATS Score -> Profile -> Logout everywhere", async ({ page }) => {
    // 1. Visit Register Page
    await page.goto("/register");
    await expect(page.locator("h1")).toContainText("NaziranGPT");

    // 2. Perform Account Registration
    await page.fill('input[placeholder="John Doe"]', testName);
    await page.fill('input[placeholder="name@company.com"]', testEmail);
    await page.fill('input[placeholder="••••••••"]', testPassword);
    
    // Choose standard candidate role and click submit
    await page.click('button:has-text("Standard Candidate")');
    await page.click('button:has-text("Create Account")');

    // 3. Confirm transition to Dashboard
    await page.waitForURL("/");
    await expect(page.locator("span:has-text('NaziranGPT')")).toBeVisible();
    await expect(page.locator("span:has-text('Jane E2E Candidate')")).toBeVisible();

    // 4. Fill target job description
    await page.fill('textarea[placeholder*="Paste the target job description"]', "Seeking a Python Software Engineer with skill in FastAPI, Docker, and PostgreSQL database queries.");

    // Create a dummy text file to act as the uploaded resume (pdfplumber/docx parses string files correctly)
    const dummyResumePath = path.join(__dirname, "dummy_resume.pdf");
    fs.writeFileSync(dummyResumePath, "Jane E2E Candidate\nEmail: jane@example.com\nPhone: 123-456-7890\nSkills: Python, FastAPI, Docker, SQL\nEducation:\nBachelor of Science in Computer Science\nExperience:\nSoftware Engineer at Startup Corp");

    // 5. Upload File
    const fileChooserPromise = page.waitForEvent("filechooser");
    await page.click('label:has-text("browse")');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(dummyResumePath);

    // 6. Wait for file to upload, parse and display score
    await page.waitForSelector("div:has-text('ATS:')", { timeout: 15000 });
    await expect(page.locator("h2:has-text('Score Insights')")).toBeVisible();
    await expect(page.locator("h3:has-text('Actionable Recommendations')")).toBeVisible();

    // 7. Navigate to Profile settings
    await page.click("a:has-text('Jane E2E Candidate')");
    await page.waitForURL("/profile");
    await expect(page.locator("h2")).toContainText("Jane E2E Candidate");

    // 8. Trigger Logout Everywhere
    await page.click('button:has-text("Sign Out of All Devices")');
    
    // Accept standard browser confirm popup automatically
    page.on("dialog", dialog => dialog.accept());

    // 9. Verify redirect back to Login screen
    await page.waitForURL("/login?session_expired=true");
    await expect(page.locator("h2")).toContainText("Welcome Back");

    // Clean up local temp dummy file
    try {
      fs.unlinkSync(dummyResumePath);
    } catch (e) {
      // ignore
    }
  });
});
