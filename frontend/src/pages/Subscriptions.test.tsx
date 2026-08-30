import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Subscriptions from "./Subscriptions";
import { listSubscriptions } from "../api/client";

vi.mock("../api/client", () => ({
  listSubscriptions: vi.fn(),
}));

const mockedList = vi.mocked(listSubscriptions);

describe("Subscriptions", () => {
  beforeEach(() => mockedList.mockReset());

  it("shows recurring charges and monthly cost", async () => {
    mockedList.mockResolvedValue({
      total_monthly_cost: 20,
      total_annual_cost: 240,
      subscriptions: [
        {
          recurring_group_id: "group-1",
          merchant: "netflix.com",
          cadence: "monthly",
          avg_amount: -16.24,
          amount_stddev: 1.31,
          monthly_cost: 16.24,
          first_seen: "2026-01-01",
          last_seen: "2026-07-01",
          next_expected: "2026-07-31",
          occurrences: 7,
          active: true,
          price_changed: true,
        },
      ],
    });
    render(<Subscriptions />);

    expect(await screen.findByText("netflix.com")).toBeInTheDocument();
    expect(screen.getByText("$20.00")).toBeInTheDocument();
    expect(screen.getByText("Price changed by more than 5%.")).toBeInTheDocument();
    expect(screen.getByText("Jul 31, 2026")).toBeInTheDocument();
  });
});
