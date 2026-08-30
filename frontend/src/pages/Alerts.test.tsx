import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Alerts from "./Alerts";
import { listAlerts } from "../api/client";

vi.mock("../api/client", () => ({
  listAlerts: vi.fn(),
}));

const mockedList = vi.mocked(listAlerts);

describe("Alerts", () => {
  beforeEach(() => mockedList.mockReset());

  it("shows alert reason and signals", async () => {
    mockedList.mockResolvedValue({
      alerts: [
        {
          transaction_id: "transaction-1",
          txn_date: "2026-02-02",
          description_raw: "BIG APPLIANCE WAREHOUSE",
          amount: -1240,
          category: "shopping",
          reason: "large statistical outlier",
          signals: ["robust_z", "iqr", "new_large_merchant"],
        },
      ],
    });
    render(<Alerts />);

    expect(await screen.findByText("BIG APPLIANCE WAREHOUSE")).toBeInTheDocument();
    expect(screen.getByText("large statistical outlier")).toBeInTheDocument();
    expect(screen.getByText("Statistical outlier")).toBeInTheDocument();
    expect(screen.getByText("Outside normal range")).toBeInTheDocument();
    expect(screen.getByText("New large merchant")).toBeInTheDocument();
    expect(screen.getByText("Feb 2, 2026")).toBeInTheDocument();
  });
});
