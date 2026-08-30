import { TAXONOMY, type Category, type Transaction } from "../api/client";

interface Props {
  transactions: Transaction[];
  onCategoryChange: (id: string, category: Category) => Promise<void>;
}

export default function DataTable({ transactions, onCategoryChange }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-slate-800 text-slate-400">
          <tr>
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3">Merchant</th>
            <th className="px-4 py-3">Amount</th>
            <th className="px-4 py-3">Category</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.id} className="border-b border-slate-800 last:border-0">
              <td className="px-4 py-3">{transaction.txn_date}</td>
              <td className="px-4 py-3">{transaction.merchant}</td>
              <td className="px-4 py-3">${transaction.amount.toFixed(2)}</td>
              <td className="px-4 py-3">
                <select
                  aria-label={`Category for ${transaction.merchant}`}
                  className="rounded border border-slate-700 bg-slate-950 px-2 py-1"
                  value={transaction.category}
                  onChange={(event) => {
                    void onCategoryChange(transaction.id, event.target.value as Category);
                  }}
                >
                  {TAXONOMY.map((category) => (
                    <option key={category} value={category}>
                      {category}
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
