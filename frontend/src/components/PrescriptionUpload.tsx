import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

type ParsedPrescription = {
  sph_od?: string | number | null;
  sph_os?: string | number | null;
  add_power?: string | number | null;
  suggested_lens_type?: string | null;
  coating_suggestion?: string | null;
  notes?: string | null;
};

type PrescriptionUploadProps = {
  onOrderCreated: () => void;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
const STORE_OPTIONS = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"];
const LENS_TYPE_OPTIONS = ["Single Vision", "Progressive", "Bifocal"];

type OrderForm = {
  customer_name: string;
  frame_name: string;
  store_location: string;
  lens_type: string;
  power: string;
  coating: string;
};

function displayValue(value: ParsedPrescription[keyof ParsedPrescription]) {
  return value === null || value === undefined || value === "" ? "-" : value;
}

function createOrderForm(prescription: ParsedPrescription): OrderForm {
  return {
    customer_name: "",
    frame_name: "",
    store_location: STORE_OPTIONS[0],
    lens_type: prescription.suggested_lens_type || LENS_TYPE_OPTIONS[0],
    power: prescription.sph_od === null || prescription.sph_od === undefined ? "" : String(prescription.sph_od),
    coating: prescription.coating_suggestion || "",
  };
}

export default function PrescriptionUpload({ onOrderCreated }: PrescriptionUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<ParsedPrescription | null>(null);
  const [orderForm, setOrderForm] = useState<OrderForm | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isCreatingOrder, setIsCreatingOrder] = useState(false);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] || null);
    setParsedData(null);
    setOrderForm(null);
    setError("");
    setSuccess("");
  }

  function updateOrderForm(field: keyof OrderForm, value: string) {
    setOrderForm((current) => (current ? { ...current, [field]: value } : current));
  }

  async function handleUpload() {
    if (!file) {
      setError("Choose a PDF or image first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(`${API_BASE_URL}/prescription/parse`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || `Request failed: ${response.status}`);
      }

      setParsedData(await response.json());
      setOrderForm(null);
    } catch (err) {
      setParsedData(null);
      setOrderForm(null);
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleCreateOrderSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!orderForm) return;

    setIsCreatingOrder(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(`${API_BASE_URL}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_name: orderForm.customer_name,
          frame_name: orderForm.frame_name,
          store_location: orderForm.store_location,
          lens_type: orderForm.lens_type,
          power: Number(orderForm.power),
          coating: orderForm.coating,
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail || `Request failed: ${response.status}`);
      }

      setSuccess("Order created successfully");
      window.setTimeout(() => onOrderCreated(), 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Order creation failed.");
    } finally {
      setIsCreatingOrder(false);
    }
  }

  return (
    <section className="space-y-3">
      <input
        className="field"
        type="file"
        accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
        onChange={handleFileChange}
      />
      <button className="btn-primary" type="button" onClick={handleUpload} disabled={isUploading}>
        {isUploading ? "Parsing..." : "Upload & Parse"}
      </button>

      {error && <div className="border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}
      {success && <div className="border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">{success}</div>}

      {parsedData && (
        <div className="space-y-3 border border-slate-300 bg-slate-50 p-4 text-sm">
          <dl className="grid gap-2 sm:grid-cols-2">
            <div>
              <dt className="font-medium text-slate-500">SPH OD</dt>
              <dd className="text-ink">{displayValue(parsedData.sph_od)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">SPH OS</dt>
              <dd className="text-ink">{displayValue(parsedData.sph_os)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Add Power</dt>
              <dd className="text-ink">{displayValue(parsedData.add_power)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Suggested Lens Type</dt>
              <dd className="text-ink">{displayValue(parsedData.suggested_lens_type)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Coating</dt>
              <dd className="text-ink">{displayValue(parsedData.coating_suggestion)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Notes</dt>
              <dd className="text-ink">{displayValue(parsedData.notes)}</dd>
            </div>
          </dl>

          <button className="btn-secondary" type="button" onClick={() => setOrderForm(createOrderForm(parsedData))}>
            Create Order with this Prescription
          </button>

          {orderForm && (
            <form className="grid gap-3 border-t border-slate-200 pt-3 sm:grid-cols-2" onSubmit={handleCreateOrderSubmit}>
              <label className="space-y-1 text-xs font-medium text-slate-500">
                Customer Name
                <input
                  className="field"
                  value={orderForm.customer_name}
                  onChange={(event) => updateOrderForm("customer_name", event.target.value)}
                  required
                />
              </label>
              <label className="space-y-1 text-xs font-medium text-slate-500">
                Frame
                <input
                  className="field"
                  value={orderForm.frame_name}
                  onChange={(event) => updateOrderForm("frame_name", event.target.value)}
                  required
                />
              </label>
              <label className="space-y-1 text-xs font-medium text-slate-500">
                Store
                <select
                  className="field"
                  value={orderForm.store_location}
                  onChange={(event) => updateOrderForm("store_location", event.target.value)}
                  required
                >
                  {STORE_OPTIONS.map((store) => (
                    <option key={store}>{store}</option>
                  ))}
                </select>
              </label>
              <label className="space-y-1 text-xs font-medium text-slate-500">
                lens_type
                <select
                  className="field"
                  value={orderForm.lens_type}
                  onChange={(event) => updateOrderForm("lens_type", event.target.value)}
                  required
                >
                  {[...new Set([orderForm.lens_type, ...LENS_TYPE_OPTIONS])].map((lensType) => (
                    <option key={lensType}>{lensType}</option>
                  ))}
                </select>
              </label>
              <label className="space-y-1 text-xs font-medium text-slate-500">
                power
                <input
                  className="field"
                  type="number"
                  step="0.25"
                  value={orderForm.power}
                  onChange={(event) => updateOrderForm("power", event.target.value)}
                  required
                />
              </label>
              <label className="space-y-1 text-xs font-medium text-slate-500">
                coating
                <input
                  className="field"
                  value={orderForm.coating}
                  onChange={(event) => updateOrderForm("coating", event.target.value)}
                />
              </label>
              <button className="btn-primary sm:col-span-2" type="submit" disabled={isCreatingOrder}>
                {isCreatingOrder ? "Creating..." : "Submit Order"}
              </button>
            </form>
          )}
        </div>
      )}
    </section>
  );
}
