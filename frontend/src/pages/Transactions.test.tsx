import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Transactions from "./Transactions";

function transaction(id: string, merchant: string) {
  return {
    id,
    txn_date: "2026-08-01",
    description_raw: merchant,
    merchant,
    amount: -42,
    category: "shopping" as const,
    category_confidence: 0.95,
    category_source: "model" as const,
    is_recurring: false,
    recurring_group_id: null,
    is_anomaly: false,
    anomaly_reason: null,
  };
}

afterEach(() => vi.unstubAllGlobals());

describe("Transactions", () => {
  it("renders filters and paginates with 50-row requests", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        total: 51,
        limit: 50,
        offset: 0,
        transactions: [transaction("transaction-1", "FIRST MERCHANT")],
      })))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        total: 51,
        limit: 50,
        offset: 50,
        transactions: [transaction("transaction-51", "SECOND MERCHANT")],
      })));
    vi.stubGlobal("fetch", fetchMock);

    render(<Transactions />);

    expect(await screen.findByText("FIRST MERCHANT")).toBeInTheDocument();
    expect(screen.getByLabelText("Category")).toBeInTheDocument();
    expect(screen.getByLabelText("Recurring")).toBeInTheDocument();
    expect(screen.getByLabelText("Anomaly")).toBeInTheDocument();
    expect(screen.getByLabelText("From date")).toBeInTheDocument();
    expect(screen.getByLabelText("To date")).toBeInTheDocument();
    expect(screen.getAllByRole("option", { name: "Rent / mortgage" })[0]).toHaveValue("rent_mortgage");
    expect(screen.getByText("Aug 1, 2026")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/transactions?limit=50&offset=0&sort=-date");

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("SECOND MERCHANT")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith("http://localhost:8000/api/transactions?limit=50&offset=50&sort=-date");
  });
});
