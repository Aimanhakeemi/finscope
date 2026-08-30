import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ImportPage from "./Import";
import { uploadImport } from "../api/client";

vi.mock("../api/client", () => ({
  uploadImport: vi.fn(),
}));

const mockedUpload = vi.mocked(uploadImport);

describe("ImportPage", () => {
  beforeEach(() => mockedUpload.mockReset());

  it("renders, submits a file, and shows the import summary", async () => {
    mockedUpload.mockResolvedValue({
      import_id: "import-1",
      filename: "statement.csv",
      rows_received: 2,
      rows_accepted: 2,
      rows_deduped: 0,
      date_range: ["2026-01-01", "2026-01-02"],
      category_breakdown: {
        groceries: 0,
        dining: 0,
        coffee: 1,
        transport: 0,
        fuel: 0,
        utilities: 0,
        rent_mortgage: 0,
        subscriptions: 0,
        shopping: 0,
        health: 0,
        entertainment: 0,
        income: 1,
        other: 0,
      },
      llm_fallback_count: 0,
    });
    render(<ImportPage />);
    const file = new File(["date,description,amount\n2026-01-01,COFFEE,-5"], "statement.csv", {
      type: "text/csv",
    });
    fireEvent.change(screen.getByLabelText("Statement CSV"), { target: { files: [file] } });
    fireEvent.submit(screen.getByRole("button", { name: "Import CSV" }).closest("form")!);

    expect(await screen.findByText("statement.csv imported")).toBeInTheDocument();
    expect(screen.getByText(/Rows accepted: 2/)).toBeInTheDocument();
    expect(mockedUpload).toHaveBeenCalledWith(file, {});
  });
});
