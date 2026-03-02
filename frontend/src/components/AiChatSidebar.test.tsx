import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AiChatSidebar } from "@/components/AiChatSidebar";

const noop = async () => {};

describe("AiChatSidebar", () => {
  it("shows empty placeholder when there are no messages", () => {
    render(<AiChatSidebar messages={[]} isLoading={false} error="" onSend={noop} />);
    expect(screen.getByText(/start with something like/i)).toBeInTheDocument();
  });

  it("shows Ready status when not loading", () => {
    render(<AiChatSidebar messages={[]} isLoading={false} error="" onSend={noop} />);
    expect(screen.getByText("Ready")).toBeInTheDocument();
  });

  it("shows Thinking status while loading", () => {
    render(<AiChatSidebar messages={[]} isLoading={true} error="" onSend={noop} />);
    expect(screen.getByText("Thinking")).toBeInTheDocument();
  });

  it("renders user and assistant messages", () => {
    const messages = [
      { role: "user" as const, content: "Move card to done" },
      { role: "assistant" as const, content: "Done! Moved the card." },
    ];
    render(<AiChatSidebar messages={messages} isLoading={false} error="" onSend={noop} />);
    expect(screen.getByText("Move card to done")).toBeInTheDocument();
    expect(screen.getByText("Done! Moved the card.")).toBeInTheDocument();
  });

  it("shows error message when error is set", () => {
    render(
      <AiChatSidebar messages={[]} isLoading={false} error="AI request failed" onSend={noop} />
    );
    expect(screen.getByText("AI request failed")).toBeInTheDocument();
  });

  it("calls onSend with trimmed message on submit", async () => {
    const onSend = vi.fn().mockResolvedValue(undefined);
    render(<AiChatSidebar messages={[]} isLoading={false} error="" onSend={onSend} />);
    await userEvent.type(screen.getByPlaceholderText(/ask the assistant/i), "  hello  ");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(onSend).toHaveBeenCalledWith("hello");
  });

  it("does not call onSend when message is blank", async () => {
    const onSend = vi.fn();
    render(<AiChatSidebar messages={[]} isLoading={false} error="" onSend={onSend} />);
    await userEvent.click(screen.getByRole("button", { name: /send/i }));
    expect(onSend).not.toHaveBeenCalled();
  });

  it("does not call onSend when loading", async () => {
    const onSend = vi.fn();
    render(<AiChatSidebar messages={[]} isLoading={true} error="" onSend={onSend} />);
    await userEvent.type(screen.getByPlaceholderText(/ask the assistant/i), "hello");
    // button is disabled when loading — userEvent skips disabled buttons
    await userEvent.click(screen.getByRole("button", { name: /sending/i }));
    expect(onSend).not.toHaveBeenCalled();
  });
});
