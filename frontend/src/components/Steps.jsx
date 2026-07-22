import { CheckCircleIcon } from "./Icons";

export default function Steps({ currentStep, steps = [] }) {
  return (
    <div className="flex items-center justify-between w-full relative mb-8">
      {/* Background connecting line */}
      <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-200 -translate-y-1/2 z-0" />
      
      {steps.map((step, index) => {
        const isCompleted = currentStep > index + 1;
        const isActive = currentStep === index + 1;
        const isUpcoming = currentStep < index + 1;

        return (
          <div key={step} className="relative z-10 flex flex-col items-center group">
            <div
              className={`
                w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 shadow-sm
                ${isCompleted ? 'bg-brand-500 text-slate-900 border-2 border-brand-500' : ''}
                ${isActive ? 'bg-slate-900 text-white border-2 border-slate-900 ring-4 ring-slate-100' : ''}
                ${isUpcoming ? 'bg-white text-slate-400 border-2 border-slate-200' : ''}
              `}
            >
              {isCompleted ? (
                <svg className="w-4 h-4 text-slate-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span
              className={`
                absolute top-10 text-[10px] font-semibold uppercase tracking-wider whitespace-nowrap transition-colors
                ${isActive ? 'text-slate-900 font-bold' : isCompleted ? 'text-slate-700' : 'text-slate-400'}
              `}
            >
              {step}
            </span>
          </div>
        );
      })}
    </div>
  );
}
