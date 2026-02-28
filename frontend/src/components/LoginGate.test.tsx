import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginGate } from "@/components/LoginGate";

const renderLoginGate = () =>
  render(
    <LoginGate>
      <div>Protected content</div>
    </LoginGate>
  );

describe("LoginGate", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders the login form by default", async () => {
    renderLoginGate();
    expect(
      await screen.findByRole("button", { name: /sign in/i })
    ).toBeInTheDocument();
  });

  it("logs in with valid credentials", async () => {
    renderLoginGate();
    const user = userEvent.setup();
    await screen.findByRole("button", { name: /sign in/i });
    await user.type(screen.getByLabelText(/username/i), "user");
    await user.type(screen.getByLabelText(/password/i), "password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(await screen.findByText("Protected content")).toBeInTheDocument();
  });

  it("shows an error on invalid credentials", async () => {
    renderLoginGate();
    const user = userEvent.setup();
    await screen.findByRole("button", { name: /sign in/i });
    await user.type(screen.getByLabelText(/username/i), "wrong");
    await user.type(screen.getByLabelText(/password/i), "bad");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    expect(
      screen.getByText(/invalid credentials/i)
    ).toBeInTheDocument();
  });

  it("restores login state from storage", async () => {
    window.localStorage.setItem("pm.authenticated", "true");
    renderLoginGate();
    expect(await screen.findByText("Protected content")).toBeInTheDocument();
  });

  it("logs out and returns to the login form", async () => {
    renderLoginGate();
    const user = userEvent.setup();
    await screen.findByRole("button", { name: /sign in/i });
    await user.type(screen.getByLabelText(/username/i), "user");
    await user.type(screen.getByLabelText(/password/i), "password");
    await user.click(screen.getByRole("button", { name: /sign in/i }));
    await user.click(screen.getByRole("button", { name: /log out/i }));
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });
});
