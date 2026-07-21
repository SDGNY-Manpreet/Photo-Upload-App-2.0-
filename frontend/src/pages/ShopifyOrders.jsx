import { useEffect, useState } from "react";
import { fetchShopifyOrders, uploadToShopify } from "../api/client";
import FileDropzone from "../components/FileDropzone";
import UploadProgress from "../components/UploadProgress";
import SearchableSelect from "../components/SearchableSelect";
import Steps from "../components/Steps";

const STATUS_OPTIONS = ["PRODUCTION", "SHIPPED", "PICKUP", "INSTALLATION", "SITE SURVEY"];
const PERSON_NAMES = [
  "Muhammad","Mikhail","Sid","Alex","Kathy","Luis",
  "Genesis","Elias","Edgar","Ivan","Yolani","Rafa","Alma","Maritza","Jason",
];

function FormLabel({ children, stepNumber }) {
  return (
    <label className="flex items-center gap-2 text-sm font-semibold text-slate-800 mb-2">
      {stepNumber && (
        <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center text-[10px] border border-slate-200">
          {stepNumber}
        </span>
      )}
      {children}
    </label>
  );
}

export default function ShopifyOrders() {
  const [orders, setOrders]         = useState([]);
  const [loading, setLoading]       = useState(true);
  const [fetchError, setFetchError] = useState(null);

  const [orderId, setOrderId]           = useState("");
  const [customerName, setCustomerName] = useState("");
  const [status, setStatus]             = useState("");
  const [personName, setPersonName]     = useState("");
  const [files, setFiles]               = useState([]);

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress]   = useState(0);
  const [step, setStep]           = useState("");
  const [result, setResult]       = useState(null);

  useEffect(() => {
    fetchShopifyOrders()
      .then((d) => setOrders(d || []))
      .catch(() => setFetchError("Could not load Shopify orders from database."))
      .finally(() => setLoading(false));
  }, []);

  const handleOrderChange = (val) => {
    setOrderId(val);
    const found = orders.find((o) => o.order_id === val);
    setCustomerName(found?.customer_name || "");
    setStatus(""); setPersonName(""); setFiles([]); setResult(null);
  };

  const resetForm = () => {
    setOrderId(""); setCustomerName(""); setStatus(""); setPersonName(""); setFiles([]);
    setProgress(0); setStep(""); setResult(null);
  };

  const handleUpload = async () => {
    setUploading(true); setResult(null); setProgress(0); setStep("Uploading to SharePoint…");
    const fd = new FormData();
    fd.append("order_id", orderId);
    fd.append("customer_name", customerName);
    fd.append("status", status);
    fd.append("person_name", personName);
    files.forEach((f) => fd.append("files", f));
    
    try {
      const res = await uploadToShopify(fd, (pct) => setProgress(Math.min(pct, 95)));
      setProgress(100); setStep("Done"); setResult(res);
      if (res.success_count === res.total) setTimeout(resetForm, 3000);
    } catch (err) {
      setResult({ success_count: 0, total: files.length,
        errors: [err.response?.data?.detail || err.message] });
    } finally {
      setUploading(false);
    }
  };

  const orderOptions = orders.map((o) => o.order_id);
  const canUpload = orderId && status && personName && files.length > 0 && !uploading;

  let currentWizardStep = 1;
  if (orderId) currentWizardStep = 2;
  if (orderId && status && personName) currentWizardStep = 3;
  if (canUpload) currentWizardStep = 4;
  if (uploading || result) currentWizardStep = 5;

  return (
    <div className="max-w-2xl mx-auto w-full animate-fade-in pb-12">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Shopify Orders</h1>
        <p className="text-sm text-slate-500 mt-1.5">
          Upload order photos to SharePoint under Customer / Order / Status.
        </p>
      </div>

      <Steps 
        currentStep={currentWizardStep} 
        steps={["Order", "Details", "Images", "Upload"]} 
      />

      <div className="bg-white border border-slate-200 rounded-3xl shadow-sm p-6 sm:p-8 space-y-8 relative">
        {loading && (
          <div className="space-y-6">
            <div className="h-14 bg-slate-100 rounded-xl animate-pulse" />
            <div className="h-14 bg-slate-100 rounded-xl animate-pulse" />
            <div className="h-40 bg-slate-100 rounded-2xl animate-pulse" />
          </div>
        )}

        {fetchError && (
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 rounded-2xl p-4 text-sm font-medium">
            <svg className="w-5 h-5 shrink-0 mt-0.5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{fetchError}</span>
          </div>
        )}

        {!loading && !fetchError && orders.length === 0 && (
          <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 text-amber-700 rounded-2xl p-4 text-sm font-medium">
            <svg className="w-5 h-5 shrink-0 mt-0.5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>No Shopify orders found in the database.</span>
          </div>
        )}

        {!loading && !fetchError && orders.length > 0 && (
          <>
            {/* Step 1 */}
            <div className={`transition-opacity duration-300 ${currentWizardStep < 1 ? 'opacity-40 pointer-events-none' : ''}`}>
              <FormLabel stepNumber="1">Select Order ID</FormLabel>
              <SearchableSelect
                options={orderOptions}
                value={orderId}
                onChange={handleOrderChange}
                disabled={uploading}
                placeholder="Search order number..."
              />
              
              {orderId && customerName && (
                <div className="mt-3 flex items-center gap-2 text-xs text-brand-800 bg-brand-50 border border-brand-200 rounded-lg px-3 py-2">
                  <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Customer: <strong className="font-bold">{customerName}</strong>
                </div>
              )}
            </div>

            {/* Step 2 */}
            {orderId && (
              <div className={`grid grid-cols-1 sm:grid-cols-2 gap-5 transition-all duration-500 animate-slide-up`}>
                <div>
                  <FormLabel stepNumber="2">Status Stage</FormLabel>
                  <SearchableSelect 
                    options={STATUS_OPTIONS}
                    value={status} 
                    onChange={(v) => { setStatus(v); setPersonName(""); setFiles([]); }} 
                    disabled={uploading} 
                    placeholder="Choose stage..."
                  />
                </div>
                {status && (
                  <div className="animate-fade-in">
                    <FormLabel stepNumber="3">Uploader Name</FormLabel>
                    <SearchableSelect 
                      options={PERSON_NAMES}
                      value={personName} 
                      onChange={(v) => { setPersonName(v); setFiles([]); }} 
                      disabled={uploading} 
                      placeholder="Select your name..."
                    />
                  </div>
                )}
              </div>
            )}

            {/* Step 3 */}
            {personName && (
              <div className="animate-slide-up pt-2">
                <FormLabel stepNumber="4">Add Images</FormLabel>
                <FileDropzone files={files} onChange={setFiles} disabled={uploading} />
              </div>
            )}

            {/* Step 4 */}
            {(uploading || result) && (
              <div className="pt-2 animate-fade-in">
                <UploadProgress percent={progress} step={step} result={result} />
              </div>
            )}

            {/* Submit */}
            {files.length > 0 && !result && (
              <div className="pt-4 animate-slide-up">
                <button
                  onClick={handleUpload}
                  disabled={!canUpload}
                  className="group relative w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white disabled:text-slate-400 font-semibold rounded-xl text-sm transition-all shadow-md hover:shadow-lg disabled:shadow-none overflow-hidden"
                >
                  {uploading ? (
                    <>
                      <svg className="w-5 h-5 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                      </svg>
                      Uploading securely...
                    </>
                  ) : (
                    <>
                      <span className="relative z-10 flex items-center gap-2">
                        <svg className="w-5 h-5 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        Upload to SharePoint
                      </span>
                      <div className="absolute inset-0 bg-gradient-to-r from-slate-800 to-slate-900 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
