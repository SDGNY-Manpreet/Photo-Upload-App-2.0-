import { useEffect, useState } from "react";
import { fetchSpecialProjects, uploadToSpecial } from "../api/client";
import FileDropzone from "../components/FileDropzone";
import UploadProgress from "../components/UploadProgress";
import SearchableSelect from "../components/SearchableSelect";
import Steps from "../components/Steps";
import { UploadCloudIcon } from "../components/Icons";

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

export default function SpecialProjects() {
  const [projects, setProjects]     = useState([]);
  const [loading, setLoading]       = useState(true);
  const [fetchError, setFetchError] = useState(null);

  const [projectId, setProjectId]         = useState("");
  const [projectDetails, setProjectDetails] = useState(null);
  const [jobNumber, setJobNumber]         = useState("");
  const [status, setStatus]               = useState("");
  const [personName, setPersonName]       = useState("");
  const [files, setFiles]                 = useState([]);

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress]   = useState(0);
  const [step, setStep]           = useState("");
  const [result, setResult]       = useState(null);

  useEffect(() => {
    fetchSpecialProjects()
      .then((d) => setProjects(d || []))
      .catch(() => setFetchError("Could not load special projects from database."))
      .finally(() => setLoading(false));
  }, []);

  const handleProjectChange = (val) => {
    setProjectId(val);
    setProjectDetails(projects.find((p) => p.project_number === val) || null);
    setJobNumber(""); setStatus(""); setPersonName(""); setFiles([]); setResult(null);
  };

  const resetForm = () => {
    setProjectId(""); setProjectDetails(null); setJobNumber("");
    setStatus(""); setPersonName(""); setFiles([]);
    setProgress(0); setStep(""); setResult(null);
  };

  const handleUpload = async () => {
    setUploading(true); setResult(null); setProgress(0); setStep("Uploading to SharePoint…");
    const fd = new FormData();
    fd.append("project_id", projectId);
    fd.append("job_number", jobNumber.trim());
    fd.append("status", status);
    fd.append("person_name", personName);
    files.forEach((f) => fd.append("files", f));
    
    try {
      const res = await uploadToSpecial(fd, (pct) => setProgress(Math.min(pct, 95)));
      setProgress(100); setStep("Done"); setResult(res);
      if (res.success_count === res.total) setTimeout(resetForm, 3000);
    } catch (err) {
      setResult({ success_count: 0, total: files.length,
        errors: [err.response?.data?.detail || err.message] });
    } finally {
      setUploading(false);
    }
  };

  const projectOptions = projects.map((p) => p.project_number);
  const jobValid   = jobNumber.trim().length > 0;
  const canUpload  = projectId && jobValid && status && personName && files.length > 0 && !uploading;

  let currentWizardStep = 1;
  if (projectId) currentWizardStep = 2;
  if (projectId && jobValid && status && personName) currentWizardStep = 3;
  if (canUpload) currentWizardStep = 4;
  if (uploading || result) currentWizardStep = 5;

  return (
    <div className="max-w-2xl mx-auto w-full animate-fade-in pb-12">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Special Projects</h1>
        <p className="text-sm text-slate-500 mt-1.5">
          Upload photos to SharePoint under Project Code / Year / Job Number / Status.
        </p>
      </div>

      <Steps 
        currentStep={currentWizardStep} 
        steps={["Project", "Details", "Images", "Upload"]} 
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

        {!loading && !fetchError && projects.length === 0 && (
          <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 text-amber-700 rounded-2xl p-4 text-sm font-medium">
            <svg className="w-5 h-5 shrink-0 mt-0.5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>No special projects found.</span>
          </div>
        )}

        {!loading && !fetchError && projects.length > 0 && (
          <>
            {/* Step 1 */}
            <div className={`transition-opacity duration-300 ${currentWizardStep < 1 ? 'opacity-40 pointer-events-none' : ''}`}>
              <FormLabel stepNumber="1">Select Project Code</FormLabel>
              <SearchableSelect
                options={projectOptions}
                value={projectId}
                onChange={handleProjectChange}
                disabled={uploading}
                placeholder="Search project code..."
              />
              
              {projectId && projectDetails && (
                <div className="mt-3 bg-brand-50 border border-brand-200 rounded-xl px-4 py-3 space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-brand-700 w-24 shrink-0 font-medium">Project Name</span>
                    <span className="text-brand-900 font-bold truncate">{projectDetails.project_name || "—"}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-brand-700 w-24 shrink-0 font-medium">Customer</span>
                    <span className="text-brand-900 font-bold truncate">{projectDetails.customer || "—"}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Step 2 */}
            {projectId && (
              <div className={`grid grid-cols-1 sm:grid-cols-2 gap-5 transition-all duration-500 animate-slide-up`}>
                <div className="sm:col-span-2">
                  <FormLabel stepNumber="2">Job Number</FormLabel>
                  <input
                    type="text"
                    value={jobNumber}
                    onChange={(e) => { setJobNumber(e.target.value); setStatus(""); setPersonName(""); setFiles([]); }}
                    disabled={uploading}
                    placeholder="Enter complete job number (e.g. 25-1234)"
                    className="w-full px-3 py-2 bg-white border border-slate-200 focus:border-slate-400 focus:ring-2 focus:ring-slate-200 rounded-lg outline-none text-slate-800 text-sm placeholder:text-slate-400 disabled:opacity-50 transition-all"
                  />
                </div>
                
                {jobValid && (
                  <>
                    <div className="animate-fade-in">
                      <FormLabel stepNumber="3">Status Stage</FormLabel>
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
                        <FormLabel stepNumber="4">Uploader Name</FormLabel>
                        <SearchableSelect 
                          options={PERSON_NAMES}
                          value={personName} 
                          onChange={(v) => { setPersonName(v); setFiles([]); }} 
                          disabled={uploading} 
                          placeholder="Select your name..."
                        />
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            {/* Step 3 */}
            {personName && (
              <div className="animate-slide-up pt-2">
                <FormLabel stepNumber="5">Add Images</FormLabel>
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
                        <UploadCloudIcon className="w-5 h-5 transition-transform group-hover:-translate-y-0.5" />
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
