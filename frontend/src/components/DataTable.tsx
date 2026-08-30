import { TAXONOMY, type Category, type Transaction } from "../api/client";
import { formatDate, humanizeCategory } from "../format";

interface Props {
  transactions: Transaction[];
  onCategoryChange: (id: string, category: Category) => Promise<void>;
}

function formatAmount(value: number): string {
  const amount = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return value < 0 ? `− $${amount}` : `$${amount}`;
}

export default function DataTable({ transactions, onCategoryChange }: Props) {
  return (
    <div className="ledger-table-wrap">
      <table className="ledger-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Merchant</th>
            <th className="numeric">Amount</th>
            <th>Category</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id}>
              <td className="date-cell">{formatDate(transaction.txn_date)}</td>
              <td>{transaction.merchant}</td>
              <td className={`numeric${transaction.amount < 0 ? " flag-amount" : ""}`}>{formatAmount(transaction.amount)}</td>
              <td>
                <select
                  aria-label={`Category for ${transaction.merchant}`}
                  className="field"
                  value={transaction.category}
                  onChange={(event) => {
                    void onCategoryChange(transaction.id, event.target.value as Category);
                  }}
                >
                  {TAXONOMY.map((category) => (
                    <option key={category} value={category}>
                      {humanizeCategory(category)}
                    </option>
                  ))}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
