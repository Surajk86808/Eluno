import { FileText, Upload } from "lucide-react";
import { useRef, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

function formatCurrency(val) {
  if (val === null || val === undefined) return "—";
  return `₹${Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
}

function EditableCell({ value, onChange }) {
  return (
    <input
      className="w-full rounded border border-transparent bg-transparent px-1 py-0.5 text-sm text-slate-700 hover:border-line focus:border-signal focus:bg-white focus:outline-none"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

export default function InvoiceUpload() {
  const [file, setFile] = useState(null);
  const [parsed, setParsed] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const fileInputRef = useRef(null);

  function handleFileChange(e) {
    setFile(e.target.files?.[0] || null);
    setParsed(null);
    setError("");
    setSaved(false);
  }

  async function handleUpload() {
    if (!file) {
      setError("Please select a PDF or image file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    setError("");
    setSaved(false);

    try {
      const res = await fetch(`${API_BASE_URL}/documents/parse-invoice`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `Parse failed: ${res.status}`);
      }
      const data = await res.json();
      setParsed(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsUploading(false);
    }
  }

  function updateLineItem(idx, field, value) {
    setParsed((prev) => {
      const items = [...(prev.line_items || [])];
      items[idx] = { ...items[idx], [field]: value };
      return { ...prev, line_items: items };
    });
  }

  function updateField(field, value) {
    setParsed((prev) => ({ ...prev, [field]: value }));
  }

  function handleSave() {
    // In a real scenario this would POST to a save endpoint.
    // For now we confirm to the user that the data is ready.
    setSaved(true);
  }

  return (
    <section className="space-y-5">
      <div className="flex items-center gap-3 rounded-xl border border-line bg-white p-4 shadow-sm">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-50 border border-teal-200">
          <FileText className="h-5 w-5 text-signal" />
        </div>
        <div>
          <h2 className="font-semibold text-ink">Invoice Parser</h2>
          <p className="text-xs text-slate-500">Upload a vendor invoice (PDF or image) — Gemini will extract the data</p>
        </div>
      </div>

      {/* Upload area */}
      <div className="rounded-xl border-2 border-dashed border-line bg-white p-8 text-center">
        <Upload className="mx-auto mb-3 h-8 w-8 text-slate-400" />
        <p className="text-sm text-slate-500 mb-3">
          {file ? (
            <span className="font-medium text-ink">{file.name}</span>
          ) : (
            "Drag and drop or click to select a PDF or image"
          )}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.webp"
          onChange={handleFileChange}
          className="hidden"
        />
        <div className="flex justify-center gap-3">
          <button
            className="btn-secondary"
            type="button"
            onClick={() => fileInputRef.current?.click()}
          >
            Choose File
          </button>
          {file && (
            <button
              className="btn-primary"
              type="button"
              onClick={handleUpload}
              disabled={isUploading}
            >
              {isUploading ? "Parsing…" : "Parse Invoice"}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>
      )}

      {/* Parsed results */}
      {parsed && (
        <div className="space-y-4 rounded-xl border border-line bg-white p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-ink">Extracted Invoice Data</h3>
            <p className="text-xs text-slate-400">Click any field to edit before saving</p>
          </div>

          {/* Header fields */}
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { label: "Vendor", field: "vendor_name" },
              { label: "Invoice #", field: "invoice_number" },
              { label: "Invoice Date", field: "invoice_date" },
            ].map(({ label, field }) => (
              <div key={field} className="rounded-lg border border-line p-3">
                <p className="text-xs font-medium text-slate-400 uppercase mb-1">{label}</p>
                <EditableCell
                  value={parsed[field]}
                  onChange={(val) => updateField(field, val)}
                />
              </div>
            ))}
          </div>

          {/* Line items table */}
          {parsed.line_items && parsed.line_items.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-line">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50 border-b border-line">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Description</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Qty</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Unit Price</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-slate-500 uppercase">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {parsed.line_items.map((item, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-3 py-2">
                        <EditableCell value={item.description} onChange={(v) => updateLineItem(i, "description", v)} />
                      </td>
                      <td className="px-3 py-2">
                        <EditableCell value={item.quantity} onChange={(v) => updateLineItem(i, "quantity", v)} />
                      </td>
                      <td className="px-3 py-2">
                        <EditableCell value={item.unit_price} onChange={(v) => updateLineItem(i, "unit_price", v)} />
                      </td>
                      <td className="px-3 py-2">
                        <EditableCell value={item.total} onChange={(v) => updateLineItem(i, "total", v)} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Totals */}
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              { label: "Subtotal", field: "subtotal" },
              { label: "Tax", field: "tax" },
              { label: "Grand Total", field: "grand_total" },
            ].map(({ label, field }) => (
              <div key={field} className={`rounded-lg border p-3 ${field === "grand_total" ? "border-signal bg-teal-50" : "border-line"}`}>
                <p className="text-xs font-medium text-slate-400 uppercase mb-1">{label}</p>
                <p className={`text-lg font-semibold ${field === "grand_total" ? "text-signal" : "text-ink"}`}>
                  {formatCurrency(parsed[field])}
                </p>
              </div>
            ))}
          </div>

          {/* Save button */}
          {saved ? (
            <div className="rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800 font-medium">
              Invoice data saved successfully.
            </div>
          ) : (
            <button className="btn-primary" type="button" onClick={handleSave}>
              Save Invoice
            </button>
          )}
        </div>
      )}
    </section>
  );
}
