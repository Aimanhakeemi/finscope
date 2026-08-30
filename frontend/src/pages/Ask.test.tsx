import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Ask from "./Ask";
import { askQuestion } from "../api/client";

vi.mock("../api/client", () => ({
  askQuestion: vi.fn(),
}));

const mockedAsk = vi.mocked(askQuestion);

describe("Ask", () => {
  beforeEach(() => mockedAsk.mockReset());

  it("shows the answer table and generated SQL", async () => {
    mockedAsk.mockResolvedValue({
      question: "How much did I spend?",
      sql: "SELECT -SUM(amount) AS spent FROM v_readonly_transactions LIMIT 500",
      columns: ["spent"],
      rows: [{ spent: 42 }],
      truncated: false,
    });
    render(<Ask />);
    fireEvent.change(screen.getByLabelText("Spending question"), {
      target: { value: "How much did I spend?" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Ask" }).closest("form")!);

    expect(await screen.findByText("42")).toBeInTheDocument();
    expect(screen.getByLabelText("Generated SQL")).toHaveTextContent("LIMIT 500");
  });
});
